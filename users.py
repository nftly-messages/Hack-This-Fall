import atexit
import json
import base64

with open('database/backup', 'r+') as backup:
    data = json.loads(backup.read() or '{}')
    users = data.get('users') or {}
    posts = data.get('posts') or {}
    pid = data.get('pid') or 0

@atexit.register
def backup():
    data = {
        'users': users,
        'posts': posts,
        'pid': pid
    }
    with open('database/backup', 'w') as backup:
        json.dump(data, backup)

def make_data(payload):
    return {
        "username": payload['identifier'],
        "posts": []
    }

def getscore(post):
    return len(post['up']) - len(post['down'])

def get_userdata(payload):
    user_id = payload.get('user_id')
    if data := users.get(user_id):
        return data
    else:
        return users.setdefault(user_id, make_data(payload))

def get_posts(num=10, page=0, user=None):
    if user:
        lposts = [posts[str(p)] for p in users[user]['posts']]
    else:
        lposts = list(posts.values())
    return sorted(lposts[(page + 1) * num:(page + 1) * (num * 2)], key=getscore)[::-1]

def make_post(payload, **data):
    if not data.get('text'):
        return
    global pid
    user_id = payload['identifier']
    posts[str(pid)] = {
        'pid': pid,
        'user': user_id,
        'text': data.get('text'),
        'up': [],
        'down': []
    }
    userdata = get_userdata(payload)
    userdata['posts'].append(pid)
    pid += 1

def upvote(payload, pid):
    post = get_post(pid)
    if post is None or not payload:
        return -1
    user_id = payload['identifier']
    ups = post['up']
    downs = post['down']
    if user_id in ups:
        ups.remove(user_id)
        return 0
    if user_id in downs:
        downs.remove(user_id)
    ups.append(user_id)
    return 1

def downvote(payload, pid):
    post = get_post(pid)
    if post is None or not payload:
        return -1
    user_id = payload['identifier']
    ups = post['up']
    downs = post['down']
    if user_id in downs:
        downs.remove(user_id)
        return 0
    if user_id in ups:
        ups.remove(user_id)
    downs.append(user_id)
    return 1

def get_score(userdata):
    score = 0
    for post_id in userdata['posts']:
        post = get_post(post_id)
        score += (len(post['up']) - len(post['down'])) if post else 0
    return score

def get_post(pid):
    try:
        return posts[str(pid)]
    except Exception as e:
        return None

def delete_post(userdata, post_id):
    if post_id not in userdata['posts']:
        return
    if str(post_id) not in posts:
        return
    userdata['posts'].remove(post_id)
    del posts[str(post_id)]
