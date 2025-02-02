"""
Package for interacting on the network at a high level.
"""
import random
import pickle
import asyncio
import logging
from ecdsa import SigningKey, NIST192p

from classicTurm.protocol import KademliaProtocol
from classicTurm.utils import digest
from classicTurm.storage import ForgetfulStorage
from classicTurm.node import Node
from classicTurm.crawling import ValueSpiderCrawl
from classicTurm.crawling import NodeSpiderCrawl
from classicTurm.blockchain import classicTurm

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


# pylint: disable=too-many-instance-attributes
class Server:
    """
    High level view of a node instance.  This is the object that should be
    created to start listening as an active node on the network.
    """

    protocol_class = KademliaProtocol

    def __init__(self, ksize=20, alpha=3, node_id=None, storage=None):
        """
        Create a server instance.  Thi-s will start listening on the given port.

        Args:
            ksize (int): The k parameter from the paper
            alpha (int): The alpha parameter from the paper
            node_id: The id for this node on the network.
            storage: An instance that implements the interface
                     :class:`~kademlia.storage.IStorage`
        """
        #self.signer = oqs.Signature('Falcon-1024')
        #self.verifier = oqs.Signature('Falcon-1024')
        self.ksize = ksize
        self.alpha = alpha
        self.storage = storage or ForgetfulStorage()
        self.node = Node(node_id or digest(random.getrandbits(255)))
        self.transport = None
        self.protocol = None
        self.refresh_loop = None
        self.save_state_loop = None
        #self.pub_key = self.signer.generate_keypair()
        #self.prv_key = self.signer.export_secret_key()
    async def startLedger(self, txperblk):
        self.qled = classicTurm(txperblk)

    async def genECKeys(self, algorithm):
        #algorithm = 'ecdsa.NIST192p'
        self.prv_key = SigningKey.generate(curve=NIST192p)
        self.pub_key = self.prv_key.verifying_key
        print('Signature Keys for node ', self.node.long_id, ' generated')
        print('ECDSA Signature ', self.pub_key)

    def stop(self):
        if self.transport is not None:
            self.transport.close()

        if self.refresh_loop:
            self.refresh_loop.cancel()

        if self.save_state_loop:
            self.save_state_loop.cancel()

    def _create_protocol(self):
        return self.protocol_class(self.node, self.storage, self.ksize, self.pub_key, self.prv_key, self.qled)

    async def listen(self, port, interface='127.0.0.1'):
        """
        Start listening on the given port.

        Provide interface="::" to accept ipv6 address
        """
        loop = asyncio.get_event_loop()
        listen = loop.create_datagram_endpoint(self._create_protocol,
                                               local_addr=(interface, port))
        log.info("Node %i listening on %s:%i",
                 self.node.long_id, interface, port)
        self.node.port = port
        print("Node ", self.node.long_id, " listening")
        self.transport, self.protocol = await listen
        # finally, schedule refreshing table
        #self.node.startCommunication(port)
        self.refresh_table()
        #self.node.sendData(("127.0.0.1", port+1), "Holaaa")

    def refresh_table(self):
        log.debug("Refreshing routing table")
        print("Refreshing routing table...")
        asyncio.ensure_future(self._refresh_table())
        loop = asyncio.get_event_loop()
        self.refresh_loop = loop.call_later(3600, self.refresh_table)

    async def _refresh_table(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        results = []
        for node_id in self.protocol.get_refresh_ids():
            node = Node(node_id)
            nearest = self.protocol.router.find_neighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest,
                                     self.ksize, self.alpha)
            results.append(spider.find())

        # do our crawling
        await asyncio.gather(*results)

        # now republish keys older than one hour
        for dkey, value in self.storage.iter_older_than(3600):
            await self.set_digest(dkey, value)

    def bootstrappable_neighbors(self):
        """
        Get a :class:`list` of (ip, port) :class:`tuple` pairs suitable for
        use as an argument to the bootstrap method.

        The server should have been bootstrapped
        already - this is just a utility for getting some neighbors and then
        storing them if this server is going down for a while.  When it comes
        back up, the list of nodes can be used to bootstrap.
        """
        neighbors = self.protocol.router.find_neighbors(self.node)
        return [tuple(n)[-2:] for n in neighbors]

    async def bootstrap(self, addrs):
        """
        Bootstrap the server by connecting to other known nodes in the network.

        Args:
            addrs: A `list` of (ip, port) `tuple` pairs.  Note that only IP
                   addresses are acceptable - hostnames will cause an error.
        """
        log.debug("Attempting to bootstrap node with %i initial contacts",
                  len(addrs))
        cos = list(map(self.bootstrap_node, addrs))
        gathered = await asyncio.gather(*cos)
        nodes = [node for node in gathered if node is not None]
        spider = NodeSpiderCrawl(self.protocol, self.node, nodes,
                                 self.ksize, self.alpha)
        return await spider.find()

    async def bootstrap_node(self, addr):
        result = await self.protocol.ping(addr, self.node.id)
        return Node(result[1], addr[0], addr[1]) if result[0] else None

    async def get(self, key):
        """
        Get a key if the network has it.

        Returns:
            :class:`None` if not found, the value otherwise.
        """
        log.info("Looking up key %s", key)
        print('Looking for: ', key)
        dkey = digest(key)
        # if this node has it, return it
        if self.storage.get(dkey) is not None:
            return self.storage.get(dkey)
        node = Node(dkey)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to get key %s", key)
            return None
        spider = ValueSpiderCrawl(self.protocol, node, nearest,
                                  self.ksize, self.alpha)
        return await spider.find()

    async def set(self, key, value):
        """
        Set the given string key to the given value in the network.
        """
        if not check_dht_value_type(value):
            raise TypeError(
                "Value must be of type int, float, bool, str, or bytes"
            )
        log.info("setting '%s' = '%s' on network", key, value)
        dkey = digest(key)
        return await self.set_digest(dkey, value)

    async def update_latestBlock(self, key, newkey):
        """
        Update the latest block's key in order for other nodes to easily 
        query the Blockhain's tail (LatestBlock).
        """
        if not check_dht_value_type(value):
            raise TypeError(
                "Value must be of type int, float, bool, str, or bytes"
            )
        log.info("setting '%s' = '%s' on network", key, value)
        dkey = digest(key)
        dvalue = digest(value)
        return await self.update_digest(dkey, value)

    async def set_digest(self, dkey, value):
        """
        Set the given SHA1 digest key (bytes) to the given value in the
        network.
        """
        node = Node(dkey)
        print('Going to store entry', dkey)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to set key %s",
                        dkey.hex())
            return False

        spider = NodeSpiderCrawl(self.protocol, node, nearest,
                                 self.ksize, self.alpha)
        nodes = await spider.find()
        log.info("setting '%s' on %s", dkey.hex(), list(map(str, nodes)))

        # if this node is close too, then store here as well
        biggest = max([n.distance_to(node) for n in nodes])
        if self.node.distance_to(node) < biggest:
            self.storage[dkey] = value
        print('Calling storage on other nodes')
        results = [self.protocol.call_store(n, dkey, value) for n in nodes]
        # return true only if at least one store call succeeded
        return any(await asyncio.gather(*results))

    async def update_digest(self, dkey, value):
        """
        Update the given SHA1 digest key (bytes) to the new value.
        """
        node = Node(dkey)

        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to set key %s",
                                    dkey.hex())
            return False
        spider = NodeSpiderCrawl(self.protocol, node, nearest, 
                                self.ksize, self.alpha)
        nodes = await spider.find()
        log.info("updating '%s' on %s", dkey.hex(), list(map(str, nodes)))

        # if this node is close too, then update here as well
        biggest = max([n.distance_to(node) for n in nodes])
        if self.node.distance_to(node) < biggest:
            content = self.storage.get(dkey)
            self.storage[dvalue] = content
        results = [self.protocol.call_update_entry(n, dkey, dvalue) for n in nodes]
        # return true only if at least one store call succeeded
        return any(await asyncio.gather(*results))

    def save_state(self, fname):
        """
        Save the state of this node (the alpha/ksize/id/immediate neighbors)
        to a cache file with the given fname.
        """
        log.info("Saving state to %s", fname)
        data = {
            'ksize': self.ksize,
            'alpha': self.alpha,
            'id': self.node.id,
            'neighbors': self.bootstrappable_neighbors()
        }
        if not data['neighbors']:
            log.warning("No known neighbors, so not writing to cache.")
            return
        with open(fname, 'wb') as file:
            pickle.dump(data, file)

    @classmethod
    async def load_state(cls, fname, port, interface='0.0.0.0'):
        """
        Load the state of this node (the alpha/ksize/id/immediate neighbors)
        from a cache file with the given fname and then bootstrap the node
        (using the given port/interface to start listening/bootstrapping).
        """
        log.info("Loading state from %s", fname)
        with open(fname, 'rb') as file:
            data = pickle.load(file)
        svr = Server(data['ksize'], data['alpha'], data['id'])
        await svr.listen(port, interface)
        if data['neighbors']:
            await svr.bootstrap(data['neighbors'])
        return svr

    def save_state_regularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.

        Args:
            fname: File name to save retularly to
            frequency: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        self.save_state(fname)
        loop = asyncio.get_event_loop()
        self.save_state_loop = loop.call_later(frequency,
                                               self.save_state_regularly,
                                               fname,
                                               frequency)


    async def Genesis(self):
        """
        Creates Genesis block and saves it in the DHT
        """
        gen = self.qled.createGenesis()
        print('Setting Genesis ', gen)
        return await self.set(gen.get('type'), pickle.dumps(gen))

    async def make_Tx(self, payer, amount):
        """
        Send a Tx to a node for signing, and receive it back.
        """
        tx = self.qled.makeTx(payer.node.long_id, self.node.long_id, amount)
        signed_tx = await self.protocol.call_approveTx(payer,pickle.dumps(tx))
        print('Got result at receiver: ', signed_tx)
        doublesigned_tx = self.qled.signTx(signed_tx[1], self.node.long_id, self.prv_key, self.pub_key)
        print('Tx doublesigned: ', doublesigned_tx)
        print('Transaction signed twice, sending to verify')
        return await self.send_verify_Tx(pickle.dumps(doublesigned_tx))

    async def send_verify_Tx(self, signed_tx):
        tx_hash = digest(pickle.loads(signed_tx).get('hash'))
        print('Digested hash: ', tx_hash)
        node = Node(tx_hash)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbors to this node %s", payer)
            return None
        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        nodes = await spider.find()
        print('Found Nodes: ', nodes)
        verifier = nodes[random.randint(0,len(nodes)-1)]
        print('Verifier node: ', verifier.ip, type(verifier))
        #tuple_verifier = tuple((verifier.ip, verifier.port))
        verified_tx = await self.protocol.call_verifyTx(verifier,signed_tx)
        print('Got Verified Transaction')
        t_saved = await self.set(pickle.loads(verified_tx[1]).get('type'), verified_tx[1])
        if not t_saved:
            return print("Problem at saving tx")
        if len(self.qled.txs) % self.qled.tpb == 0:
            return await self.ask_mine_Blk()
        return False

    async def get_latestBlk(self):
        print('Getting latest Block')
        return await self.get('LastBlock')

    async def update_BlkChain(self, last_block, new_block):
        former_last = self.qled.updateLatestBlk(pickle.loads(last_block))
        up1 = await self.set(former_last.get('type'), pickle.dumps(former_last))
        up2 = await self.set('LastBlock', new_block)
        return up1 & up2

    async def ask_mine_Blk(self):
        """
        Request a batch of transactions to be validated by a peer.
        """
        last_blk = await self.get_latestBlk()
        print('Last Block: ', pickle.loads(last_blk))
        blk_hash = digest(pickle.loads(last_blk).get('hash'))
        node = Node(blk_hash)
        nearest = self.protocol.router.find_neighbors(node)
        if not nearest:
            log.warning("There are no known neighbours to this node %s", payer)
            return None
        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        nodes = await spider.find()
        print('Found Nodes: ', nodes)
        miner = nodes[random.randint(0,len(nodes)-1)]
        print('Miner node: ', miner.ip, type(miner))
        nblk = self.qled.mineBlock(pickle.loads(last_blk))
        mined_blk = await self.protocol.call_povBlk(miner,last_blk, nblk)
        print('Mined Block and last block ', pickle.loads(mined_blk[1]))
        b_saved = await self.update_BlkChain(last_blk, mined_blk[1])
        return b_saved


def check_dht_value_type(value):
    """
    Checks to see if the type of the value is a valid type for
    placing in the dht.
    """
    typeset = [
        int,
        float,
        bool,
        str,
        bytes
    ]
    return type(value) in typeset  # pylint: disable=unidiomatic-typecheck
