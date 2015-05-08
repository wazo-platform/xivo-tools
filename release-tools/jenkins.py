class _Jenkins(object):

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def launch(self, section, **kwargs):
        job_name = config.get(section, 'job_name')
        if kwargs:
            self._launch_post(job_name, kwargs)
        else:
            self._launch_get(job_name)

    def _launch_get(self, job_name):
        url = self._build_url('build', job_name)
        params = {'token': self.token}

        return self._get_response('GET', url, params)

    def _launch_post(self, job_name, params):
        url = self._build_url('buildWithParameters', job_name)
        params['token'] = self.token

        self._get_response('POST', url, params)

    def _build_url(self, endpoint, job_name):
        url = "{url}/job/{name}/{endpoint}".format(url=self.url,
                                                   endpoint=endpoint,
                                                   name=job_name)
        return url

    def _get_response(self, method, url, params):
        response = requests.request(method, url, params=params)
        msg = "{}: {}".format(response.status_code, response.text.encode('utf8'))
        assert response.status_code == 201, msg

        return response
