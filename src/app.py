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
from werkzeug.middleware.proxy_fix import ProxyFix

from functools import wraps
from api.extensions import limiter
from api.taichi_company import tcc

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False
# Render puts one proxy in front of the app; trust its X-Forwarded-For/Proto so rate limits
# apply per visitor (not to the proxy's IP) and redirects use https
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

def _with_www_twin(url):
    """https://example.org -> also https://www.example.org (and the other way), so both addresses work."""
    url = (url or "").rstrip("/")
    if "://" not in url:
        return [url] if url else []
    scheme, host = url.split("://", 1)
    twin = host[4:] if host.startswith("www.") else f"www.{host}"
    return [url] if "localhost" in host or host.count(".") == 0 else [url, f"{scheme}://{twin}"]


# Configure allowed origins
allowed_origins = (
    _with_www_twin(os.getenv('FRONTEND_URL') or 'https://shiny-funicular-9746vqgg99j3qw6-3000.app.github.dev')
    + [(os.getenv('BACKEND_URL') or 'https://shiny-funicular-9746vqgg99j3qw6-3001.app.github.dev').rstrip("/")]
)

# Configure CORS for different route patterns
CORS(app, resources={
    # Video keys: TVs (Chromecast) fetch the key from their own origin. Safe because every key request
    # needs an active playback session (sign-in token + session header, or the signed ?t= token); no cookies.
    r"/api/tcc/key/*": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Authorization", "X-Playback-Session"],
        "supports_credentials": False
    },
    # API routes - full CORS with credentials
    r"/api/*": {
        "origins": allowed_origins,
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Request-Id", "X-Playback-Session"],
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

# Set RATELIMIT_ENABLED=false only for local automated testing
app.config["RATELIMIT_ENABLED"] = os.getenv("RATELIMIT_ENABLED", "true").lower() != "false"
limiter.init_app(app)

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

# Admin routes are protected inside api/admin.py: only logged-in users with role "admin" get in.

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

app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY') or os.environ.get('JWT_SECRET')

# Session cookie is only used for the /admin login
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = ENV == "production"
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
app.register_blueprint(tcc, url_prefix='/api/tcc')

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