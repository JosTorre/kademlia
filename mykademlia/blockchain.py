# This is used to define the pq blockchain's data structure.
import time
import hashlib
import base64
import json
from ecdsa import SigningKey

# inspired by https://github.com/janfilips/blockchain

class quanTurm():

    def __init__(self):
        self.sha = hashlib.sha3_256()
        self.txs = []
        # Might be the need of starting oqs here to sign and verify.

    def createGenesis(self):
        blk = {
                'type':'Genesis',
                'id':0,
                'timestamp':time.time(),
                'prev_hash':0,
                'hash':self.sha.update(b'Creator:JoseTorre'),
            }
        return blk

    def mineBlock(self, prev_blk):
        blk = {
                'type':'LastBlock',
                'id':int(prev_blk.get('id')) + 1,
                'time':time.time(),
                'prev_hash':prev_blk.get('hash'),
                'txs':self.txs,
                'hash':self.sha.update(self.txs).hexdigest(),
                'povs':'',
                'povk':'',
            }
        return blk

    def makeTx(self, sender, receiver, amount):
        detail = [{
            'timestamp': time.time(),
            'amount':amount,
            'sender':sender,
            'receiver':receiver,
            }]
        tx = {
                'type':'Transaction',
                'detail':detail,
                'hash':self.sha.update(detail).hexdigest(),
                'svk':'',
                'rvk':'',
                'ssig':'',
                'rsig':'',
            }
        self.txs.append(tx)
        return tx

    def signTx(self, tx, signer, ssk, svk):
        trx = tx.get('detail')
        signature = ssk.sign(trx)
        if signer == trx.get('sender'):
            tx['svk'] = svk,
            tx['ssig'] = signature
        elif signer == trx.get('receiver'):
            tx['rvk'} = svk
            tx['rsig'] = signature
        return tx

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
        if lblkverif && hashverif && nhashverif:
            newblk['povs'] = povsig.sign(ntxs)
            newblk['povk'] = povverifk
            return newblk
        else:
            return False



