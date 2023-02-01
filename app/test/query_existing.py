#!/usr/bin/env python3

import asyncio
from utils import *
import time

async def recv_historical(ws):
    result = { 'update': {}, 'historical': False }
    while 'update' in result and not result['historical']:
        result = await recv(ws)
    return result

async def main():

    custom_tag = random_id()
    custom_tag2 = random_id()
    custom_tag4 = random_id()
    custom_tag3 =  random_id()

    my_id, my_token = owner_id_and_token()
    other_id, other_token = owner_id_and_token()
    another_id, another_token = owner_id_and_token()

    async with websocket_connect(my_token) as ws:
        print("adding 10 objects")
        for i in range(10):
            base = object_base(my_id)
            await send(ws, {
                'messageID': random_id(),
                'update': base | {
                    '_tags': [custom_tag],
                    'content': random_id(),
                }
            })
            result = await recv_historical(ws)
            assert result['reply'] == 'inserted'
        print("...added")

        print("querying for them")
        await send(ws, {
            'messageID': random_id(),
            'subscribe': [custom_tag]
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'subscribed'
        for i in range(10):
            result = await recv_historical(ws)
            assert 'update' in result
            assert result['update']['_tags'] == [custom_tag]
        print("...received")

        # Try subscribing again
        await send(ws, {
            'messageID': random_id(),
            'subscribe': [custom_tag]
        })
        result = await recv_historical(ws)
        assert 'error' in result
        print("Could not subscribe again")

        print("unsubscribing")
        await send(ws, {
            'messageID': random_id(),
            'unsubscribe': [custom_tag]
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'unsubscribed'

        # Try unsubscribing again
        await send(ws, {
            'messageID': random_id(),
            'unsubscribe': [custom_tag]
        })
        result = await recv_historical(ws)
        assert 'error' in result
        print("Could not unsubscribe again")

        # Adding items with multiple tags and combinations
        base = object_base(my_id)
        await send(ws, {
            'messageID': random_id(),
            'update': base | {
                '_tags': [custom_tag2],
                'something': 'one'
            }
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'inserted'
        base = object_base(my_id)
        await send(ws, {
            'messageID': random_id(),
            'update': base | {
                '_tags': [custom_tag4],
                'something': 'two'
            }
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'inserted'
        base = object_base(my_id)
        await send(ws, {
            'messageID': random_id(),
            'update': base | {
                '_tags': [custom_tag4, custom_tag2],
                'something': 'three'
            }
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'inserted'
        print("...added")

        # Try subscribing again
        print("Subscribing to the tags")
        await send(ws, {
            'messageID': random_id(),
            'subscribe': [custom_tag2, custom_tag4]
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'subscribed'
        results = [ await recv_historical(ws) for i in range(3) ]
        outputs = [ result["update"]["something"] for result in results ]
        assert 'one' in outputs
        assert 'two' in outputs
        assert 'three' in outputs
        print("All results received")
        assert not await another_message(ws, recv=recv_historical)
        print("no more results received")

        base = object_base(my_id)
        await send(ws, {
            'messageID': random_id(),
            'update': base | {
                'content': 'qwerty',
                '_tags': [custom_tag3],
                '_to': [other_id]
            }
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'inserted'
        print("Created a private object")

        await send(ws, {
            'messageID': random_id(),
            'subscribe': [custom_tag3]
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'subscribed'
        result = await recv_historical(ws)
        assert result['update']['content'] == 'qwerty'
        print("Creator can see it")

    async with websocket_connect(other_token) as ws:

        # Recipient can see it
        await send(ws, {
            'messageID': random_id(),
            'subscribe': [custom_tag3]
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'subscribed'
        result = await recv_historical(ws)
        assert result['update']['content'] == 'qwerty'
        print("Recipient can see it")

    async with websocket_connect(another_token) as ws:

        await send(ws, {
            'messageID': random_id(),
            'subscribe': [custom_tag3]
        })
        result = await recv_historical(ws)
        assert result['reply'] == 'subscribed'
        print("Snoop cannot see it")

if __name__ == "__main__":
    asyncio.run(main())
