  
import os
from flask import request, jsonify, url_for, redirect, Response
from flask_admin import Admin, AdminIndexView, expose, BaseView
from .models import db, User, Classes, Book, Video, Article
from flask_admin.contrib.sqla import ModelView

# class AuthenticatedBaseView:
#     def is_accessible(self):
#         auth=request.authorization
#         if not auth:
#             return False
#         return auth.username == os.environ.get("ADMIN_USER", "admin") and \
#                auth.password == os.environ.get("ADMIN_PASS", "your-secure-password") 
        
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        return Response(
            "Logged out successfully. Close this window and reopen the admin page to log in again.",
            401,
            {"WWW-Authenticate": "Basic realm='Login Required'"}
        )

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    
    # Add your models here, for example this is how we add a the User model to the admin
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Classes, db.session))
    admin.add_view(ModelView(Book, db.session))
    # admin.add_view(ModelView(Video, db.session))
    admin.add_view(ModelView(Article, db.session))


    # You can duplicate that line to add mew models
    # admin.add_view(ModelView(YourModelName, db.session))

    admin.add_view(LogoutView(name='Logout', endpoint='logout'))