import atexit
import json
import base64

with open('database/backup', 'w+') as backup:
    try:
        data = json.load(backup)
    except Exception as e:
        print(e)
        data = {}
        backup.write('{}')
    users = data.get('users') or {}
    posts = data.get('posts') or []
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
        lposts = [posts[p] for p in users[user]['posts']]
    else:
        lposts = posts
    return sorted(lposts[page:page + num], key=getscore)[::-1]

def make_post(payload, **data):
    if not data.get('text'):
        return
    global pid
    user_id = payload['identifier']
    posts.append({
        'pid': pid,
        'user': user_id,
        'text': data.get('text'),
        'up': [],
        'down': []
    })
    userdata = get_userdata(payload)
    userdata['posts'].append(pid)
    pid += 1

def upvote(payload, pid):
    if not posts or pid < 0 or pid > len(posts):
        return -1
    post = posts[pid]
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
    if not posts or pid < 0 or pid > len(posts):
        return -1
    post = posts[pid]
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
        post = posts[post_id]
        score += len(post['up']) - len(post['down'])
    return score

def get_post(pid):
    try:
        return posts[int(pid)]
    except Exception as e:
        print(e)
        return None
