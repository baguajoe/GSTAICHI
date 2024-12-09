from flask import Blueprint, request, jsonify, abort
from api.models import db, User, Classes, Book, Video, Article
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

api = Blueprint('api', __name__)
CORS(api)

# User Signup
@api.route("/signup", methods=["POST"])
def create_signup():
    email = request.json.get("email")
    password = request.json.get("password")
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, is_active=True)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 201

# User Login
@api.route("/login", methods=["POST"])
def create_login():
    email = request.json.get("email")
    password = request.json.get("password")
    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid email or password"}), 401

    expiration = timedelta(days=7)
    access_token = create_access_token(identity=user.email, expires_delta=expiration)
    return jsonify({"token": access_token}), 200

# Protected Route
@api.route("/private", methods=["GET"])
@jwt_required()
def create_private():
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify(logged_in_as=current_user), 200

# Articles Routes
@api.route('/articles', methods=['GET'])
def get_articles():
    articles = Article.query.all()
    return jsonify([article.serialize() for article in articles])

@api.route('/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Article.query.get_or_404(id)
    return jsonify(article.serialize())


@api.route("/articles", methods=["POST"])
def add_article():
    data = request.get_json()
    full_content = data.get("content")
    
    # Split the content into two parts
    split_index = len(full_content) // 2
    split_index = full_content.rfind(". ", 0, split_index) + 1

    part1 = full_content[:split_index].strip()
    part2 = full_content[split_index:].strip()

    article = Article(
        title=data.get("title"),
        content_part1=part1,
        content_part2=part2,
        author=data.get("author"),
        publication_date=datetime.strptime(data.get("publication_date"), "%Y-%m-%d")
    )
    db.session.add(article)
    db.session.commit()
    return jsonify({"message": "Article added successfully"}), 201

@api.route('/articles/<int:id>', methods=['PUT'])
def update_article(id):
    data = request.get_json()
    article = Article.query.get_or_404(id)

    if 'title' in data:
        article.title = data['title']
    if 'content_part1' in data:
        article.content_part1 = data['content_part1']
    if 'content_part2' in data:
        article.content_part2 = data['content_part2']
    if 'author' in data:
        article.author = data['author']
    if 'publication_date' in data:
        article.publication_date = datetime.strptime(data['publication_date'], '%Y-%m-%d')
    if 'download_url' in data:
        article.download_url = data['download_url']
    if 'is_downloadable' in data:
        article.is_downloadable = data['is_downloadable']

    db.session.commit()
    return jsonify({'message': 'Article updated successfully', 'article': article.serialize()})

@api.route('/articles/<int:id>', methods=['DELETE'])
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return jsonify({'message': 'Article deleted successfully'})
