from locust import HttpLocust, TaskSet, task
from requests.auth import HTTPBasicAuth


class ConfdTasks(TaskSet):

    def on_start(self):
        self.token = self.client.post('/api/auth/0.1/token',
                                      auth=HTTPBasicAuth('locust', '1Wraibyorc)'),
                                      json={'backend': 'xivo_admin', 'expiration': 60},
                                      verify=False).json()['data']['token']

    @task
    def users(self):
        self.client.get('/api/confd/1.1/groups', headers={'X-Auth-Token': self.token})

    @task
    def groups(self):
        self.client.get('/api/confd/1.1/groups', headers={'X-Auth-Token': self.token})


class ConfdUser(HttpLocust):
    task_set = ConfdTasks
    min_wait = 5000
    max_wait = 15000
