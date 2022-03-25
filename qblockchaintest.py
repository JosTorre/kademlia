import oqs
import pickle

tx = [{'timestamp': 1648149447.7371817, 'amount': '56', 'sender': 513119731461101164229439318327648116401531460277, 'receiver': 737709903983592934136023427959808238500948312736}]

ptx = pickle.dumps(tx)

signer = oqs.Signature('Falcon-1024')
pbkey = signer.generate_keypair()
verifier = oqs.Signature('Falcon-1024')

signature = signer.sign(ptx)

print('pbkey type',type(pbkey))

print(signature, type(signature))

print(verifier.verify(ptx, signature, pbkey))
