import asyncio
from kademlia.network import Server

async def runNetwork():
    node = Server()
    await node.listen(5678)
    node2 = Server()
    await node.listen(5660)
    await node.bootstrap([("127.0.0.1", 5660)])
    print("Made node ", node)
    print("Made node 2 ", node2)
    value = input("Write value to store: ")
    await node.set("my-key", value)
    print("Setting value")
    result = await node.get("my-key")
    print(result)



asyncio.run(runNetwork())
