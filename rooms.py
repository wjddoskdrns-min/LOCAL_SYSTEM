# rooms.py
import time
import uuid

class Room:
    def __init__(self, request_id, ttl_sec=30):
        self.room_id = str(uuid.uuid4())
        self.request_id = request_id
        self.created_at = time.time()
        self.ttl_sec = ttl_sec
        self.closed = False

    def expired(self):
        return time.time() - self.created_at >= self.ttl_sec

    def close(self):
        self.closed = True
