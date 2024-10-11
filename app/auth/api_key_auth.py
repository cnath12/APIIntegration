from flask import request

class APIKeyAuth:
    def __init__(self, app):
        self.app = app

    def check_api_key(self):
        api_key = request.headers.get('X-API-Key')
        if api_key is None:
            return False
        result = api_key == self.app.config['API_KEY']
        return result