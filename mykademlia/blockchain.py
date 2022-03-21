# This is used to define the pq blockchain's data structure.
import time
import hashlib
import base64
import json
#from ecdsa import SigningKey
import oqs

# inspired by https://github.com/janfilips/blockchain

class quanTurm():
    
    #This method initializes the parameters used per node to create the Blockchain.
    def __init__(self):
        self.sha = hashlib.sha3_256()
        self.txs = []
        # Might be the need of starting oqs here to sign and verify.
        #self.signer = oqs.Signature('Falcon-1024')
        #self.verifier = oqs.Signature('Falcon-1024')
    
    #This method creates the Genesis Block in form of a dictionary.
    def createGenesis(self):
        self.sha.update(b'Creator:JoseTorre')
        gen = {
                'type':'Genesis',
                'id':0,
                'timestamp':time.time(),
                'prev_hash':0,
                'hash':self.sha.hexdigest(),
            }
        return gen
    
    #This method takes the previous block and returns the next block.
    def mineBlock(self, prev_blk):
        ltxs = json.dumps(self.txs).encode('utf-8')
        self.sha.update(ltxs)
        blk = {
                'type':'LastBlock',
                'id':int(prev_blk.get('id')) + 1,
                'time':time.time(),
                'prev_hash':prev_blk.get('hash'),
                'txs':self.txs,
                'hash':self.sha.hexdigest(),
                'povs':'',
                'povk':'',
            }
        self.txs = []
        return blk
    
    #This method updates the blockchain tail block and returns a normal block.
    def updateLatestBlk(self, lastBlk):
        lastBlk['type'] = 'Blk' + str(lastBlk.get('id'))
        return lastBlk

    #Creates a Transaction in form of a dictionary from the given parameters.
    def makeTx(self, sender, receiver, amount):
        detail = [{
            'timestamp': time.time(),
            'amount':amount,
            'sender':sender,
            'receiver':receiver,
            }]
        ndetail = json.dumps(detail).encode('utf-8')
        self.sha.update(ndetail)
        tx = {
                'type':'Tx' + str(len(self.txs)),
                'detail':detail,
                'hash':self.sha.hexdigest(),
                'svk':'',
                'rvk':'',
                'ssig':'',
                'rsig':'',
            }
        self.txs.append(tx)
        return tx
    
    #Adds the signature of the sender or receiver to the transaction.
    def signTx(self, tx, signer, ssk, svk):
        trx = tx.get('detail')
        signature = ssk.sign(trx)
        if signer == trx.get('sender'):
            tx['svk'] = svk,
            tx['ssig'] = signature
        elif signer == trx.get('receiver'):
            tx['rvk'] = svk
            tx['rsig'] = signature
        return tx

    #Verifies if the sender and receiver signatures are correct and checks the hash.
    def verifyTx(self, tx, verifk, sigfk):
        #Get data from transaction
        rsig = tx.get('rsig')
        rvk = tx.get('rvk')
        ssig = tx.get('ssig')
        svk = tx.get('svk')
        trx = tx.get('detail')
        txhash = tx.get('hash')
        #Verify hash
        if txhash == self.sha.update(trx).hexdigest():
            hasha = True
        else:
            hasha = False
        #Verify signatures
        v1 = verifk.verify(trx, rsig, rvk)
        v2 = verifk.verify(trx, ssig, svk)
        #If correct, pov
        if v1 & v2 & hasha: 
            # Add verifyer signature
            tx['povs'] = sigfk.sign(tx)
            tx['povk'] = verifk
            return tx
        else:
            return False

    #Verifies a block taking the last and new block, checking signatures and hashes; returnes signed new block.
    def povBlk(self, lastblk, newblk, povsig, povverifk):
        #Get data from both blocks
        lhash = lastblk.get('hash')
        ltxs = lastblk.get('txs')
        nprevhash = newblk.get('prev_hash')
        nhash = newblk.get('hash')
        ntxs = newblk.get('txs')
        lpovs = newblk.get('povs')
        lpovk = newblk.get('povk')
        #Validations
        lblkverif = verifier.verify(ltxs, lpovs, lpovk)
        hashverif = lhash == nprevhash
        nhashverif = nhash == self.sha.update(ntxs).hexdigest()
        if lblkverif & hashverif & nhashverif:
            newblk['povs'] = povsig.sign(ntxs)
            newblk['povk'] = povverifk
            return newblk
        else:
            return False



