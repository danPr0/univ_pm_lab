from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .actor import Actor
from .embedding import Embedding
from .genre import Genre
from .movie import Movie
from .movie_genre import MovieGenre
from .recommendation import Recommendation
from .role import Role
from .user import User
from .watchlist import Watchlist
