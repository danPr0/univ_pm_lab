from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_migrate import Migrate
from config import Config
from models import db, Movie, User, Watchlist


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    movies = Movie.query.order_by(Movie.date.desc().nullslast()).all()

    # Get user's watchlist movie IDs
    watchlist_movie_ids = set()
    if user:
        watchlist_movie_ids = {w.movie_id for w in user.watchlists}

    return render_template('index.html', user=user, movies=movies, watchlist_movie_ids=watchlist_movie_ids)


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


@app.route('/recommendations')
def recommendations():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login to view your recommendations.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(user_id)

    # Get movies from user's watchlist
    liked_movies = db.session.query(Movie).join(
        Watchlist, Movie.id == Watchlist.movie_id
    ).filter(Watchlist.user_id == user_id).order_by(
        Movie.date.desc().nullslast()
    ).all()

    return render_template('recommendations.html', user=user, movies=liked_movies)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)