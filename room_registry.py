# room_registry.py
from rooms import Room

ROOMS = {}

def create_room(request_id, ttl=30):
    room = Room(request_id, ttl)
    ROOMS[room.room_id] = room
    return room

def cleanup_rooms():
    for rid, room in list(ROOMS.items()):
        if room.expired() or room.closed:
            del ROOMS[rid]
