from . import db



class Actor(db.Model):
    __tablename__ = 'actors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    roles = db.relationship('Role', back_populates='actor', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Actor {self.name}>'
