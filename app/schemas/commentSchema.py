from app.schemas import ma
from marshmallow import fields, validate

class CommentSchema(ma.Schema):
    id = fields.Integer(required=False)
    user_id = fields.Integer(required=True)
    username = fields.String(required=True)
    comment_body = fields.String(required=True)

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)