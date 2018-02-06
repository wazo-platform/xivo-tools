from locust import HttpLocust, TaskSet, task
from lxml import html


class AdminUITasks(TaskSet):
    def on_start(self):
        login_page = self.client.get('/admin/login/', verify=False)
        csrf_token = html.fromstring(login_page.content).xpath('//form/input[@id="csrf_token"]/@value')[0]
        self.client.post('/admin/login/', {
            'csrf_token': csrf_token,
            'username': 'locust',
            'password': '1Wraibyorc)',
            'language': 'en',
        })

    @task
    def index(self):
        self.client.get("/admin")

    @task
    def plugins(self):
        self.client.get("/admin/plugins")

    @task
    def users(self):
        self.client.get("/admin/users")


class AdminUIUser(HttpLocust):
    task_set = AdminUITasks
    min_wait = 5000
    max_wait = 15000
