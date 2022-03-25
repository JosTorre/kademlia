import asyncio
import logging
import pickle
import random
import time
import json
from mykademlia.network import Server
from mykademlia.blockchain import quanTurm

async def startNodes(nnodes, algorithm):
    global node
    node = []
    for i in range(nnodes):
        node.append(Server())
        print("Created node: ", node[i].node.long_id)
        port = 1000 + i
        node[i].genQKeys(algorithm)
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

async def runLedger(nnodes, ntxs, nblks):
    qLed = quanTurm()
    #Create and add Genesis Block
    gen = qLed.createGenesis()
    print("Genesis: ", json.dumps(gen, sort_keys=False, indent=4))
    await node[1].set(gen.get('type'),pickle.dumps(gen))
    #Make transactions and mine blocks
    for b in range(nblks):
        for n in range(ntxs):
            receiver = random.randint(0,nnodes-1)
            sender = random.randint(0,nnodes-1)
            print('sender: ', sender, ' receiver: ', receiver )
            tx = qLed.makeTx(node[sender].node.long_id, node[receiver].node.long_id, str(random.randint(0,100)))
            #print('Transaction ', n,' : ', json.dumps(tx, sort_keys=False, indent=4))
            #await node[receiver].bootstrap([(node[sender].node.ip, node[sender].node.port)])
            print('Going to send transaction to sender node', node[sender].node.ip, node[sender].node.port)
            signed_tx = await node[receiver].send_sign_Tx(node[sender], pickle.dumps(tx))
            #print('Transaction received signed: ', signed_tx)
            print('going to insert!!!')
            print('SSS',pickle.dumps(signed_tx))
            await node[receiver].set(tx.get('type'),pickle.dumps(signed_tx))
        #Get former Block
        if b == 0:
            lblk = await node[receiver].get('Genesis')
            lblk = pickle.loads(lblk)
        else:
            lblk = await node[receiver].get('LastBlock')
            lblk = pickle.loads(lblk)
        #print('Retrieved last Block: ', json.dumps(lblk, sort_keys=False, indent=4))
        blk1 = qLed.mineBlock(lblk)
        #MISSING Modify former block and save in DHT
        await node[receiver].set(blk1.get('type'),pickle.dumps(blk1))
        #print('Block: ', b,' : ', json.dumps(blk1, sort_keys=False, indent=4))

async def main():

    #Get the parameters
    sig_algorithm = input("Post-quantum Signature Algorithm: ")
    nnodes = int(input("Number of Nodes: "))
    ntxs = int(input("Number of Transactions per Block: "))
    nblks = int(input("Number of Blocks: "))
    #Start running the nodes
    await startNodes(nnodes, sig_algorithm)
    #Start and run the Blockchain
    await runLedger(nnodes, ntxs, nblks) 

start_time = time.time()
asyncio.run(main())
#Create Geneis Block and save it into the network
#asyncio.run(node[5].publishTransaction(("127.0.0.1",1007),35))
print("Finished in --- %s seconds --- " % (time.time() - start_time))
