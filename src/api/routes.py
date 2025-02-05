from flask import Blueprint, request, jsonify, abort
from api.models import db, User, Classes, Book, Video, Article
from api.send_email import send_email
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
# from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

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

@api.route("/contact", methods=['POST'])
def submit_contact():
    data= request.get_json()
    name=data.get("name")
    email=data.get("email")
    message=data.get("message")

    if not all([name, email,  message]):
        return jsonify({"error":  "all fields are required"}),  400
    
    try:
        email_body = f"New contact form submission:\n\nName: {name}\nEmail: {email}\n\nMessage:\n{message}"

        send_email(
            recipient=os.getenv("GMAIL"),
            subject="New Contact Form Submission",
            body=email_body
        )

        return jsonify ({"message": "Contact form submitted successfully"}), 200
    
    except Exception as e:
        return jsonify({"error":  str(e)}),  500
    

# #@api.route('/video', methods=['POST'])
# def create_video():
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     # Check if the file type is allowed
#     ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
#     def allowed_file(filename):
#         return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#     if not allowed_file(file.filename):
#         return jsonify({"error": "Invalid file type"}), 400

#     # Save the uploaded file
#     from werkzeug.utils import secure_filename
#     UPLOAD_FOLDER = './uploads/videos'  # Define the upload folder
#     os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

#     filename = secure_filename(file.filename)
#     file_path = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(file_path)

#     # Get additional data from the form
#     data = request.form  # Use form data for additional fields
#     if not data.get('title'):
#         return jsonify({"error": "Title is required"}), 400

#     # Create a new video entry in the database
#     new_video = Video(
#         title=data['title'],
#         description=data.get('description', ''),
#         url=file_path,  # Save the file path in the database
#         streaming_url=data.get('streaming_url', None),
#         duration=data.get('duration', None),
#         is_downloadable=data.get('is_downloadable', True),
#         is_streamable=data.get('is_streamable', True),
#         category=data.get('category', None),
#         tags=data.get('tags', None),
#         price=data.get('price', 0.0)
#     )

#     # Save to the database
#     db.session.add(new_video)
#     db.session.commit()

#     return jsonify({"message": "Video uploaded and created successfully", "video": new_video.serialize()}), 201




# # Route to delete a video
# @api.route('/video/<int:video_id>', methods=['DELETE'])
# def delete_video(video_id):
#     video = Video.query.get(video_id)

#     # Check if the video exists
#     if not video:
#         return jsonify({"error": "Video not found"}), 404

#     # Delete the video
#     db.session.delete(video)
#     db.session.commit()

#     return jsonify({"message": f"Video with ID {video_id} has been deleted successfully"}), 200

# @api.route('/stream/<video_id>', methods=['GET'])
# def stream_video(video_id):
#     user_id = request.args.get('user_id')
#     video = Video.query.get(video_id)

#     if not video:
#         return jsonify({"error": "Video not found"}), 404

#     if not video.is_streamable:
#         return jsonify({"error": "This video is not available for streaming"}), 403

#     if not user_has_access(user_id, video_id):
#         return jsonify({"error": "Unauthorized access"}), 403

#     # Return the streaming URL
#     return jsonify({"streaming_url": video.streaming_url})



# @api.route('/video/<video_id>', methods=['GET'])
# def get_video(video_id):
#     user_id = request.args.get('user_id')
#     video = Video.query.get(video_id)

#     if not video:
#         return jsonify({"error": "Video not found"}), 404

#     if not user_has_access(user_id, video_id):
#         return jsonify({"error": "Unauthorized access"}), 403

#     # Return the direct video URL (e.g., .mp4 file)
#     return jsonify({"video_url": video.url})

# @api.route('/admin/upload-video', methods=['POST'])
# def admin_upload_video():
#     """Admin-only route to upload videos"""
#     # Ensure the admin provides a file
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400

#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     if not allowed_file(file.filename):
#         return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

#     # Secure the filename and save it
#     filename = secure_filename(file.filename)
#     file_path = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(file_path)

#     # Get additional metadata from the request form
#     data = request.form
#     if not data.get('title'):
#         return jsonify({"error": "Title is required"}), 400

#     # Create a new video entry in the database
#     new_video = Video(
#         title=data['title'],
#         description=data.get('description', ''),
#         url=file_path,  # Path to the uploaded file
#         streaming_url=data.get('streaming_url', None),
#         duration=data.get('duration', None),
#         is_downloadable=data.get('is_downloadable', True),
#         is_streamable=data.get('is_streamable', True),
#         category=data.get('category', None),
#         tags=data.get('tags', None),
#         price=data.get('price', 0.0)
#     )

#     # Save to the database
#     db.session.add(new_video)
#     db.session.commit()

#     return jsonify({"message": "Video uploaded successfully", "video": new_video.serialize()}), 201

# @api.route('/admin/upload-video', methods=['POST'])
# @jwt_required()
# def admin_upload_video():
#     current_user = get_jwt_identity()

#     # Check if the current user is an admin
#     if not current_user.get("is_admin"):
#         return jsonify({"error": "Unauthorized"}), 403

    # Proceed with video upload logic
    ...


# @api.route('/admin/upload-video', methods=['POST'])
# @login_required
# def admin_upload_video():
#     if not current_user.is_admin:
#         return jsonify({"error": "Unauthorized"}), 403

#     # Proceed with video upload logic
#     ...

