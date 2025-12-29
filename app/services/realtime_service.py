from app import socketio
from flask_socketio import emit, join_room, leave_room

def notify_new_order(restaurant_id, order_data):
    socketio.emit('new_order', order_data, room=f'restaurant_{restaurant_id}')

def notify_order_update(restaurant_id, order_data):
    socketio.emit('order_update', order_data, room=f'restaurant_{restaurant_id}')

@socketio.on('join_restaurant')
def handle_join(data):
    restaurant_id = data.get('restaurant_id')
    if restaurant_id:
        join_room(f'restaurant_{restaurant_id}')
        emit('joined', {'message': f'Joined restaurant {restaurant_id}'})

@socketio.on('leave_restaurant')
def handle_leave(data):
    restaurant_id = data.get('restaurant_id')
    if restaurant_id:
        leave_room(f'restaurant_{restaurant_id}')
        emit('left', {'message': f'Left restaurant {restaurant_id}'})

@socketio.on('connect')
def handle_connect():
    emit('connected', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    pass

