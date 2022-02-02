import argparse
import logging
import asyncio
import random

from kademlia.network import Server

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
log = logging.getLogger('jt-pqbchord')
log.addHandler(handler)
log.setLevel(logging.DEBUG)

server = Server()


def parse_arguments():
    parser = argparse.ArgumentParser()

    # Optional arguments
    parser.add_argument("-n", "--nodes", help="Number of wanted nodes", type=int, default=5)
    #parser.add_argument("-i", "--ip", help="IP address of existing node", type=str, default=None)
    parser.add_argument("-p", "--port", help="port number of existing node", type=int, default=None)

    return parser.parse_args()


def connect_to_bootstrap_node(port, myport):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(myport))
    bootstrap_node = ('127.0.0.1', port)
    loop.run_until_complete(server.bootstrap([bootstrap_node]))
    print("Listening on ", myport)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


def create_bootstrap_node(port):
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    loop.run_until_complete(server.listen(port))
    print("Listening on ", port)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        loop.close()


def main():
    args = parse_arguments()
    port = 1001
    myport = args.port + 1002
    connect_to_bootstrap_node(port, myport)
    '''
    args = parse_arguments()
    for x in range(args.nodes):
        
        if x == 0:
            port = random.randint(1000,8000)
            create_bootstrap_node(port)
            print("First node up on ", port)
        else: 
            myport = port + x
            connect_to_bootstrap_node(port, myport)
            print(x," node up on ", myport)
    '''


if __name__ == "__main__":
    main()
