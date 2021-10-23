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

def pint(s):
    try:
        return int(s)
    except:
        return

@app.route('/')
def index():
    num = pint(request.args.get('n')) or 10
    page = pint(request.args.get('p')) or 0
    payload = get_payload()
    if payload and verifyToken(payload):
        return render_template('index.html', userdata=users.get_userdata(payload), posts=users.get_posts(num, page))
    else:
        return render_template('index.html', posts=users.get_posts(num, page))

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

@app.route("/logout")
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('userID', '', expires=0)
    return resp

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

@app.route("/delete/<pid>", methods=['POST'])
def delete_post(pid):
    payload = get_payload()
    if not (payload and verifyToken(payload)):
        return make_response({'failed': 'not authenticated'}, 403)
    userdata = users.get_userdata(payload)
    post_id = pint(post_id)
    if post_id is None or post_id not in userdata['posts']:
        return make_response({'failed': 'not found'}, 404)
    userdata['posts'].remove(post_id)
    users.posts[post_id] = None
    return make_response({}, 200)

@app.template_filter('get_score')
def get_score(userdata):
    return users.get_score(userdata)

app.run()
