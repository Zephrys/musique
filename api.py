from flask import Flask, g, flash, request, jsonify, redirect, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
from flask import send_file
from flask.ext.httpauth import HTTPBasicAuth
import soundcloud
from key import client_id
from pprint import pprint
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import json
from get_from_azure import get_from_azure

app = Flask(__name__)
api = Api(app)

# for session management
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(username):
    return User.get(username)


mongoclient = MongoClient('mongodb://localhost:27017/')
sinder = mongoclient.sinder

# create a client object with your app credentials
client = soundcloud.Client(client_id=client_id)

@app.before_request
def before_request():
    g.user = current_user


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
        return sinder.userdb.find_one({'username': id})

    def get_id(self):
        return unicode(sinder.userdb.find_one({'username': self.username})['username'])

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

    return render_template('random.html', song_dict=get_track())


@app.route('/api/')
def get():
    return jsonify({'Yo': 'We are here! :D'}), 200


@app.route('/track/', methods=['GET'])
def rate_track():
    """
    :return: save info for user and track and calls get track for next track
    """
    rating = request.args['rating']
    username = request.args['username']

#      put info in recommendation matrix

    get_track()


@app.route('/track/', methods=['GET'])
@login_required
def get_track():
    """
    get track info from azure recommendation engine for particular user
    """
    userid = g.user.get_id()

    # c = sinder.queue.find({'userid': userid, 'status': 'yes'})
    # if c.count() > 0:
    #     c[0].update()

    print userid
    tracks = get_from_azure(str(userid))[0]

    # for track in tracks:
    # return jsonify(get_track_details(tracks)), 200

    pprint(tracks)
    return get_track_details(tracks)


@app.route('/register', methods=['POST'])
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


@app.route('/login', methods=['POST'])
def user_login():
    print request
    username = request.form.get('username')
    password = request.form.get('password')

    check_user = sinder.userdb.find({'username': username})

    if check_user.count() <= 0:
        return redirect('/')
        return json.dumps(dict(success=0, error_msg="User doesn't exists"))
    else:
        check_user = check_user[0]
        if check_user['username'] == username and check_user['password'] == password:
            # login successful
            user = User(_id= check_user['_id'], username=username, password=password)
            login_user(user)
            flash("Login Successful!")
            return redirect('/swipe')
            return jsonify(status=1)
        else:
            # TODO Add reader for these message on main html pages !!
            flash("Invalid Credentials")
            return redirect('/')
            return jsonify(status=0, error_msg="Invalid Credentials")


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

    if artwork_url == 'None':
        artwork_url = 'http://i.imgur.com/bLrm4qD.jpg?1'

    ret = {
        'track_no': str(track_no),
        'stream_url': stream_url.location,
        'artwork_url': artwork_url,
        'artist': user['username'],
        'title': title,
    }
    pprint(ret)
    return ret

if __name__ == '__main__':
    app.secret_key = 'shuffle bro kaam kar jae bas'
    app.run(debug=True)
