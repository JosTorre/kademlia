import asyncio
import logging
from mykademlia.network import Server

async def startNodes(nnodes):
    node=[]
    for i in range(nnodes):
        node.append(Server())
        print("Created node: ", node[i].node.long_id)
        port = 1000 + i
        await node[i].listen(port)
        node[i].genSigKeys()
    await bootstrapNodes(node)

async def bootstrapNodes(node):
    for i in range(len(node)):
        port = 1000 + i
        if i > 0:
            toport = port - 1
            await node[i].bootstrap([("127.0.0.1", toport)])
        else:
            toport = 1000 + len(node) -1
            await node[i].bootstrap([("127.0.0.1", toport)])
        print("Node ", node[i].node.long_id, " connected to port ", toport)

nnodes = input("Number of Nodes: ")
node = asyncio.run(startNodes(int(nnodes)))
