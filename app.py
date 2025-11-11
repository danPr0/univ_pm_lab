import numpy as np
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_migrate import Migrate
from sqlalchemy import not_
from sqlalchemy import cast, String

from config import Config
from models import Embedding, Movie, User, Watchlist, Actor, Genre, Role, MovieGenre, db
from scipy.spatial.distance import cosine

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None

    # Getting filters, if there are any. and querying the DB
    name = request.args.get('name', '').strip()
    year = request.args.get('year', '').strip()
    director = request.args.get('director', '').strip()
    studio = request.args.get('studio', '').strip()
    rating = request.args.get('rating', '').strip()
    liked_only = request.args.get('liked_only') == 'true'

    query = Movie.query

    if name:
        query = query.filter(Movie.name.ilike(f'%{name}%'))
    if year:
        query = query.filter(Movie.date.isnot(None), cast(Movie.date, String).like(f'{year}-%'))
    if director:
        query = query.filter(Movie.director.ilike(f'%{director}%'))
    if studio:
        query = query.filter(Movie.studio.ilike(f'%{studio}%'))
    if rating:
        query = query.filter(Movie.rating == rating)

    # Get user's watchlist movie IDs
    watchlist_movie_ids = set()
    if user:
        watchlist_movie_ids = {w.movie_id for w in user.watchlists}
        if liked_only and watchlist_movie_ids:
            query = query.filter(Movie.id.in_(watchlist_movie_ids))
        elif liked_only:
            query = query.filter(False)

    query = query.order_by(Movie.date.desc().nullslast())

    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    movies = pagination.items

    return render_template('index.html', user=user, movies=movies, watchlist_movie_ids=watchlist_movie_ids, pagination=pagination,
        filters={
            'name': name,
            'year': year,
            'director': director,
            'studio': studio,
            'rating': rating,
            'liked_only': liked_only
        })


@app.route('/toggle_watchlist/<int:movie_id>', methods=['POST'])
def toggle_watchlist(movie_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Please login first'}), 401

    user = User.query.get(user_id)
    movie = Movie.query.get(movie_id)

    if not movie:
        return jsonify({'error': 'Movie not found'}), 404

    # Check if movie is already in watchlist
    watchlist_entry = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()

    if watchlist_entry:
        # Remove from watchlist
        db.session.delete(watchlist_entry)
        db.session.commit()
        return jsonify({'status': 'removed', 'in_watchlist': False})
    else:
        # Add to watchlist
        new_entry = Watchlist(user_id=user_id, movie_id=movie_id)
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({'status': 'added', 'in_watchlist': True})


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        login = request.form['login']
        password = request.form['password']

        if User.query.filter_by(login=login).first():
            flash('Login already taken.', 'error')
            return redirect(url_for('signup'))

        user = User(full_name=full_name, login=login)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_name = request.form['login']
        password = request.form['password']

        user = User.query.filter_by(login=login_name).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Welcome back!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/select_likes', methods=['GET', 'POST'])
def select_likes():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    query = (
        db.session.query(Movie)
        .join(Watchlist, Movie.id == Watchlist.movie_id)
        .filter(Watchlist.user_id == user_id)
    )

    filters = {}
    name = request.args.get('name', '').strip()
    year = request.args.get('year', '').strip()
    director = request.args.get('director', '').strip()
    studio = request.args.get('studio', '').strip()
    duration = request.args.get('duration', '').strip()
    rating = request.args.get('rating', '').strip()

    if name:
        query = query.filter(Movie.name.ilike(f"%{name}%"))
        filters['name'] = name
    if year:
        query = query.filter(db.extract('year', Movie.date) == int(year))
        filters['year'] = year
    if director:
        query = query.filter(Movie.director.ilike(f"%{director}%"))
        filters['director'] = director
    if studio:
        query = query.filter(Movie.studio.ilike(f"%{studio}%"))
        filters['studio'] = studio
    if duration:
        query = query.filter(Movie.duration == duration)
        filters['duration'] = duration
    if rating:
        query = query.filter(Movie.rating == rating)
        filters['rating'] = rating

    liked_movies = query.order_by(Movie.date.desc().nullslast()).all()

    if request.method == 'POST':
        selected_ids = request.form.getlist('movie_ids')
        if not selected_ids:
            flash('Please select at least one movie to get recommendations.', 'error')
            return redirect(url_for('select_likes', **filters))

        session['selected_like_ids'] = [int(i) for i in selected_ids]
        return redirect(url_for('recommendations'))

    return render_template('select_likes.html', user=user, liked_movies=liked_movies, filters=filters)

@app.route('/recommendations')
def recommendations(top_n=5, alpha=0.72, beta=0.1, gamma=0.1, delta=0.08):
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to view your recommendations.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    # Get selected movies if any
    selected_ids = session.pop('selected_like_ids', None)

    liked_movies_query = (
        db.session.query(Movie)
        .join(Watchlist, Movie.id == Watchlist.movie_id)
        .filter(Watchlist.user_id == user_id)
    )

    if selected_ids:
        liked_movies_query = liked_movies_query.filter(Movie.id.in_(selected_ids))

    liked_movies = liked_movies_query.order_by(Movie.date.desc().nullslast()).all()

    liked_vectors = [np.array(m.embedding.embedding) for m in liked_movies if m.embedding is not None]
    if not liked_vectors:
        return render_template('recommendations.html', user=user, movies=[])

    user_vec = np.mean(liked_vectors, axis=0)

    liked_directors = set(m.director for m in liked_movies if m.director)

    liked_actors = set(
        a.id
        for m in liked_movies
        for a in db.session.query(Actor)
            .join(Role, Actor.id == Role.actor_id)
            .filter(Role.movie_id == m.id)
        )
    liked_genres = set(
        g.id
        for m in liked_movies
        for g in db.session.query(Genre)
            .join(MovieGenre, Genre.id == MovieGenre.genre_id)
            .filter(MovieGenre.movie_id == m.id)
        )

    candidate_movies = (
        db.session.query(Movie)
        .join(Embedding)
        .filter(Embedding.embedding.is_not(None))
        .filter(not_(Movie.id.in_([m.id for m in liked_movies])))
        .all()
    )

    recommendations = []

    for movie in candidate_movies:
        sim_embedding = 1 - cosine(user_vec, movie.embedding.embedding) if movie.embedding else 0

        same_director = 1 if movie.director in liked_directors else 0

        movie_actors = set(
            a.id
            for a in db.session.query(Actor)
                .join(Role, Actor.id == Role.actor_id)
                .filter(Role.movie_id == movie.id)
        )
        actor_overlap = len(liked_actors & movie_actors) / len(liked_actors | movie_actors) if liked_actors else 0

        movie_genres = set(
            g.id
            for g in db.session.query(Genre)
                .join(MovieGenre, Genre.id == MovieGenre.genre_id)
                .filter(MovieGenre.movie_id == movie.id)
        )
        genre_overlap = len(liked_genres & movie_genres) / len(liked_genres | movie_genres) if liked_genres else 0

        score = alpha * sim_embedding + beta * same_director + gamma * actor_overlap + delta * genre_overlap

        recommendations.append((movie, score))

    recommendations.sort(key=lambda x: x[1], reverse=True)
    top_recom = [m for m, s in recommendations[:top_n]]

    return render_template('recommendations.html', user=user, movies=top_recom)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(use_reloader=False)
