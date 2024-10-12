# app/rbac/constants.py

ROLES = {
    'admin': ['create_user', 'read_user', 'update_user', 'delete_user', 'manage_roles'],
    'manager': ['create_user', 'read_user', 'update_user'],
    'user': ['read_user'],
}