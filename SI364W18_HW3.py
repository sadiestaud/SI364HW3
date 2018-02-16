## SI 364 - Winter 2018
## HW 3

####################
## Import statements
####################

from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError, IntegerField
from wtforms.validators import Required, Length
from flask_sqlalchemy import SQLAlchemy

############################
# Application configurations
############################
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hard to guess string from si364'
## TODO 364: Create a database in postgresql in the code line below, and fill in your app's database URI. It should be of the format: postgresql://localhost/YOUR_DATABASE_NAME

## Your final Postgres database should be your uniqname, plus HW3, e.g. "jczettaHW3" or "maupandeHW3"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://sadiestaudacher@localhost/sadiesHW3"
## Provided:
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

##################
### App setup ####
##################
# manager = Manager(app) # In order to use manager
db = SQLAlchemy(app) # For database use

#########################
#########################
######### Everything above this line is important/useful setup,
## not problem-solving.##
#########################
#########################

#########################
##### Set up Models #####
#########################

## TODO 364: Set up the following Model classes, as described, with the respective fields (data types).

## The following relationships should exist between them:
# Tweet:User - Many:One
class Tweet(db.Model): # - Tweet
    __tablename__ = 'tweets'
    id = db.Column(db.Integer, primary_key=True) ## -- id (Integer, Primary Key)
    text = db.Column(db.String(280)) ## -- text (String, up to 280 chars)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id')) ## -- user_id (Integer, ID of user posted -- ForeignKey)

    def __repr__(self):
        return "{%r} | (ID: {%r})" % (self.text, self.id) ## __repr__ method that returns strings of a format like: {Tweet text...} (ID: {tweet id})

class User(db.Model): # - User
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True) ## -- id (Integer, Primary Key)
    username = db.Column(db.String(64), unique=True) ## -- username (String, up to 64 chars, Unique=True)
    display_name = db.Column(db.String(124)) ## -- display_name (String, up to 124 chars)

    tweets = db.relationship('Tweet', backref='User')
## ---- Line to indicate relationship between Tweet and User tables (the 1 user: many tweets relationship)
    def __repr__(self):
        return "{%r} | ID: {%r}" % (self.username, self.id) ## Should have a __repr__ method that returns strings of a format like: {username} | ID: {id}

########################
##### Set up Forms #####
########################

# TODO 364: Fill in the rest of the below Form class so that someone running
# this web app will be able to fill in information about tweets they wish
# existed to save in the database:

# TODO 364: Set up custom validation for this form such that:
class TweetForm(FlaskForm):
    text = StringField("Enter a text for a tweet (no longer than 280 characters!): ", validators = [Required(),Length(max=280, message="The tweet cannot be more than 280 characters!")] ) ## -- text: tweet text (Required, should not be more than 280 characters)
    username = StringField("Enter username (cannot be longer than 64 characters): ", validators = [Required(), Length(max=64, message="The user name cannot be more than 64 characters!")] ) ## -- username: the twitter username who should post it (Required, should not be more than 64 characters)
    display_name = StringField("Enter the display name: ", validators = [Required()]) ## -- display_name: the display name of the twitter user with that username (Required, + set up custom validation for this -- see below)
    submit = SubmitField("Submit yo tweeeet")

    def validate_username(form, field):
        if field.data[0] == "@": # - the twitter username may NOT start with an "@" symbol  (the template will put that in where it should appear)
            raise ValidationError('Twitter name cannot start with @')

    def validate_display_name(form, field):
        split_name = field.data.split()
        if len(split_name) < 2: # - the display name MUST be at least 2 words
            raise ValidationError('Display name must be at least 2 words')


###################################
##### Routes & view functions #####
###################################

## Error handling routes - PROVIDED
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

#############
## Main route
#############

@app.route('/', methods=['GET', 'POST'])
def index():
    form = TweetForm(request.form) # Initialize the form
    num_tweets = len(Tweet.query.all()) # Get the number of Tweets
    if form.validate_on_submit(): # If the form was posted to this route, Get the data from the form
        username = form.username.data
        tweet = form.text.data
        display_name = form.display_name.data
        user = User.query.filter_by(username=username).first()     ## Find out if there's already a user with the entered username
        if user:     ## If there is, save it in a variable: user
            print("User Exists")
        else:
            user = User(username=username, display_name = display_name)     ## Or if there is not
            db.session.add(user) #then create one and add it to the database
            db.session.commit()

        # t = Tweet.query.filter_by(text=tweet).first()
        # t_u = Tweet.query.filter_by(user_id = user.id).first()
        if Tweet.query.filter_by(user_id = user.id,text=tweet).first(): ## If there already exists a tweet in the database with this text and this user id (the id of that user variable above...)
            flash("Tweet already exists") ## Then flash a message about the tweet already existing
            return redirect(url_for('all_tweets')) ## And redirect to the list of all tweets
        else: ## Assuming we got past that redirect,
            new_tweet_info = Tweet(text = tweet, user_id = user.id) ## Create a new tweet object with the text and user id
            db.session.add(new_tweet_info) ## And add it to the database
            db.session.commit()
            flash('Tweet added') ## Flash a message about a tweet being successfully added
        return redirect(url_for('index')) ## Redirect to the index page

    # PROVIDED: If the form did NOT validate / was not submitted
    errors = [v for v in form.errors.values()]
    if len(errors) > 0:
        flash("!!!! ERRORS IN FORM SUBMISSION - " + str(errors))
    return render_template('index.html',form = form, num_tweets = num_tweets) # TODO 364: Add more arguments to the render_template invocation to send data to index.html

@app.route('/all_tweets')
def see_all_tweets():
    t_list = Tweet.query.all()

    all_tweets = []
    for tweet in t_list:
        user = User.query.filter_by(id = tweet.user_id).first()
        tupple = (tweet.text, user.username)
        all_tweets.append(tupple)
    return render_template('all_tweets.html', all_tweets = all_tweets)



@app.route('/all_users')
def see_all_users():
    users = User.query.all()
    return render_template('all_users.html', users=users)

@app.route('/longest_tweet') #Create another route (no scaffolding provided) at /longest_tweet
def get_longest_tweet(): #with a view function get_longest_tweet (see details below for what it should do)
    tweets = Tweet.query.all()
    tweet_text = {}
    for tweet in tweets:
        count = 0
        whitespace = ' '
        for character in tweet.text:
            if character != whitespace:
                count += 1
        tweet_text[tweet.text] = count
    sorted_tweet_text = sorted(tweet_text.items(), key = lambda x : x[1], reverse = True)
    text = sorted_tweet_text[0][0]
    longest_tweet = Tweet.query.filter_by(text = text).first()
    u = User.query.filter_by(id = longest_tweet.user_id).first()
    user = u.username
    return render_template('longest_tweet.html', text = text, user = user)




if __name__ == '__main__':
    db.create_all() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual
