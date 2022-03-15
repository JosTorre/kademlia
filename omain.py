import asyncio
import logging
from mykademlia.network import Server

def startNodes(nnodes):
    global node
    node = []
    for i in range(nnodes):
        node.append(Server())
        print("Created node: ", node[i].node.long_id)
        port = 1000 + i
        node[i].listen(port)
        node[i].genSigKeys()
    bootstrapNodes(node)

def bootstrapNodes(node):
    for i in range(len(node)):
        port = 1000 + i
        if i > 0:
            toport = port - 1
            node[i].bootstrap([("127.0.0.1", toport)])
        else:
            toport = 1000 + len(node) -1
            node[i].bootstrap([("127.0.0.1", toport)])
        print("Node ", node[i].node.long_id, " connected to port ", toport)

nnodes = input("Number of Nodes: ")
startNodes(int(nnodes))
node[5].publishTransaction(("127.0.0.1",1007),35)
print("Finish")
