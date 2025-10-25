from . import db


class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    movie_genres = db.relationship('MovieGenre', back_populates='genre', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Genre {self.name}>'
