from . import db


class Watchlist(db.Model):
    __tablename__ = 'watchlists'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)

    user = db.relationship('User', back_populates='watchlists')
    movie = db.relationship('Movie', back_populates='watchlists')
