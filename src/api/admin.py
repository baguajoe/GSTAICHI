import os
from flask import request, jsonify, url_for, redirect, Response
from flask_admin import Admin, AdminIndexView, expose, BaseView
from .models import db, User, Classes, Book, Video, Article
from flask_admin.contrib.sqla import ModelView

# No need for authentication class since auth is handled at the app level
# We can focus ModelView on just model functionality

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        return Response(
            "Logged out successfully. Close this window and reopen the admin page to log in again.",
            401,
            # {"WWW-Authenticate": "Basic realm='Login Required'"}
        )

def setup_admin(app):
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    
    # Create admin with custom base template if you want to add any global JS/CSS
    admin = Admin(
        app, 
        name='4Geeks Admin', 
        template_mode='bootstrap3'
    )
    
    # Add your models to the admin interface
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Classes, db.session))
    admin.add_view(ModelView(Book, db.session))
    # admin.add_view(ModelView(Video, db.session))
    admin.add_view(ModelView(Article, db.session))

    # Add logout view
    admin.add_view(LogoutView(name='Logout', endpoint='logout'))