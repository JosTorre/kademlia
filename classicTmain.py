import asyncio
import logging
import pickle
import random
import time
import json
import oqs
import sys
from pprint import pprint

from mykademlia.network import Server
from classicTurm.blockchain import classicTurm


async def startNodes(nnodes, algorithm, txperblk):
    global node
    node = []
    for i in range(nnodes):
        node.append(Server())
        print("Created node: ", node[i].node.long_id)
        port = 1000 + i
        await node[i].genECKeys(algorithm)
        await node[i].startLedger(txperblk)
        await node[i].listen(port)
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

async def runLedger(nnodes, txperblk, nblks):
    #Create and add Genesis Block
    await node[1].Genesis()
    #Make transactions and mine blocks
    mined_blocks = 0
    transacted = 0
    while mined_blocks < nblks:
        rn = random.sample(range(0,nnodes-1),2)
        receiver = rn[0]
        payer = rn[1]
        print('payer: ', payer, ' receiver: ', receiver)
        mined = await node[receiver].make_Tx(node[payer], str(random.randint(0,100)))
        transacted += 1
        if mined:
            mined_blocks += 1
    print("Transactions Made: ", transacted, " Mined Blocks: ", mined_blocks)

async def storageStats(nnodes):
    for i in range(nnodes):
        print('Node ', i, ' stored ', sys.getsizeof(node[i].storage.data), ' bytes.')

async def main():

    #Introduce Sig Mechanisms
    print("Available Elliptic Curve Signature Algorithms:")
    print("NIST192p, NIST192p, BRAINPOOLP192r1, SECP112r1")
    #Get the parameters
    sig_algorithm = input("Elliptic Curve Signature Algorithm: ")
    nnodes = int(input("Number of Nodes: "))
    ntxs = int(input("Number of Transactions per Block: "))
    nblks = int(input("Number of Blocks: "))
    #Start running the nodes
    await startNodes(nnodes, sig_algorithm, ntxs)
    #Start and run the Blockchain
    await runLedger(nnodes, ntxs, nblks)
    await storageStats(nnodes)

start_time = time.time()
asyncio.run(main())
#Create Geneis Block and save it into the network
#asyncio.run(node[5].publishTransaction(("127.0.0.1",1007),35))
print("Finished in --- %s seconds --- " % (time.time() - start_time))
