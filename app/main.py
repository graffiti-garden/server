#!/usr/bin/env python3

import jwt
import uvicorn
from os import getenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from . import rest
# from .pubsub import PubSub
from .schema import validate

app = FastAPI()

# Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Token authorization (generated by auth container)
secret = getenv('AUTH_SECRET')

@app.on_event("startup")
async def startup():
    # Initialize the database
    client = AsyncIOMotorClient('mongo')
    app.db = client.graffiti.objects

    # Create indexes if they don't already exist
    await app.db.create_index('_id')
    await app.db.create_index('_by')
    await app.db.create_index('_key')
    await app.db.create_index('_tags')
    await app.db.create_index('_to')

    # Initialize database interfaces
    # TODO: PubSub

@app.websocket("/")
async def query_socket(ws: WebSocket, token: str|None=None):
    await ws.accept()
    # Perform authorization
    owner_id = None
    if token:
        try:
            token = jwt.decode(token, secret, algorithms=["HS256"])
            assert token["type"] == "token"
            owner_id = token["owner_id"]
        except:
            await ws.send_json({
                'error': 'authorization',
                'detail': 'invalid token'
            })

    # Register with the pub/sub manager
    # async with app.pubsub.register(ws) as socket_id:
    socket_id = None

    # Send messages back and forth
    while True:
        try:
            msg = await ws.receive_json()
            await reply(ws, msg, socket_id, owner_id)
        except:
            break

async def reply(ws, msg, socket_id, owner_id):
    # Initialize the output
    output = {}
    if 'messageID' in msg:
        output['messageID'] = msg['messageID']

    # Make sure the message is formatted properly
    try:
        validate(msg)
    except Exception as e:
        output['error'] = 'validation'
        output['detail'] = str(e).split('\n')[0]
        await ws.send_json(output)
        return

    # Pass it to the proper function
    try:

        if 'object' in msg:
            result = await rest.update(app, msg['object'], owner_id)

        elif msg.keys() >= { 'userID', 'objectKey' }:
            result = await rest.get(app, msg['userID'], msg['objectKey'], owner_id)

        elif 'objectKey' in msg:
            result = await rest.remove(app, msg['objectKey'], owner_id)

        # elif 'tags_since' in msg:
            # result = await app.pubsub.subscribe(msg['tags_since'], socket_id, owner_id)

        # elif 'tags' in msg:
            # result = await app.pubsub.unsubscribe(msg['tags'], socket_id, owner_id)

        else:
            result = await rest.tags(app, owner_id)

        output["result"] = result

    except Exception as e:
        output['error'] = 'unknown'
        output['detail'] = str(e)

    finally:
        await ws.send_json(output)

if __name__ == "__main__":
    args = {}
    if getenv('DEBUG') == 'true':
        args['reload'] = True
    uvicorn.run('app.main:app', host='0.0.0.0', **args)
