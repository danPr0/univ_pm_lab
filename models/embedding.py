from pgvector.sqlalchemy import Vector
from . import db


class Embedding(db.Model):
    __tablename__ = 'embeddings'

    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    embedding = db.Column(Vector, nullable=False)

    movie = db.relationship('Movie', back_populates='embedding')
