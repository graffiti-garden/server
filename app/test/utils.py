import jwt
import json
import string
import random
from hashlib import sha256
from os import getenv
import websockets

def random_id(n=20):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(n))

def random_sha():
    return sha256(random_id().encode()).hexdigest()

def object_base(owner_id, proof=None):
    object_base = {
        '_key': random_id(),
        '_by': owner_id,
        '_tags': ['something']
    }
    return object_base

def owner_id_and_token():
    secret = getenv('AUTH_SECRET')
    id_ = random_sha()
    token = jwt.encode({
        "type": "token",
        "owner_id": id_
        }, secret, algorithm="HS256")
    return id_, token

def websocket_connect(token=None):
    link = "ws://localhost:8000"
    if token:
        link += f"?token={token}"
    return websockets.connect(link)

async def send(ws, j):
    await ws.send(json.dumps(j))

async def recv(ws):
    return json.loads(await ws.recv())
