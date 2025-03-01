"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
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

from functools import wraps
from flask_httpauth import HTTPBasicAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


auth=HTTPBasicAuth()

# from models import Person

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

limiter=Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "25 per minute"]
)


ADMIN_USER = os.environ.get("ADMIN_USER", "admin" )
ADMIN_PASS = os.environ.get("ADMIN_PASS", "your-secured-password")

@auth.verify_password
def verify_password(username, password):
    return username ==ADMIN_USER and password == ADMIN_PASS

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.endpoint == "sitemap":
            return f(*args, **kwargs)
        
        auth=request.authorization
        if not auth:
            return Response(
                "could not verify your access level for url.\n"
                "you have to login with proper credentials", 401,
                {"WWW-Authenticate": "Basic realm='Login Required'"}
            )
        if auth.username == ADMIN_USER and auth.password == ADMIN_PASS:
            return f(*args, **kwargs)
        
        return Response(
            "could not verify your access level for url.\n"
            "you have to login with proper credentials", 401,
            {"WWW-Authenticate": "Basic realm='Login Required'"}
        )
    return decorated

@app.before_request
@require_auth
def before_request():
    pass
        

app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET')  # Change this!
jwt = JWTManager(app)


# database condiguration
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