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
    url = db.Column(db.String(2083), nullable=False)  # URL for video file
    streaming_url = db.Column(db.String(2083), nullable=True)  # URL for streaming (HLS or DASH)
    duration = db.Column(db.Interval, nullable=True)
    is_downloadable = db.Column(db.Boolean, default=True)
    is_streamable = db.Column(db.Boolean, default=True)  # New field: Streamable option
    category = db.Column(db.String(100), nullable=True)
    tags = db.Column(db.String(300), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    purchases = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Video {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "streaming_url": self.streaming_url,
            "duration": str(self.duration) if self.duration else None,
            "is_downloadable": self.is_downloadable,
            "is_streamable": self.is_streamable,
            "category": self.category,
            "tags": self.tags.split(',') if self.tags else [],
            "price": self.price,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "views": self.views,
            "purchases": self.purchases,
        }

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    section=db.Column(db.Text, nullable=True, default="Other")
    # content_part1 = db.Column(db.Text, nullable=False)
    # content_part2 = db.Column(db.Text, nullable=False)
    content_part1 = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=False)
    content_part2 = db.Column(db.Text(collation='utf8mb4_unicode_ci'))
    author = db.Column(db.String(100), nullable=False)
    publication_date = db.Column(db.Date, nullable=False)
    download_url = db.Column(db.String(2083), nullable=True)
    is_downloadable = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Article {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "section": self.section,
            "content_part1": self.content_part1,
            "content_part2": self.content_part2,
            "author": self.author,
            "publication_date": self.publication_date.strftime("%Y-%m-%d"),
            "download_url": self.download_url,
            "is_downloadable": self.is_downloadable,
        }
