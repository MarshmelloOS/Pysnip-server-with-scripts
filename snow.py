from pyspades.server import Server
from twisted.internet import task
import random

snowflakes = []

def spawn_snowflakes():
    global snowflakes
    snowflakes = [(random.randint(0, 511), random.randint(0, 511), random.randint(30, 50)) for _ in range(5)]

def update_snowflakes(protocol):
    global snowflakes
    for i in range(len(snowflakes)):
        x, y, z = snowflakes[i]
        z -= 1
        if z <= 0:
            snowflakes[i] = (random.randint(0, 511), random.randint(0, 511), random.randint(30, 50))
        else:
            snowflakes[i] = (x, y, z)
        protocol.send_contained(protocol.build_block(x, y, z, 2))  # 2 represents the snow block ID

def on_chat(connection, message):
    if message == "/snow":
        spawn_snowflakes()

server = Server()

server.on_chat = on_chat

snowfall_task = task.LoopingCall(update_snowflakes, server.protocol)
snowfall_task.start(0.1)

server.run()
