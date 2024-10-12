# app/models/role.py

class Role:
    def __init__(self, name, permissions):
        self.id = str(uuid.uuid4())
        self.name = name
        self.permissions = permissions

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'permissions': self.permissions
        }

    @classmethod
    def from_dict(cls, data):
        role = cls(data['name'], data['permissions'])
        role.id = data['id']
        return role