from datetime import datetime
from . import db


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.utcnow)
    reaction = db.Column(db.String(50))

    user = db.relationship('User', back_populates='recommendations')
    movie = db.relationship('Movie', back_populates='recommendations')
    