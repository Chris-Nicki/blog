from flask_httpauth import   HTTPTokenAuth
from app.utils.util import decode_token
from app.models import User, Role
from app.database import db


token_auth = HTTPTokenAuth(scheme='Bearer')

@token_auth.verify_token
def verify(token):
    user_id = decode_token(token)
    if user_id is not None:
        return db.session.get(User, user_id)
    else:
        return None
    
@token_auth.error_handler
def handle_error(status_code):
    return {"error": "Invalid token. Please Try again"}, status_code

@token_auth.get_user_roles
def get_roles(user):
    if user.role.role_name == 'Admin':
        return [role.role_name for role in db.session.scalars(db.select(Role))]
    else:
        return [user.role.role_name]