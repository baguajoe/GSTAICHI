from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean(), default=True)

    def __repr__(self):
        return f'<User {self.email}>'

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
        }

class Classes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return f"<Classes {self.name}>"

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "date": self.date.strftime('%Y-%m-%d'),
            "location": self.location,
        }

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    publication_date = db.Column(db.Date, nullable=False)
    download_url = db.Column(db.String(2083), nullable=True)
    is_pod_available = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Book {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "price": str(self.price),
            "publication_date": self.publication_date.strftime('%Y-%m-%d'),
            "download_url": self.download_url,
            "is_pod_available": self.is_pod_available,
        }

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(2083), nullable=False)
    duration = db.Column(db.Interval, nullable=True)
    is_downloadable = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Video {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "duration": str(self.duration) if self.duration else None,
            "is_downloadable": self.is_downloadable,
        }

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content_part1 = db.Column(db.Text, nullable=False)
    content_part2 = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    publication_date = db.Column(db.Date, nullable=False)
    download_url = db.Column(db.String(2083), nullable=True)
    is_downloadable = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Article3 {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "content_part1": self.content_part1,
            "content_part2": self.content_part2,
            "author": self.author,
            "publication_date": self.publication_date.strftime("%Y-%m-%d"),
            "download_url": self.download_url,
            "is_downloadable": self.is_downloadable,
        }
