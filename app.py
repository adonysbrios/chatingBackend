from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, send, join_room, leave_room, disconnect

app = Flask(__name__)
app.config['SECRET_KEY']='2193i129emdndnd_0sadm1m2.asd'
socketio = SocketIO(app=app, cors_allowed_origins="*")

users = {}

# room: {password: "1234"}
rooms = {}

@socketio.on('login')
def handle_connect(data):
    username = data
    user = {'username': username, 'sid': request.sid, 'rooms': []}
    users[request.sid] = user
    emit('login_success', user)

@socketio.on('disconnect')
def handle_disconnect():
    del users[request.sid]

@socketio.on('join')
def handle_join(data):
    room = data['name']
    room_password = data['password']
    if(room in users[request.sid]['rooms']):
        print("User is in room")
        return
    
    if(rooms[room]['password'] != room_password):
        print("Password incorrect")
        return
    
    join_room(room)
    users[request.sid]['rooms'].append(room)
    emit("room_incoming",[room, {"alert":f"{users[request.sid]['username']} joined",}], room=room)
    emit("notification", f"You're in {room}")
    emit("joinRoom", room)
    print(f"{users[request.sid]['username']} joined")

@socketio.on('create_room')
def handle_create_room(data):
    room = data['name']
    password = data['password']
    if(room in rooms):
        return
    rooms[room] = {'password': password}
    join_room(room)
    emit("joinRoom", room)
    emit("notification", f"You're in {room}")

@socketio.on('leave')
def handle_leave(data):
    room = data['room']
    if(room not in users[request.sid]['rooms']):
        return
    #delete room from user
    users[request.sid]['rooms'].remove(room)
    leave_room(room)

#Send message to room
@socketio.on('message')
def handle_message(data):

    print(data)
    #check if users exists
    if request.sid not in users:
        return
    
    room = data['room']
    message = data['message']
    user = users[request.sid]
    emit('room_incoming', [room, {'message': message, 'user': user, }], room=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)