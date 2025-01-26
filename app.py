from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, send, join_room, leave_room, disconnect
import redis as r

redis = r.Redis(host='localhost', 
                port=6379,
                charset="utf-8",
                decode_responses=True)

try:
    redis.ping()
    print("Connected to Redis!")
except r.ConnectionError:
    print("Unable to connect to Redis.")

app = Flask(__name__)
app.config['SECRET_KEY']='2193i129emdndnd_0sadm1m2.asd'
socketio = SocketIO(app=app, cors_allowed_origins="*")

@socketio.on('login')
def handle_connect(data):
    username = data['username']
    password = data['password']

    if(redis.get('user'+username) != password):
        emit('notification', 'Username or password is incorrect')
        return

    rooms = redis.smembers('rmm'+username)
    for room in rooms:
        join_room(room)
        emit("joinRoom", room)

    redis.set('sid'+request.sid, username)
    emit('login_success', username)
    emit('myRooms', list(rooms))
    emit('notification', f'You\'re logged as {username}')

@socketio.on('register')
def handle_register(data):
    username = data['username']
    password = data['password']
    if(redis.get('user'+username) != None):
        emit('notification', 'Username already exists')
        return

    if(len(password)<8):
        emit('notification', 'Password must be at least 8 characters')
        return

    redis.set('user'+username, password)
    emit('notification', 'Registration successful')

@socketio.on('disconnect')
def handle_disconnect():
    print("Disconnected")
    redis.delete('sid'+request.sid)

@socketio.on('join')
def handle_join(data):
    room = data['name']
    room_password = data['password']

    if(redis.get('sid'+request.sid) == None):
        emit('notification', 'You are not logged in')
        return

    if(redis.get('room'+room) == None):
        emit('notification', 'Room does not exist')
        return

    if(redis.get('room'+room) != room_password):
        emit('notification', 'Password incorrect')
        return

    user = redis.get('sid'+request.sid)
    user_rooms = redis.smembers('rmm'+user)
    if(not room in user_rooms):
        redis.sadd('rmm'+user, room)

    join_room(room)        
    emit("room_incoming",[room, {"alert":f"{user} joined",}], room=room)
    emit("notification", f"You're in {room}")
    emit("joinRoom", room)
    print(f"{user} joined")

@socketio.on('create_room')
def handle_create_room(data):
    room = data['name']
    password = data['password']

    user = redis.get('sid'+request.sid)
    if(user == None):
        emit('notification', 'You are not logged in')
        return

    if(redis.get('sid'+request.sid) == None):
        emit('notification', 'You are not logged in')
        return


    if(redis.get('room'+room) != None):
        emit('notification', 'Room already exists')
        return

    redis.set('room'+room, password)

    user_rooms = redis.smembers('rmm'+user)
    if(not room in user_rooms):
        redis.sadd('rmm'+user, room)


    join_room(room)
    emit("joinRoom", room)
    emit("notification", f"You're in {room}")

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    leave_room(room)

#Send message to room
@socketio.on('message')
def handle_message(data):

    if(redis.get('sid'+request.sid) == None):
        emit('notification', 'You are not logged in')
        return
    
    room = data['room']
    message = data['message']
    user = redis.get('sid'+request.sid)
    emit('room_incoming', [room, {'message': message, 'user': user, }], room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)