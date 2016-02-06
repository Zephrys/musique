from flask import Flask, flash, request, jsonify, redirect, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
from flask import send_file
from flask.ext.httpauth import HTTPBasicAuth
import soundcloud
from key import client_id
from pprint import pprint
from flask_login import LoginManager, login_user, login_required, logout_user

app = Flask(__name__)
api = Api(app)

# for session management
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


mongoclient = MongoClient('mongodb://localhost:27017/')
sinder = mongoclient.sinder

# create a client object with your app credentials
client = soundcloud.Client(client_id=client_id)


class User():
    username = ""
    password = ""
    is_auth = False

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.is_auth = False

    @classmethod
    def get(cls, id):
        return sinder.userdb.find_one({'_id': id})

    def get_id(self):
        return unicode(sinder.userdb.find_one({'username': self.username}))

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def is_authenticated(self):
        return self.is_auth


@app.route('/', methods=['GET'])
def see():
    return render_template('index.html')


@app.route('/swipe/')
def swipe():
    return render_template('random.html', title='swipe page')


@app.route('/api/')
def get():
    return jsonify({'Yo': 'We are here! :D'}), 200


@app.route('/api/track/', methods=['GET'])
def rate_track():
    """
    :return: save info for user and track and calls get track for next track
    """
    rating = request.args['rating']
    username = request.args['username']

#      put info in recommendation matrix

    get_track()


@app.route('/api/track/', methods=['GET'])
def get_track(track):
    """
    get track info from mongo storage for particular use
    """
    username = request.args['username']

    # get user track from mongo

    track = get_next_suggestion(username)

    return jsonify(get_track_details(track)), 200


@app.route('/newuser/', methods = ['POST'])
def new_user():
    username = request.form.get('username')
    password = request.form.get('password')
    if sinder.userdb.find({'username': username }).count() > 0:
        # pain bro, username already exists
        return jsonify({'error': 'User already exists', 'username': username}), 200

    user = User(username=username, password=password)
    sinder.userdb.insert_one(user.__dict__)
    flash("User Registered!")
    user.is_auth = True
    login_user(user)
    return jsonify({'username': user.username, 'done': True}), 200


@app.route('/logout')
@login_required
def logout():
    logout_user()


@app.route('/', methods=['POST'])
def user_login():
    username = request.form.get('username')
    password = request.form.get('password')

    check_user = sinder.userdb.find({'username': username})[0]

    if check_user.count() <= 0:
        return jsonify({'error': 'User doesn\'t exist :( '}), 401
    else:
        if check_user['username'] == username and check_user['password'] == password:
            # login successful
            login_user(User(username, password))
            flash("Login Successful!")
            return redirect('/swipe')
        else:
            # TODO Add reader for these message on main html pages !!
            flash("Invalid Credentials")
            return jsonify({'status': 'Invalid Credentials'}), 201


def get_track_details(track_no):
    """
    :param track_no: track number as on sound cloud
    :return: fetch and return image, stream url, artist info from sound cloud
    """
    # fetch track to stream
    track = client.get('/tracks/' + str(track_no))

    # get the tracks streaming URL
    stream_url = client.get(track.stream_url, allow_redirects=False)
    artwork_url = str(track.artwork_url).replace("large", "t500x500")
    title = track.title
    user = track.user

    ret = {
        'stream_url': stream_url,
        'artwork_url': artwork_url or 'http://i.imgur.com/bLrm4qD.jpg?1',
        'artists': user['username'],
        'title': title,
    }
    pprint(ret)
    return ret

if __name__ == '__main__':
    app.run(debug=True)
