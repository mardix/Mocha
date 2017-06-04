

class Request(object):
    def __init__(self):
        self.method = "NO METHOD"
        self.files = []

flask_request = Request()


class _RequestProxy(object):


    @property
    def IS_GET(self):
        return flask_request.method == "GET"

    @property
    def IS_POST(cls):
        return flask_request.method == "POST"

    @property
    def IS_PUT(self):
        return flask_request.method == "PUT"

    @property
    def IS_DELETE(self):
        return flask_request.method == "DELETE"

    def __getattr__(self, item):
        return getattr(flask_request, item)

flask_request.method = "POST"
request = _RequestProxy()



print(request.files)
print(request.method)
print (request.IS_POST)


