import logging
import asyncio
import sys
import json
import pickle

from kademlia.network import Server

if len(sys.argv) != 5:
    print("Usage: python set.py <bootstrap node> <bootstrap port> <key> <value>")
    sys.exit(1)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('kademlia')
log.addHandler(handler)
log.setLevel(logging.DEBUG)
lista = {"timestamp": 1647391451.1517725, "amount": 30, "sender": "a", "receiver": "b"}
nlista = pickle.dumps(lista)
async def run():
    server = Server()
    await server.listen(8469)
    bootstrap_node = (('127.0.0.1', 100))
    await server.bootstrap([bootstrap_node])
    await server.set(lista.get('sender'), nlista)
    server.stop()

asyncio.run(run())
