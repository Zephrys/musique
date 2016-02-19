from flask import Flask, g, flash, request, jsonify, redirect, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
from flask import send_file

import soundcloud
from key import client_id
from pprint import pprint
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
from get_from_azure import get_from_azure
import random
from decorator import crossdomain

app = Flask(__name__)
api = Api(app)

# for session management
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(id):
    print id
    return User.get(id)


mongoclient = MongoClient('mongodb://localhost:27017/')
sinder = mongoclient.sinder

# create a pclient object with your app credentials
client = soundcloud.Client(client_id=client_id)

@app.before_request
def before_request():
    g.user = current_user


class User(UserMixin):
    _id = 0
    username = ""
    password = ""
    # is_auth = False

    def __init__(self, username, password):
        self._id = username
        self.username = username
        self.password = password
        # self.is_auth = False

    @classmethod
    def get(cls, id):
        obj = sinder.userdb.find_one({'_id': id})
        return User(obj['username'], obj['password'])

    def get_id(self):
        print("returning this from get_id" + unicode(self._id))
        return unicode(self._id)


@app.route('/', methods=['GET'])
def see():
    return render_template('index.html')

@app.route('/getTrack', methods=['GET'])
@crossdomain(origin='*')
def get_stream_url(username=""):
    """
    :param track_no: track number as on sound cloud
    :return: fetch and return image, stream url, artist info from sound cloud
    """
    track_no = request.args['track_no']

    track = client.get('/tracks/' + str(track_no))

    # get the tracks streaming URL
    stream_url = client.get(track.stream_url, allow_redirects=False)


    return jsonify({'stream_url': stream_url.location}),200





@app.route('/swipe/')
@login_required
def swipe():

    return render_template('random.html', song_dict=get_track_details())


@app.route('/track/', methods=['GET', 'OPTIONS'])
@crossdomain(origin='*')
def rate_track():
    """
    :return: save info for user and track and calls get track for next track
    """
    rating = request.args['dir']
    username = request.args['username']
    print request.args

    track_no = request.args['track_no']

    sinder.entries.update({'track_no': track_no, 'username': username}, {'username': username, 'track_no': track_no, 'dir': 1 if rating == "right" else 0}, upsert=True)

    if rating == "right":
        insert_track = sinder.tracklist.find_one({'track_no': track_no})
        sinder.playlist.update({'track_no': track_no, 'username': username}, {'username': username,
                                   'track_no': track_no, 'title': insert_track['title'],
                                   'artwork_url': insert_track['artwork_url'],
                                   'artist': insert_track['artist']}, upsert=True)

    return get_track(username)


@app.route('/playlist/', methods=['GET'])
@login_required
def get_playlist():
    userid = g.user.get_id()

    list_songs = []

    songs = sinder.playlist.find({'username': userid})

    for song in songs:
        if not song.has_key('artwork_url'):
            song['artwork_url'] = 'http://i.imgur.com/bLrm4qD.jpg?1'
        list_songs.append(song)

    print "reached ehre"
    return render_template('playlist.html', list_songs=list_songs)


def get_track(username):
    """
    get track info from azure recommendation engine for particular user
    """
    return jsonify(get_track_details(username)), 200

def get_track_details(username=""):
    """
    :param username: bit of a hack in username
    XXX(psdh) Figure out how do usernames work across AJAX requests
    :return: fetch and return image, stream url, artist info from sound cloud
    """

    try:
        userid = g.user.username
    except:
        userid = username

    print userid
    username = userid


    get_songs = sinder.songsdb.find({'username': username, 'heard': 0})
    if get_songs.count() > 0:
        track = get_songs[0]
        track_no = track['track_no']
        track['heard'] = 1
        sinder.songsdb.update({'_id': track['_id']}, track)
    else:
        track_nos = get_from_azure(sumchar(userid))

        print len(track_nos)


        for track_no in track_nos:
            print "inserting" + track_no  + " + now"
            if sinder.songsdb.find({'track_no': track_no, 'username': userid}).count() == 0:
                sinder.songsdb.insert_one({'track_no': track_no, 'username': userid, 'heard': 0})

        track_no = track_nos[0]
        sinder.songsdb.update({'track_no': track_no, 'username': userid}, {'track_no': track_no, 'username': userid, 'heard': 1})

    # fetch track to stream
    try:
        track = client.get('/tracks/' + str(track_no))
    except:
        # reaching here implies that get track points to a bad url,
        # such songs must be removed from everywhere
        sinder.removesongs.add({'track_no': track_no})
        return get_track_details(username)

    # get the tracks streaming URL
    stream_url = client.get(track.stream_url, allow_redirects=False)
    artwork_url = str(track.artwork_url).replace("large", "t300x300")
    title = track.title
    user = track.user

    if artwork_url == 'None':
        artwork_url = 'http://i.imgur.com/bLrm4qD.jpg?1'

    ret = {
        'track_no': str(track_no),
        'artwork_url': artwork_url,
        'artist': user['username'],
        'title': title,
    }

    copy = {
        'track_no': str(track_no),
        'artwork_url': artwork_url,
        'artist': user['username'],
        'title': title,
    }

    sinder.tracklist.insert_one(copy)

    ret['stream_url'] = stream_url.location

    pprint(ret)
    return ret

@app.route('/register', methods=['POST'])
def new_user():
    username = request.form.get('signup_username')
    password = request.form.get('signup_password')
    pprint(request.form)
    pprint (username)
    pprint(password)
    if sinder.userdb.find({'username': username}).count() > 0:
        # pain bro, username already exists
        return jsonify({'error': 'User already exists', 'username': username, 'status': 0}), 200

    user = User(username=username, password=password)
    print user.__dict__
    login_user(user)

    sinder.userdb.insert_one(user.__dict__)

    return jsonify({'status': 1}), 200


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/login', methods=['POST'])
def user_login():
    print request
    username = request.form.get('username')
    password = request.form.get('password')

    check_user = sinder.userdb.find({'username': username})

    if check_user.count() <= 0:
        return redirect('/')
    else:
        check_user = check_user[0]
        if check_user['username'] == username and check_user['password'] == password:
            # login successful
            user = User(username=username, password=password)
            login_user(user)

            return redirect('/swipe')
        else:
            # TODO Add reader for these message on main html pages !!

            return jsonify({'error': 'Invalid Credentials', 'status': 0}), 200


def sumchar(s):
    ret = 0
    for ch in s:
        ret += ord(ch)

    return ret
app.secret_key = 'shuffle bro kaam kar jae bas'



    
