'''
Created on 2012-03-14

@author: jylebleu
'''


import csv
import json
import urllib2
import urllib

XIVO1 = "192.168.32.70"
XIVO2 = "192.168.32.139"
GATEWAY1 = "xivo-gtw-1"
GATEWAY2 = "xivo-gtw-2"
CONTEXT = "test_incall"


INCALL_URI = "/service/ipbx/json.php/%s/call_management/incall"

class WebServicesResponse(object):
    def __init__(self, url, code, data):
        self.url = url
        self.code = code
        self.data = data

class WebServices(object):
    def __init__(self, module, uri_prefix):
        uri_prefix = uri_prefix

        self.module = module
        self._wsr = None
        self._path = self._compute_path(uri_prefix)
        self._uri_prefix = uri_prefix
        self._opener = self._build_opener(None, None)
        self._headers = {"Content-type": "application/json",
                         "Accept": "text/plain"}

    def _compute_path(self, uri_prefix):
        if 'localhost' in uri_prefix or '127.0.0.1' in uri_prefix:
            method = 'private'
        else:
            method = 'restricted'
        return INCALL_URI % method


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

    def list(self):
        qry = {"act": "list"}
        return self._request_http(qry)

    def add(self, content):
        qry = {"act": "add"}
        return self._request_http(qry, content)

class IncomingCallsCache():
    def __init__(self, incomingcall_ws):
        self.incomingcall_ws = incomingcall_ws


    def init_cache(self):
        response = self.incomingcall_ws.list()
        if response.code == 200:
            incoming_calls = json.loads(response.data)
            self.incalls = dict((incoming_call['exten'], incoming_call) for incoming_call in incoming_calls)
        else:
            self.incalls = {}

    def exists(self, extension):
        return extension in self.incalls

def createIncomingCalls(user_phone_nb , incoming_call_ws, gateway):
    exten = user_phone_nb
    context = CONTEXT


    incall_content = new_incall_content(exten, context, gateway)
    response = incoming_call_ws.add(incall_content)


def new_incall_content(exten, context, gateway):
    return {
        "incall": {
            "exten": unicode(exten),
            "context": unicode(context),
            "preprocess_subroutine": "",
        },
        "dialaction": {
            "answer": {
                 "actiontype": "custom",
                 "actionarg1": "Dial(SIP/%s/${XIVO_DSTNUM})" % gateway,
                 "actionarg2": ""
            }
        }
    }


def import_csv(incoming_call_cache1, incoming_call_cache2, incoming_call_ws1, incoming_call_ws2, gateway1, gateway2):
    userReader = csv.reader(open('users.csv', 'rb'), delimiter=';', quotechar='|')

    for row in userReader:
        extension = row[3]
        if incoming_call_cache1.exists(extension):
            print "Xivo1 : incoming call already exists for %s " % extension
        else:
            print "Xivo1 : creating incoming call for %s gateway %s" % (extension,gateway1)
            createIncomingCalls(extension, incoming_call_ws1 , gateway1)
        if incoming_call_cache2.exists(extension):
            print "Xivo2 : incoming call already exists for %s " % extension
        else:
            print "Xivo2 : creating incoming call for %s gateway %s" % (extension,gateway2)
            createIncomingCalls(extension, incoming_call_ws2 , gateway2)





def main():
    xivo1 = XIVO1
    xivo2 = XIVO2
    gateway1 = GATEWAY1
    gateway2 = GATEWAY2

    print "--------------creating incoming calls-------------"
    print " xivo 1 : %s " % xivo1
    print " xivo 2 : %s " % xivo2
    print " gateway 1 : %s " % gateway1
    print " gateway 2 : %s " % gateway2

    incoming_call_ws1 = WebServices('ipbx/call_management/incall', 'https://%s:443' % XIVO1)
    incoming_call_ws2 = WebServices('ipbx/call_management/incall', 'https://%s:443' % XIVO2)

    incoming_call_cache1 = IncomingCallsCache(incoming_call_ws1)
    incoming_call_cache1.init_cache()
    incoming_call_cache2 = IncomingCallsCache(incoming_call_ws2)
    incoming_call_cache2.init_cache()
    import_csv(incoming_call_cache1, incoming_call_cache2, incoming_call_ws1, incoming_call_ws2, gateway1, gateway2)

if __name__ == '__main__':
    main()
