import asyncio
import logging
import pickle
import random
import time
import json
import sys
import oqs
import os
import psutil 
from pprint import pprint

from mykademlia.network import Server
from mykademlia.blockchain import quanTurm


async def startNodes(nnodes, algorithm, txperblk):
    global node
    node = []
    for i in range(nnodes):
        node.append(Server())
        print("Created node: ", node[i].node.long_id)
        port = 1000 + i
        await node[i].genQKeys(algorithm)
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
    global mined_blocks
    global transacted
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
    print('\n')
    print("Transactions Made: ", transacted, " Mined Blocks: ", mined_blocks)

async def generalStats(nnodes):
    
    startqtime = time.time()
    lastBlk = await node[1].get_latestBlk()
    querytime = time.time() - startqtime
    lastBlk = pickle.loads(lastBlk)
    sometxs = lastBlk.get('txs')
    sometx = await node[1].get(sometxs[1])
    sometx = pickle.loads(sometx)
    print('Last Block: ', lastBlk)
    print('Some Transaction: ', sometx, '\n\n\n')
    print('\n--- Output Stats ---\n')
    print('Block size: ', sys.getsizeof(lastBlk))
    print('Block size (encoded): ', sys.getsizeof(pickle.dumps(lastBlk)))
    print('Transaction size: ', sys.getsizeof(sometx))
    print('Transaction size (encoded): ', sys.getsizeof(pickle.dumps(sometx)))
    print('Used memory space per node: \n')
    for i in range(nnodes):
        print('Node ', i, ' stored ', sys.getsizeof(node[i].storage.data), ' bytes.')
    print('\n')
    print('\n--- System Stats ---\n')
    print('CPU usage of ', psutil.cpu_percent(),'%')
    print('RAM usage of ', psutil.virtual_memory().percent,'%')
    print('RAM stats: ', psutil.virtual_memory())
    print('\n--- Time Stats ---\n')
    print('Query speed of %s seconds'% (querytime/10))
    

async def main():

    #Introduce Sig Mechanisms
    sigs = oqs.get_enabled_sig_mechanisms()
    print('Available Post-Quantum Secure Signature Schemes:\n')
    pprint(sigs, compact='True')
    #Get the parameters
    sig_algorithm = input("Post-quantum Signature Algorithm: ")
    nnodes = int(input("Number of Nodes: "))
    ntxs = int(input("Number of Transactions per Block: "))
    nblks = int(input("Number of Blocks: "))
    #Start running the nodes
    start_time = time.time()
    await startNodes(nnodes, sig_algorithm, ntxs)
    tfinalstartnodes = time.time() - start_time
    #Start and run the Blockchain
    await runLedger(nnodes, ntxs, nblks)
    global finland_time
    finland_time = time.time()
    await generalStats(nnodes)
    print('Time to Start nodes and Gen Keys: ', tfinalstartnodes/10)
    ttime = ((finland_time - start_time)/10)
    print("FINISHED in --- %s seconds --- " % ttime)
    print("Mean time per transaction --- %s seconds --- " % (ttime/float(transacted)))
    print("Block latency of --- %s seconds --- per block" % (ttime/float(mined_blocks)))

def printIntro():
    with  open('mykademlia/init.txt', 'r') as f:
        for line in f:
            print(line)

os.system('clear')
printIntro()
asyncio.run(main())
printIntro()
