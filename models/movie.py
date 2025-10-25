from . import db


class Movie(db.Model):
    __tablename__ = 'movies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer)
    director = db.Column(db.String(255))
    studio = db.Column(db.String(255))
    rating = db.Column(db.Float)

    embedding = db.relationship('Embedding', back_populates='movie', uselist=False, cascade='all, delete-orphan')
    watchlists = db.relationship('Watchlist', back_populates='movie', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', back_populates='movie', cascade='all, delete-orphan')
    roles = db.relationship('Role', back_populates='movie', cascade='all, delete-orphan')
    movie_genres = db.relationship('MovieGenre', back_populates='movie', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Movie {self.name}>'
