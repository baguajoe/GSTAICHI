from flask import Blueprint, request, jsonify, abort
from api.models import db, User, Class, Book, Video, Article, SiteSettings
from api.extensions import limiter
from api.tcc_auth import role_required
from api.send_email import send_email
from flask_cors import CORS
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
# from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import func
import os

api = Blueprint('api', __name__)
CORS(api)

MIN_PASSWORD_LENGTH = 8
RESET_TOKEN_MAX_AGE = 60 * 60  # one hour


def _find_user_by_email(email):
    return User.query.filter(func.lower(User.email) == (email or "").strip().lower()).first()


# User Signup
@api.route("/signup", methods=["POST"])
@limiter.limit("10 per hour")
def create_signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()
    if not email or "@" not in email:
        return jsonify({"msg": "Please enter a valid email address."}), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"msg": f"Password must be at least {MIN_PASSWORD_LENGTH} characters."}), 400
    if _find_user_by_email(email):
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password, is_active=True, name=name or None)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 201

# User Login
@api.route("/login", methods=["POST"])
@limiter.limit("10 per minute;50 per hour")
def create_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password") or ""
    user = _find_user_by_email(email)
    if user is None or not check_password_hash(user.password, password):
        return jsonify({"msg": "Invalid email or password"}), 401
    if user.is_suspended:
        return jsonify({"msg": "This account has been suspended. Please contact us for help."}), 403

    user.last_login_at = datetime.utcnow()
    db.session.commit()

    expiration = timedelta(days=7)
    access_token = create_access_token(identity=user.email, expires_delta=expiration)
    return jsonify({"token": access_token, "user": user.serialize_account()}), 200


def _reset_serializer():
    return URLSafeTimedSerializer(os.environ.get("FLASK_APP_KEY", "sample key"), salt="password-reset")


@api.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    data = request.get_json(silent=True) or {}
    user = _find_user_by_email(data.get("email"))
    # Always answer the same way so nobody can test which emails have accounts
    response = jsonify({"msg": "If that email has an account, a reset link is on its way."})
    if user is None:
        return response, 200

    # Including part of the current password hash makes the link stop working once it has been used
    token = _reset_serializer().dumps({"uid": user.id, "ph": user.password[-12:]})
    frontend = os.getenv("FRONTEND_URL", "").rstrip("/")
    link = f"{frontend}/tai-chi-company/reset-password?token={token}"
    settings = SiteSettings.get()
    body = (
        f"Hello{(' ' + user.name) if user.name else ''},\n\n"
        f"Someone asked to reset the password for your {settings.app_name} account.\n"
        f"To choose a new password, open this link within one hour:\n\n{link}\n\n"
        f"If you did not ask for this, you can ignore this email.\n\n"
        f"Need help? Call {settings.contact_phone or ''}\n{settings.school_name}"
    )
    try:
        send_email(recipient=user.email, subject=f"Reset your {settings.app_name} password", body=body)
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
    return response, 200


@api.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"msg": f"Password must be at least {MIN_PASSWORD_LENGTH} characters."}), 400
    try:
        payload = _reset_serializer().loads(data.get("token") or "", max_age=RESET_TOKEN_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return jsonify({"msg": "This reset link has expired or was already used. Please ask for a new one."}), 400
    user = db.session.get(User, payload.get("uid"))
    if user is None or user.password[-12:] != payload.get("ph"):
        return jsonify({"msg": "This reset link has expired or was already used. Please ask for a new one."}), 400
    user.password = generate_password_hash(password)
    db.session.commit()
    return jsonify({"msg": "Your password has been changed. You can sign in now."}), 200

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
    # Member-only Tai Chi Company articles are served by /api/tcc/articles instead
    articles = Article.query.filter(Article.members_only.is_(False)).all()
    return jsonify([article.serialize() for article in articles])

@api.route('/articles/<int:id>', methods=['GET'])
def get_article(id):
    article = Article.query.filter(Article.id == id, Article.members_only.is_(False)).first_or_404()
    return jsonify(article.serialize())


@api.route("/articles", methods=["POST"])
@role_required("admin")
def add_article():
    data = request.get_json()

    article = Article(
        title=data.get("title"),
        section=data.get("section", "Other"),
        content=data.get("content"),
        author=data.get("author"),
    )
    db.session.add(article)
    db.session.commit()
    return jsonify({"message": "Article added successfully"}), 201

@api.route('/articles/<int:id>', methods=['PUT'])
@role_required("admin")
def update_article(id):
    data = request.get_json()
    article = Article.query.get_or_404(id)

    if 'title' in data:
        article.title = data['title']
    if 'content' in data:
        article.content = data['content']
    if 'section' in data:
        article.section = data['section']
    if 'author' in data:
        article.author = data['author']

    db.session.commit()
    return jsonify({'message': 'Article updated successfully', 'article': article.serialize()})

@api.route('/articles/<int:id>', methods=['DELETE'])
@role_required("admin")
def delete_article(id):
    article = Article.query.get_or_404(id)
    db.session.delete(article)
    db.session.commit()
    return jsonify({'message': 'Article deleted successfully'})

@api.route("/purchase-notification", methods=['POST'])
def purchase_notification():
    """Send email notification when a purchase is completed"""
    data = request.get_json()
    
    # Build items list for email
    items_list = ""
    for item in data.get('items', []):
        items_list += f"  - {item.get('name')} (Qty: {item.get('quantity')}) - ${item.get('price')}\n"
    
    email_body = f"""
New Purchase Completed!

Order ID: {data.get('orderId')}
Transaction ID: {data.get('transactionId')}

Customer Information:
  Name: {data.get('payerName')}
  Email: {data.get('payerEmail')}

Shipping Address:
{data.get('shippingAddress', 'Not provided')}

Order Details:
{items_list}
Subtotal: ${data.get('subtotal')}
Shipping: ${data.get('shipping')}
Total: ${data.get('total')}

Shipping Region: {data.get('shippingRegion')}
"""
    
    try:
        recipient = os.getenv("NOTIFICATION_EMAIL", os.getenv("GMAIL"))
        send_email(
            recipient=recipient,
            subject=f"New Purchase - ${data.get('total')} - {data.get('payerName')}",
            body=email_body
        )
        return jsonify({"message": "Notification sent successfully"}), 200
    except Exception as e:
        print(f"Failed to send purchase notification: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
            recipient=os.getenv("NOTIFICATION_EMAIL", os.getenv("GMAIL")),
            subject="New Contact Form Submission - Gin Soon Tai Chi",
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

