from . import db


class Role(db.Model):
    __tablename__ = 'roles'

    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('actors.id'), primary_key=True)

    movie = db.relationship('Movie', back_populates='roles')
    actor = db.relationship('Actor', back_populates='roles')
