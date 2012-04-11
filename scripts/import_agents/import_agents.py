#!/usr/bin/python
# -*- coding: UTF-8 -*-

import csv
import json
import urllib2
import urllib

XIVO = '192.168.31.217'
USERNAME = None
PASSWORD = None
CSVFILE = 'agents_skills.csv'
CONTEXT = 'default'
URI_AGENT = '/callcenter/json.php/%s/settings/agents'
URI_SKILL = '/callcenter/json.php/%s/settings/queueskills'

class WebServicesResponse(object):
    def __init__(self, url, code, data):
        self.url = url
        self.code = code
        self.data = data


class WebServices(object):
    def __init__(self, uri_prefix, uri_suffix):
        self._wsr = None
        self._path = self._compute_path(uri_prefix, uri_suffix)
        self._uri_prefix = uri_prefix
        self._uri_suffix = uri_suffix
        self._opener = self._build_opener(USERNAME, PASSWORD)
        self._headers = {"Content-type": "application/json",
                         "Accept": "text/plain"}

    def _compute_path(self, uri_prefix, uri_suffix):
        if 'localhost' in uri_prefix or '127.0.0.1' in uri_prefix:
            method = 'private'
        else:
            method = 'restricted'
        return uri_suffix % method

    def _request_http(self, qry, data=None):
        if isinstance(data, dict):
            data = json.dumps(data)
        url = '%s%s?%s' % (self._uri_prefix, self._path, self._build_query(qry))
        request = urllib2.Request(url=url, data=data, headers=self._headers)
        handle = self._opener.open(request)
        try:
            self._wsr = WebServicesResponse(url, handle.code, handle.read())
        finally:
            handle.close()
        return self._wsr

    def _build_opener(self, username, password):
        handlers = []
        if username is not None or password is not None:
            pwd_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            pwd_manager.add_password(None, self._uri_prefix, username, password)
            handlers.append(urllib2.HTTPBasicAuthHandler(pwd_manager))
        return urllib2.build_opener(*handlers)

    def _build_query(self, qry):
        return urllib.urlencode(qry)

    def _get_path(self):
        return self._path

    def list(self):
        qry = {"act": "list"}
        return self._request_http(qry)

    def add(self, content):
        qry = {"act": "add"}
        return self._request_http(qry, content)
    
    def edit(self, content, id):
        qry = {"act": "edit", "id": id}
        return self._request_http(qry, content)

    def view(self, id):
        qry = {"act": "view", "id": id}
        return self._request_http(qry)

    def search(self, search):
        qry = {"act": "search", "search": search}
        return self._request_http(qry)

    def delete(self, id):
        qry = {"act": "delete", "id": id}
        return self._request_http(qry)

    def deleteall(self):
        qry = {"act": "deleteall"}
        return self._request_http(qry)


class AgentCache(object):
    """
    Cache agents already present on the XiVO
        init_cache :
            creates a dict with all the agents configured in the XiVO
            the agent number is the key of this dict
        exists :
            returns 1 if an agent is matching
    """

    def __init__(self, agent_ws):
        self.agent_ws = agent_ws

    def init_cache(self):
        response = self.agent_ws.list()
        if response.code == 200:
            agents = json.loads(response.data)
            self.agents = dict((agent['number'], agent) for agent in agents)
        else:
            self.agents = {}

    def exists(self, agent_number):
        if self.agents is not None:
            return agent_number in self.agents


# Functions creating the JSON content for Agent and Skill objects

def new_agent(firstname, lastname, number):
    return {
            "agentfeatures" : {
                "firstname": unicode(firstname),
                "lastname" : unicode(lastname),
                "number"   : unicode(number),
                "passwd"   : unicode(number),
                "context"  : "default",
                "numgroup" : "1",
                "autologoff": "0",
                "ackcall": "no",
                "wrapuptime": "0",
                "enddtmf" : "*",
                "acceptdtmf" : "#",
             },
            "agentoptions": {
                "musiconhold" : "default",
                "maxlogintries":"3",
            }
    }

def new_skilled_agent(firstname, lastname, number, skills, skill_ws):
    agent = new_agent(firstname, lastname, number)
    # Read skills of agents :
    #  - create them in xivo if it doesn't exist
    #  - update the agent json object accordingly
    for sk in skills:
        sk_id = add_skill_if_not_exists(sk['skill_cat'], sk['skill_name'], skill_ws)
        if 'queueskills' not in agent:
            agent.update({"queueskills":
                            [{
                                "weight" : unicode(sk['skill_weight']),
                                "id" : unicode(sk_id)
                            }]
                        })
        else:
            agent['queueskills'].append({
                                    "weight" : unicode(sk['skill_weight']),
                                    "id" : unicode(sk_id)
                                    })
    return agent

