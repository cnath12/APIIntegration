# app/models/user.py

class User:
    def __init__(self, username, email, roles=None):
        self.id = str(uuid.uuid4())
        self.username = username
        self.email = email
        self.roles = roles or []

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'roles': self.roles
        }

    @classmethod
    def from_dict(cls, data):
        user = cls(data['username'], data['email'], data.get('roles', []))
        user.id = data['id']
        return user