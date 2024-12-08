from flask import Blueprint, request, jsonify, abort
from api.models import db, User, Classes, Book, Video, Article
from flask_cors import CORS
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

api = Blueprint('api', __name__)


# Allow CORS requests to this API
CORS(api)

@api.route("/signup",methods=["POST"])
def create_signup():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exist"}), 400
    
    hashed_password=generate_password_hash(password)
    new_user=User(email=email, password=hashed_password, is_active=True)

    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "user created successfully"}), 201

@api.route("/login",methods=["POST"])
def create_login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    user=User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password, password):
        return jsonify({"msg":"invalid email or password"}), 401
    
    expiration=datetime.timedelta(days=7)
    access_token = create_access_token(identity=user.email, expires_delta=expiration)
    return jsonify({"token": access_token}), 200


@api.route("/private",methods=["GET"])
@jwt_required()
def create_private():
    current_user=get_jwt_identity()
    user=User.query.filter_by(email=current_user).first()
    if not user: 
        return jsonify({"msg":"user not found"}), 404
    
    return jsonify(log_in_as=current_user), 200
   

# Example: Routes for Articles
@api.route('/articles', methods=['GET'])
def get_articles():
    articles = Article.query.all()
    return jsonify([{
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'author': article.author,
        'publication_date': article.publication_date.strftime('%Y-%m-%d'),
        'download_url': article.download_url,
        'is_downloadable': article.is_downloadable
    } for article in articles])


@api.route('/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Article.query.get_or_404(id)
    return jsonify({
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'author': article.author,
        'publication_date': article.publication_date.strftime('%Y-%m-%d'),
        'download_url': article.download_url,
        'is_downloadable': article.is_downloadable
    })

@api.route('/articles', methods=['POST'])
def create_article():
    data = request.get_json()
    if not data or not all(k in data for k in ('title', 'content', 'author', 'publication_date')):
        abort(400)
    article = Article(
        title=data['title'],
        content=data['content'],
        author=data['author'],
        publication_date=datetime.strptime(data['publication_date'], '%Y-%m-%d'),
        download_url=data.get('download_url'),
        is_downloadable=data.get('is_downloadable', True)
    )
    db.session.add(article)
    db.session.commit()
    return jsonify({'message': 'Article created successfully'}), 201

@api.route('/articles/<int:id>', methods=['PUT'])
def update_article(id):
    data = request.get_json()
    article = Article.query.get_or_404(id)
    if 'title' in data:
        article.title = data['title']
    if 'content' in data:
        article.content = data['content']
    if 'author' in data:
        article.author = data['author']
    if 'publication_date' in data:
        article.publication_date = datetime.strptime(data['publication_date'], '%Y-%m-%d')
    if 'download_url' in data:
        article.download_url = data['download_url']
    if 'is_downloadable' in data:
        article.is_downloadable = data['is_downloadable']
    db.session.commit()
    return jsonify({'message': 'Article updated successfully'})

@api.route('/articles/<int:id>', methods=['DELETE'])
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return jsonify({'message': 'Article deleted successfully'})