def new_skill(skill_cat, skill_name):
    return {
            "name": unicode(skill_name).lower().replace(' ',''),
            "description": unicode(skill_name),
            "printscreen": "",
            "category_name": unicode(skill_cat)
            }


# Functions which create Agents and Skills objects

"""
This function add the skill given in parameter
if it doesn't exist.
It then returns the 'id' of the skill created (or existing)
"""
def add_skill_if_not_exists(skill_cat, skill_name, skill_ws):
    response = skill_ws.list()
    if response.code == 200:
        skills = json.loads(response.data)
    else:
        skills = {}

    matching_skills = [skill for skill in skills if skill['name'] == skill_name]
    if len(matching_skills) == 0:
        skill = new_skill(skill_cat, skill_name)
        res = skill_ws.add(skill)

    response = skill_ws.list()
    #XXX : what if the skill list is still void ...
    if response.code == 200:
        skills = json.loads(response.data)
        matching_skills = [skill for skill in skills if skill['name'] == skill_name]
        return matching_skills[0]['id']


def create_agents(agent, agent_ws, gateway):
    context = CONTEXT

    if agent.has_key('skills'):
        agent_content =  new_skilled_agent(agent['firstname'], agent['lastname'], agent['number'], agent['skills'])
    else:
        agent_content = new_agent(agent['firstname'], agent['lastname'], agent['number'])
    response = agent_ws.add(agent_content)
    return response


def import_csv(agent_cache, agent_ws, skill_ws, xivo):
    """
    1. Open .CSV file
    .csv file has to have this header :
        col1,col2,col3,col4 ...
        where col1 are option names from Agent. Currently accepted values are listed in the AGENT_KEYS list below
        for skills, the col name must be : <category name>.<skill name> 
        (e.g. language.french)
    2. For each row :
        a. Test if this agent exists :
            i.  if the Agent exists, print a warning msg
            ii. if it doesn't, create it (if this agent has skills, create the skills accordingly)
    """
    AGENT_KEYS = ['agentfirstname','agentlastname','agentnumber']
    new_agent = {}

    with open(CSVFILE, 'rb') as fobj:
        csvreader = csv.DictReader(fobj, delimiter=';', quotechar='"')

        for ag in csvreader:
            new_agent = {}
            new_agent['firstname'] = ag['agentfirstname']
            new_agent['lastname'] = ag['agentlastname']
            new_agent['number'] = ag['agentnumber']
            for (key, val) in ag.items():
                if key not in AGENT_KEYS:
                    if val != '':
                        if 'skills' not in new_agent:
                            new_agent['skills'] = [{'skill_cat': key.split('.')[0], 'skill_name': key.split('.')[1], 'skill_weight': val}]
                        else:
                            new_agent['skills'].append({'skill_cat': key.split('.')[0], 'skill_name': key.split('.')[1], 'skill_weight': val})
             
            if agent_cache.exists(new_agent['number']):
                print "XiVO : agent %s already exists " % new_agent['number']
            else:
                print "XiVO : creating agent %s" % new_agent['number']
                context = CONTEXT
                if new_agent.has_key('skills'):
                    agent_content =  new_skilled_agent(new_agent['firstname'], new_agent['lastname'], new_agent['number'], new_agent['skills'], skill_ws)
                else:
                    agent_content = new_agent(new_agent['firstname'], new_agent['lastname'], new_agent['number'])
                response = agent_ws.add(agent_content)
                if response.code == 200:
                    print "XiVO : agent %s created" % new_agent['number']
                else:
                    print "XiVO : an error was encountered when creating agent %s : %s - %s" %(new_agent['number'], response.code, response.data)

def main():
    xivo = XIVO

    print "--------------creating agents-------------"
    print " xivo : %s " % xivo

    agent_ws = WebServices('https://%s' % XIVO, URI_AGENT)
    skill_ws = WebServices('https://%s' % XIVO, URI_SKILL)
    
    print " WS to be called :"
    print "   - Agent : %s" % agent_ws._get_path()
    print "   - Skill : %s" % skill_ws._get_path()

    agent_cache = AgentCache(agent_ws)
    agent_cache.init_cache()
    import_csv(agent_cache, agent_ws, skill_ws, xivo)


if __name__ == '__main__':
    main()
