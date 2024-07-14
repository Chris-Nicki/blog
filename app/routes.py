from . import app, db, limiter, cache
from flask import request, redirect, url_for
from app.schemas.userSchema import user_input_schema, user_output_schema, users_schema, user_login_schema
from app.schemas.postSchema import post_schema, posts_schema
from app.schemas.commentSchema import comment_schema, comments_schema
from marshmallow import ValidationError
from app.models import User, Post, Comment, Role
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.util import encode_token
from app.auth import token_auth


@app.route('/')
def index():
    return redirect(url_for('swagger_ui.show'))


################################
        #Token Route#
################################
@app.route('/token', methods=['POST'])
def get_token():
    if not request.is_json:
        return {"error": "Request body must be application/json"}, 400  
    try:
        data = request.json
        credentials = user_login_schema.load(data)
        query = db.select(User).where(User.username==credentials['username'])
        user = db.session.scalars(query).first()
        if user is not None and check_password_hash(user.password, credentials['password']):
            auth_token = encode_token(user.id)
            return {'token': auth_token}, 200
        else:
            return {"error": "Username and/or password is incorrect"}, 401
    except ValidationError as err:
        return err.messages, 400


################################
        # User Routes#
################################

# Get ALL Users
@app.route('/users', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get__all_users():
    args = request.args
    page = args.get('page', 1, type = int)
    per_page = args.get('per_page', 10, type = int)
    query = db.select(User).limit(per_page).offset((page -1)* per_page)
    all_users = db.session.scalars(query).all()
    return users_schema.jsonify(all_users)

# Get Users by username 
@app.route('/users/username', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get_users():
    args = request.args
    page = args.get('page', 1, type = int)
    per_page = args.get('per_page', 10, type = int)
    search = args.get('search')
    query = db.select(User).where(User.username.like(f'%{search}%')).limit(per_page).offset((page -1)* per_page)
    users = db.session.scalars(query).all()
    return users_schema.jsonify(users)

# Get User by ID
@app.route('/users/<int:id>', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get_single_user(id):
    user = db.session.get(User, id)
    if user is not None:
        return user_output_schema.jsonify(user)
    return {"error": f"User with ID {id} does not exist"}, 400 

# Create a new User
@app.route('/users' , methods=['POST'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def create_user():
    if not request.is_json:
        return {"error": "Request body must be application/json"}, 400
    try:
        data = request.json
        user_data = user_input_schema.load(data)
        query = db.select(User).where((User.username == user_data ['username']) | (User.email == user_data['email']))
        check_users = db.session.scalars(query).all()
        if check_users:
            return {"error": "User with that username and/or email already exist"}, 400 # Bad Request By Client
        if "role_id" in user_data:
            new_user = User(
            first_name = user_data['first_name'],
            last_name = user_data['last_name'],
            username = user_data['username'],
            email = user_data['email'],
            password = generate_password_hash(user_data['password']),
            role_id = user_data['role_id']
            )
        else:
            new_user = User(
                first_name = user_data['first_name'],
                last_name = user_data['last_name'],
                username = user_data['username'],
                email = user_data['email'],
                password = generate_password_hash(user_data['password'])
        )
        db.session.add(new_user)
        db.session.commit()
        return user_output_schema.jsonify(new_user), 201 
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400

# Updating a User
@app.route('/users/<int:user_id>', methods=['PUT'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Poster')
def update_user(user_id):
    if not request.is_json:
        return {"error": "Request body must be application/json"}, 400 

    try:
        data = request.json
        user_data = user_input_schema.load(data)
        user = db.session.query(User).filter(User.id == user_id).first()
        if user is None:
            return {"error": f"User with Id {user_id} not found"}, 404 
        user.first_name = user_data['first_name']
        user.last_name = user_data['last_name']
        user.username = user_data['username']
        user.email = user_data['email']
        user.password = generate_password_hash(user_data['password'])
        db.session.commit()
        return user_output_schema.jsonify(user), 201  
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400
    
# Delete a User
@app.route('/users/<int:user_id>', methods=['DELETE'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Admin')
def delete_user(user_id):
    try:
        user = db.session.query(User).filter(User.id == user_id).first()
        if user is None:
            return {"error": f"User with Id {user_id} not found"}, 400
        db.session.delete(user)
        db.session.commit()
        return {"messagae": f"User with Id {user_id} deleted successfully"}, 201
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400
    

################################
        # Post Routes#
################################
        
# Get ALL Posts
@app.route('/posts', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get__all_posts():
    args = request.args
    page = args.get('page', 1, type = int)
    per_page = args.get('per_page', 10, type = int)
    query = db.select(Post).limit(per_page).offset((page -1)* per_page)
    all_posts = db.session.scalars(query).all()
    return posts_schema.jsonify(all_posts)

# Get Posts by username 
@app.route('/posts/by_user_id', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get_posts():
    args = request.args
    page = args.get('page', 1, type = int)
    per_page = args.get('per_page', 10, type = int)
    search = args.get('search')
    query = db.select(Post).where(Post.user_id.like(f'%{search}%')).limit(per_page).offset((page -1)* per_page)
    posts = db.session.scalars(query).all()
    return posts_schema.jsonify(posts)

# Get a single Post by ID
@app.route('/posts<int:post_id>', methods = ['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get_single_post(post_id):
    post = db.session.get(Post, post_id)
    if post is not None:
        return post_schema.jsonify(post)
    return {"error": f"Post with ID {post_id} does not exist."}, 404 
#Create a new Post
@app.route('/posts', methods = ['POST'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Poster')
def create_post():
    logged_in_user = token_auth.current_user()
    print (f'{logged_in_user} is creating a new post.')
    if not request.is_json:
        return {"error": "Request body must be application/json."}, 400 
    try:
        raw_data = request.json
        post_data = post_schema.load(raw_data)
        
        new_post = Post(
            title = post_data['title'],
            body = post_data['body'],
            user_id = post_data['user_id']
        )
        db.session.add(new_post)
        db.session.commit()
        return post_schema.jsonify(new_post), 201 
    except ValidationError as err:
        return err.messages, 400
   
# Update a Post 
@app.route('/posts/<int:post_id>', methods=['PUT'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Poster')
def update_post(post_id):
    if not request.is_json:
        return {"error": "Request  body must be in application/json."}, 400
    try:
        raw_data = request.json
        post_data = post_schema.load(raw_data)
        post = db.session.query(Post).filter(Post.id == post_id).first()
        if post is None:
            return {"error": f"Post with Id {post_id} not found"}, 404
        post.title = post_data['title']
        post.body = post_data['body']
        post.user_id = post_data['user_id']
        db.session.commit()
        return post_schema.jsonify(post), 201
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400
    
# Delete a Post
@app.route('/posts/<int:post_id>', methods=["DELETE"])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Admin')
def delete_post(post_id):
    try:
        post =db.session.query(Post).filter(Post.id ==post_id).first()
        if post is None:
            return {"error": f"Post with Id {post_id} not found"}, 404
        db.session.delete(post)
        db.session.commit()
        return {"message": f"Post with Id {post_id} deleted successfully"}, 201
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400
            
##########################
    #Comments Routes#
##########################

# Get ALL Comments
@app.route('/comments', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get__all_comments():
    args = request.args
    page = args.get('page', 1, type = int)
    per_page = args.get('per_page', 10, type = int)
    query = db.select(Comment).limit(per_page).offset((page -1)* per_page)
    all_comments= db.session.scalars(query).all()
    return posts_schema.jsonify(all_comments)

# Get Comments by username 
@app.route('/comments/username', methods=['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get_comments():
    args = request.args
    page = args.get('page', 1, type = int)
    per_page = args.get('per_page', 10, type = int)
    search = args.get('search')
    query = db.select(Comment).where(Comment.username.like(f'%{search}%')).limit(per_page).offset((page -1)* per_page)
    comments = db.session.scalars(query).all()
    return comments_schema.jsonify(comments)

# Get a single Comment by ID
@app.route('/comments<int:comment_id>', methods = ['GET'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
def get_single_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if comment is not None:
        return comment_schema.jsonify(comment)
    return {"error": f"Post with ID {comment_id} does not exist."}, 404 

#Create a new Comment
@app.route('/comments', methods = ['POST'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Poster')
def create_comment():
    logged_in_user = token_auth.current_user()
    print (f'{logged_in_user} is creating a new comment.')
    if not request.is_json:
        return {"error": "Request body must be application/json."}, 400 
    try:
        raw_data = request.json
        comment_data = comment_schema.load(raw_data)
        
        new_comment = Comment(
            user_id = comment_data['user_id'],
            username = comment_data['username'],
            comment_body = comment_data['comment_body']
        )
        db.session.add(new_comment)
        db.session.commit()
        return comment_schema.jsonify(new_comment), 201 
    except ValidationError as err:
        return err.messages, 400
   
# Update a Comment 
@app.route('/comments/<int:comment_id>', methods=['PUT'])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Poster')
def update_comment(comment_id):
    if not request.is_json:
        return {"error": "Request  body must be in application/json."}, 400
    try:
        raw_data = request.json
        comment_data = comment_schema.load(raw_data)
        comment = db.session.query(Comment).filter(Comment.id == comment_id).first()
        if comment is None:
            return {"error": f"comment with Id {comment_id} not found"}, 404
        comment.user_id = comment_data['user_id']
        comment.username = comment_data['username']
        comment.comment_body = comment_data['comment_body']
        db.session.commit()
        return comment_schema.jsonify(comment), 201
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400
    
# Delete a Comment

@app.route('/comments/<int:comment_id>', methods=["DELETE"])
@cache.cached(timeout=60)
@limiter.limit("100 per hour")
@token_auth.login_required(role='Admin')
def delete_comment(comment_id):
    try:
        comment =db.session.query(Comment).filter(Comment.id ==comment_id).first()
        if comment is None:
            return {"error": f"comment with Id {comment_id} not found"}, 404
        db.session.delete(comment)
        db.session.commit()
        return {"message": f"comment with Id {comment_id} deleted successfully"}, 201
    except ValidationError as err:
        return err.messages, 400
    except ValueError as err:
        return {"error": str(err)}, 400