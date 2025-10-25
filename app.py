from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_migrate import Migrate
from config import Config
from models import db, Movie, User


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)


@app.route('/')
def index():
    user_id = session.get('user_id')
    user = User.query.get(user_id) if user_id else None
    movies = Movie.query.order_by(Movie.date.desc().nullslast()).all()
    return render_template('index.html', user=user, movies=movies)


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


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
