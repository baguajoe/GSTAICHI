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

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(300), nullable=False)

    def __repr__(self):
        return f"<Class {self.name}>"

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
    section=db.Column(db.String(100), nullable=True, default="Other")
    # content = db.Column(db.Text(collation='utf8mb4_unicode_ci'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # Example for PostgreSQL-compatible unicode collation
    # content = db.Column(db.Text().with_variant(db.Text("C.UTF-8"), 'postgresql'), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    article_photo = db.relationship("ArticlePhoto", back_populates="article", uselist=False)
    article_photos = db.relationship("ArticlePhotos", back_populates="article")

    def __repr__(self):
        return f"<Article {self.title}>"

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "section": self.section,
            "content": self.content,
            "author": self.author,
            "article_photo": self.article_photo.serialize() if self.article_photo else None,
            "article_photos": [photo.serialize() for photo in self.article_photos],
        }

class ArticlePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    article = db.relationship("Article", back_populates="article_photo", uselist=False)

    def __init__(self, public_id, image_url, article_id):
        self.public_id = public_id
        self.image_url = image_url.strip()
        self.article_id = article_id

    def serialize(self):
        return {
            "id": self.id,
            "image_url": self.image_url
        }
    

class ArticlePhotos(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(500), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    article = db.relationship("Article", back_populates="article_photos")

    def __init__(self, public_id, image_url, article_id):
        self.public_id = public_id
        self.image_url = image_url.strip()
        self.article_id = article_id

    def serialize(self):
        return {
            "id": self.id,
            "image_url": self.image_url
        }

