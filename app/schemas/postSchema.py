from app.schemas import ma 
from marshmallow import fields, validate

class PostSchema(ma.Schema):
    id = fields.Integer(required=False)
    title = fields.String(required=True)
    body = fields.String(required=True)
    user_id = fields.Integer(required=True)

post_schema = PostSchema()
posts_schema = PostSchema(many=True)