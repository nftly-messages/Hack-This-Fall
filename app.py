from flask import Flask, render_template, request, make_response, redirect, url_for, send_file
from sawo import createTemplate
import requests
import json
import os
from dotenv import load_dotenv
import base64

import users
load_dotenv()
API_KEY = os.getenv("API_KEY")

app = Flask(__name__)
app.static_folder = 'static'
createTemplate("templates/partials", flask=True)

def verifyToken(payload):
    data = {
        'user_id': payload['user_id'],
        'verification_token': payload['verification_token']
    }
    resp = requests.post('https://api.sawolabs.com/api/v1/userverify/', data=data)
    if resp.ok:
        return resp.json()['user_valid']
    else:
        return False

def get_payload():
    b64payload = request.cookies.get('userID')
    payload = json.loads(base64.b64decode(b64payload.encode())) if b64payload else {}
    return payload

def set_payload(payload):
    b64payload = base64.b64encode(json.dumps(payload).encode())
    resp = make_response({'status': 200})
    resp.set_cookie('userID', b64payload)
    return resp

@app.route('/')
def index():
    payload = get_payload()
    if payload and verifyToken(payload):
        return render_template('index.html', userdata=users.get_userdata(payload), posts=users.get_posts())
    else:
        return render_template('index.html', posts=users.get_posts())

@app.route('/user')
def user():
    payload = get_payload()
    if payload and verifyToken(payload):
        userdata = users.get_userdata(payload)
        return render_template('user.html', userdata=userdata, posts=users.get_posts(user=payload['user_id']))
    return redirect('/login_page')

@app.route('/about')
def about():
    payload = get_payload()
    if payload and verifyToken(payload):
        return render_template('about.html', userdata=users.get_userdata(payload))
    else:
        return render_template('about.html')

@app.route("/login_page")
def login_page():
    payload = get_payload()
    if payload and verifyToken(payload):
        return redirect('/user')
    sawo = {
        "auth_key": API_KEY,
        "to": "login",
        "identifier": "email"
    }
    return render_template("login.html", sawo=sawo)

@app.route("/login", methods=["POST", "GET"])
def login():
    payload = json.loads(request.data)["payload"]
    if verifyToken(payload):
        return set_payload(payload)
    return {'status': 404}

@app.route("/new_post", methods=["POST"])
def new_post():
    payload = get_payload()
    if not (payload and verifyToken(payload)):
        return make_response({'failed': 'not authenticated'}, 403)
    users.make_post(payload, **request.form)
    return redirect('/user')

@app.route("/vote/<pid>/<direction>", methods=['POST'])
def vote(pid, direction):
    payload = get_payload()
    try:
        pid = int(pid)
    except:
        return {'status': 404}
    if direction == 'up':
        if users.upvote(payload, pid) == -1:
            return {'status': 404}
        return {'status': 200}
    elif direction == 'down':
        if users.downvote(payload, pid) == -1:
            return {'status': 404}
        return {'status': 200}
    return {'status': 404}

@app.route("/photos/<pid>")
def get_photo(pid):
    post = users.get_post(pid)
    if post is None:
        return send_file(url_for('static', filename='error.png'), mimetype='image/png')
    return send_file(f'database/photos/{pid}.img', mimetype='image/png')

#I MADE A CHANGE WORK

@app.template_filter('get_score')
def get_score(userdata):
    return users.get_score(userdata)

@app.template_filter('get_image')
def get_image(post):
    return f'photos/{post["pid"]}'

app.run()
