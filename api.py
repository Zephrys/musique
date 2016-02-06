from flask import Flask, request, jsonify, redirect, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
from flask import send_file
from flask.ext.httpauth import HTTPBasicAuth
import soundcloud
from key import client_id
from pprint import pprint


app = Flask(__name__)
api = Api(app)

# implement after working :)
# auth = HTTPBasicAuth()

mongoclient = MongoClient('mongodb://localhost:27017/')
sinder = mongoclient.sinder

# create a client object with your app credentials
client = soundcloud.Client(client_id=client_id)


class User():
    username = ""
    password = ""

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.route('/', methods=['GET'])
def see():
    return render_template('index.html')


@app.route('/swipe/')
def swipe():
    return render_template('swipe.html', title='swipe page')


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
# @auth.login_required
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
    return jsonify({'username': user.username, 'done': True}), 200


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
            return redirect('/swipe')
            return jsonify({'status': 'Login successful'}), 200
        else:
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
