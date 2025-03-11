"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import logging
from flask import Flask, request, jsonify, url_for, send_from_directory, Response
from flask_migrate import Migrate
from flask_swagger import swagger
from api.utils import APIException, generate_sitemap
from api.models import db
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from functools import wraps
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

auth = HTTPBasicAuth()

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

# Configure allowed origins
allowed_origins = [
    os.getenv('FRONTEND_URL', 'https://shiny-funicular-9746vqgg99j3qw6-3000.app.github.dev'),
    os.getenv('BACKEND_URL', 'https://shiny-funicular-9746vqgg99j3qw6-3001.app.github.dev')
]

# Configure CORS for different route patterns
CORS(app, resources={
    # API routes - full CORS with credentials
    r"/api/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Request-Id"],
        "supports_credentials": True
    },
    # Admin routes - restricted CORS (typically you only need GET/POST)
    r"/admin/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "25 per minute"]
)

# Add more detailed debug logging for CORS issues
@app.before_request
def log_cors_debug():
    if request.method == 'OPTIONS':
        logger.debug("CORS Preflight request detected")
        if request.path.startswith('/admin/'):
            logger.debug("Admin route preflight")
        else:
            logger.debug("Non-admin route preflight")
            
    logger.debug(f"Origin header: {request.headers.get('Origin')}")
    logger.debug(f"Access-Control-Request-Method: {request.headers.get('Access-Control-Request-Method')}")
    logger.debug(f"Access-Control-Request-Headers: {request.headers.get('Access-Control-Request-Headers')}")

# Authentication only for admin routes
@app.before_request
def before_request():
    # Debug information
    logger.debug(f"Request path: {request.path}")
    logger.debug(f"Request method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    # Skip authentication for all non-admin routes
    if not request.path.startswith('/admin/'):
        logger.debug("Non-admin route, authentication bypassed")
        return None
    
    # For admin routes, apply authentication
    auth = request.authorization
    if not auth:
        logger.debug("No auth provided for admin route")
        return Response(
            "could not verify your access level for admin interface.\n"
            "you have to login with proper credentials", 401,
            {"WWW-Authenticate": "Basic realm='Admin Login Required'"}
        )
    
    ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "your-secured-password")
    
    if auth.username == ADMIN_USER and auth.password == ADMIN_PASS:
        logger.debug("Auth successful for admin route")
        return None
    
    logger.debug("Auth failed for admin route")
    return Response(
        "could not verify your access level for admin interface.\n"
        "you have to login with proper credentials", 401,
        {"WWW-Authenticate": "Basic realm='Admin Login Required'"}
    )

# Add logging for responses
@app.after_request
def after_request(response):
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response headers: {dict(response.headers)}")
    return response

# Handle OPTIONS preflight requests
@app.route('/api/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    logger.debug(f"OPTIONS request for /api/{path}")
    return app.make_default_options_response()

app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET')  # Change this!
jwt = JWTManager(app)

# database configuration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)

# Add all endpoints form the API with a "api" prefix
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # avoid cache memory
    return response

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)