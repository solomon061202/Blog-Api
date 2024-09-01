from flask import Flask, request, jsonify, abort
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from marshmallow import Schema, fields, ValidationError
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Solomon%402002@localhost/blog_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '123456789'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Models
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Schemas
class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)  # Changed from user_name to username
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class PostSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    content = fields.Str(required=True)
    author_id = fields.Int(required=True) 

class CommentSchema(Schema):
    id = fields.Int(dump_only=True)
    post_id = fields.Int(required=True)
    content = fields.Str(required=True)
    author_id = fields.Int(required=True)  
    created_at = fields.DateTime(dump_only=True)

user_schema = UserSchema()
users_schema = UserSchema(many=True)
post_schema = PostSchema()
posts_schema = PostSchema(many=True)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

# Routes for Users
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'New user created!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity={'user_id': user.id, 'username': user.username, 'email': user.email})
        return jsonify(access_token=access_token), 200
    
    return jsonify(message="Invalid credentials"), 401

@app.route('/posts', methods=['POST'])
@jwt_required()
def create_post():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    
    # Assuming admin check is not needed; adjust if necessary
    try:
        data = request.get_json()
        post = post_schema.load(data)
        new_post = Post(**post)
        db.session.add(new_post)
        db.session.commit()
        return jsonify(post_schema.dump(new_post)), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@app.route('/posts', methods=['GET'])
def read_posts():
    posts = Post.query.all()
    return jsonify(posts_schema.dump(posts)), 200

@app.route('/posts/<int:id>', methods=['GET'])
def read_single_post(id):
    post = db.session.get(Post, id)
    return jsonify(post_schema.dump(post)), 200

@app.route('/posts/<int:id>', methods=['PUT'])
@jwt_required()
def update_post(id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    
    # Assuming admin check is not needed; adjust if necessary
    post = Post.query.get_or_404(id)
    data = request.get_json()
    
    if 'title' in data:
        post.title = data['title']
    if 'content' in data:
        post.content = data['content']
    
    db.session.commit()

    return jsonify(post_schema.dump(post)), 200

@app.route('/posts/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_post(id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()
    
    # Assuming admin check is not needed; adjust if necessary
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return '', 204

# Routes for Comments
@app.route('/comments', methods=['POST'])
@jwt_required()
def create_comment():
    current_user = get_jwt_identity()
    data = request.get_json()
    
    try:
        comment_data = comment_schema.load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    new_comment = Comment(
        post_id=comment_data['post_id'],
        content=comment_data['content'],
        author_id=current_user['user_id']  # Use the current user id
    )
    
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify(comment_schema.dump(new_comment)), 201

@app.route('/comments', methods=['GET'])
def read_comments():
    post_id = request.args.get('post_id')

    if post_id:
        comments = Comment.query.filter_by(post_id=post_id).all()
    else:
        comments = Comment.query.all()

    return jsonify(comments_schema.dump(comments)), 200

@app.route('/comments/<int:id>', methods=['GET'])
def read_single_comment(id):
    comment = db.session.get(Comment, id)
    return jsonify(comment_schema.dump(comment)), 200

@app.route('/comments/<int:id>', methods=['PUT'])
@jwt_required()
def update_comment(id):
    current_user = get_jwt_identity()
    comment = Comment.query.get_or_404(id)
    
    if 'content' in request.json:
        comment.content = request.json['content']
    
    db.session.commit()
    return jsonify(comment_schema.dump(comment)), 200

@app.route('/comments/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_comment(id):
    current_user = get_jwt_identity()
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return '', 204

# Error handling
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify(e.messages), 400

if __name__ == '__main__':
    app.run(debug=True)
