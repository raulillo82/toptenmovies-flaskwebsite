from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField
from wtforms.validators import DataRequired, NumberRange
from auth import api_key, api_token
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
# create the extension
db = SQLAlchemy()
# initialize the app with the extension
db.init_app(app)


#Create table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)
    # Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Book {self.title}>'


#Create table schema
with app.app_context():
    db.create_all()

#TEST to create one entry manually
#new_movie = Movie(
#    title="Phone Booth",
#    year=2002,
#    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#    rating=7.3,
#    ranking=10,
#    review="My favourite character was the caller.",
#    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#)
#with app.app_context():
#    db.session.add(new_movie)
#    db.session.commit()

#Yet another TEST to create one entry manually
#second_movie = Movie(
#    title="Avatar The Way of Water",
#    year=2022,
#    description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#    rating=7.5,
#    ranking=9,
#    review="I liked the water.",
#    img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
#)
#with app.app_context():
#    db.session.add(second_movie)
#    db.session.commit()


class MovieEditForm(FlaskForm):
    rating = DecimalField('Your rating out of 10, e.g. 7.5',
                         validators=[DataRequired(),
                                     NumberRange(min=0.0, max=10.0)])
    review = StringField('Your review', validators=[DataRequired()])
    submit = SubmitField('Done')


class MovieAddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    movies_query = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars()
    movies_list = movies_query.all()
    for i in range(len(movies_list)):
        #Update DB rankings
        movies_list[i].ranking = len(movies_list)-i
    db.session.commit()
    return render_template("index.html", movies=movies_list)


@app.route('/edit', methods=["GET", "POST"])
def rate_movie():
    form = MovieEditForm()
    movie_id = request.args.get("id")
    if form.validate_on_submit():
        #Write to the db
        movie_to_update = db.get_or_404(Movie, movie_id)
        movie_to_update.rating = request.form["rating"]
        movie_to_update.review = request.form["review"]
        db.session.commit()
        return redirect(url_for('home'))

    #Read a Particular Record By Query
    with app.app_context():
        selected_movie = db.get_or_404(Movie, movie_id)
    return render_template("edit.html", form=form, movie=selected_movie)


@app.route('/delete')
def delete():
    #Delete a Particular Record By PRIMARY KEY
    movie_id = request.args.get("id")
    with app.app_context():
        movie_to_delete = db.get_or_404(Movie, movie_id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for("home"))

@app.route('/add', methods=["GET", "POST"])
def add():
    form = MovieAddForm()
    if form.validate_on_submit():
        #Search the movie in the API
        api_key, api_token
        url = f"https://api.themoviedb.org/3/search/movie?query={request.form['title']}&include_adult=false&language=en-US&page=1"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {api_token}"
        }
        response = requests.get(url, headers=headers)
        return render_template("select.html", movies=response.json()["results"])

    return render_template("add.html", form=form)


@app.route('/find')
def find_movie():
    movie_id = request.args.get("id")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    response = requests.get(url, headers=headers)
    response_movie = response.json()
    #Write to the DB:
    new_movie = Movie(
            title=response_movie["title"],
            img_url=
            f"https://image.tmdb.org/t/p/w500/{response_movie['poster_path']}",
            year=response_movie["release_date"].split("-")[0],
            description=response_movie["overview"])
    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for("rate_movie", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
