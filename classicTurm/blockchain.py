# This is used to define the pq blockchain's data structure.
import time
import hashlib
import base64
import json
import pickle
#from ecdsa import SigningKey
from ecdsa import SigningKey, VerifyingKey, NIST192p

# inspired by https://github.com/janfilips/blockchain

class classicTurm():
    
    #This method initializes the parameters used per node to create the Blockchain.
    def __init__(self, tpb):
        self.tx_counter = 0
        self.txs = []
        self.tpb = tpb
        self.balance = 1000
        # Might be the need of starting oqs here to sign and verify.
        #self.signer = oqs.Signature('Falcon-1024')
        #self.verifier = oqs.Signature('Falcon-1024')
    
    #This method creates the Genesis Block in form of a dictionary.
    def createGenesis(self):
        gen = {
                'type':'LastBlock',
                'id':0,
                'timestamp':time.time(),
                'prev_hash':0,
                'hash':hashlib.sha256(b'Creator:JoseTorre').hexdigest(),
            }
        return gen
    
    #This method takes the previous block and returns the next block.
    def mineBlock(self, prev_blk):
        ltxs = pickle.dumps(self.txs)
        blk = {
                'type':'LastBlock',
                'id':int(prev_blk.get('id')) + 1,
                'time':time.time(),
                'prev_hash':prev_blk.get('hash'),
                'txs':self.txs,
                'hash':hashlib.sha256(ltxs).hexdigest(),
                'povs':'',
                'povk':'',
            }
        self.txs = []
        return pickle.dumps(blk)
    
    #This method updates the blockchain tail block and returns a normal block.
    def updateLatestBlk(self, lastBlk):
        lastBlk['type'] = 'Blk' + str(lastBlk.get('id'))
        return lastBlk

    #Creates a Transaction in form of a dictionary from the given parameters.
    def makeTx(self, sender, receiver, amount):
        detail = {
            'timestamp': time.time(),
            'amount':amount,
            'sender':sender,
            'receiver':receiver,
            }
        ndetail = pickle.dumps(detail)
        tx = {
                'type':'Tx' + '_' + str(receiver) + '_' + str(self.tx_counter),
                'detail':detail,
                'hash':hashlib.sha256(ndetail).hexdigest(),
                'svk':'',
                'rvk':'',
                'ssig':'',
                'rsig':'',
            }
        self.txs.append(tx.get('type'))
        self.tx_counter += 1
        return tx
    
    #Adds the signature of the sender or receiver to the transaction.
    def signTx(self, tx, signerid, prv_key, signer_pubk):
        print('Approving: ', tx, ' Depickled: ', pickle.loads(tx))
        tx = pickle.loads(tx)
        print('Approving2: ', tx)
        trx = tx.get('detail')
        txhash = tx.get('hash')
        signature = prv_key.sign(pickle.dumps(txhash))
        if signerid == trx.get('sender'):
            tx['svk'] = signer_pubk.to_string()
            tx['ssig'] = signature
        elif signerid == trx.get('receiver'):
            tx['rvk'] = signer_pubk.to_string()
            tx['rsig'] = signature
        else:
            return print("Neither signer or receiver id, given: ", signerid," expecter=d: ", trx.get('sender'))
        print('Approved: ', tx)
        return tx

    #Verifies if the sender and receiver signatures are correct and checks the hash.
    def verifyTx(self, tx, sigfk, verifk):
        tx = pickle.loads(tx)
        print("Transaction to Verify: ", tx)
        print("Verifier keys: ", sigfk, verifk)
        #print('Transaction: ', tx)
        #Get data from transaction
        rsig = tx.get('rsig')
        rvk = tx.get('rvk')
        rvk = VerifyingKey.from_string(rvk, curve=NIST192p)
        ssig = tx.get('ssig')
        svk = tx.get('svk')
        svk = VerifyingKey.from_string(svk, curve=NIST192p)
        trx = tx.get('detail')
        txhash = tx.get('hash')
        ndetail = pickle.dumps(trx)
        #print('receiver sig: ', rsig)
        #print('receiver key: ', rvk)
        #Verify hash
        if txhash == hashlib.sha256(ndetail).hexdigest():
            hasha = True
        else:
            hasha = False
        #Verify signatures
        v1 = rvk.verify(rsig, pickle.dumps(txhash))
        v2 = svk.verify(ssig, pickle.dumps(txhash))
        #If correct, pov
        if v1 & v2 & hasha: 
            # Add verifyer signature
            tx['povs'] = sigfk.sign(pickle.dumps(txhash))
            tx['povk'] = verifk.to_string()
            return tx
        else:
            return False

    #Verifies a block taking the last and new block, checking signatures and hashes; returnes signed new block.
    def povBlk(self, lastblk, newblk, povsig, povverif):
        lastblk = pickle.loads(lastblk)
        newblk = pickle.loads(newblk)
        #Get data from both blocks
        lhash = lastblk.get('hash')
        ltxs = lastblk.get('txs')
        nprevhash = newblk.get('prev_hash')
        nhash = newblk.get('hash')
        ntxs = newblk.get('txs')
        lpovs = lastblk.get('povs')
        lpovk = lastblk.get('povk')
        #Check if genesis
        if lastblk['id'] == 0:
            verif = hashlib.sha256(b'Creator:JoseTorre').hexdigest() == lhash
            print('Verified Genesis: ', verif, lhash)
        else:
            lpovk = VerifyingKey.from_string(lpovk, curve=NIST192p)
            lblkverif = lpovk.verify(lpovs, pickle.dumps(lhash))
            hashverif = lhash == nprevhash
            nhashverif = nhash == hashlib.sha256(pickle.dumps(ntxs)).hexdigest()
            verif = lblkverif & hashverif & nhashverif 
        if verif:
            newblk['povs'] = povsig.sign(pickle.dumps(nhash))
            newblk['povk'] = povverif.to_string()
            return newblk
        else:
            return False



