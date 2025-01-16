from pyspades.server import connection
import json
import time
import os

# Rate of coins earned per second
COIN_RATE = 0.05  # Adjust as needed

def calculate_coins(time_spent):
    return time_spent * COIN_RATE

def get_time():
    return int(time.time())

def coins(connection, *args):
    if isinstance(connection, CryptoConnection):
        current_time = get_time()
        time_since_last_update = current_time - connection.last_login_time
        earned_coins = calculate_coins(time_since_last_update)
        connection.balance += earned_coins
        connection.last_login_time = current_time
        connection.send_chat("You have {} coins. Keep playing to earn more!".format(round(connection.balance, 2)))
    else:
        connection.send_chat("Coins feature is not available for this connection type.")

# Define the CryptoConnection class
class CryptoConnection(connection):
    balance = 0

    def on_login(self, name):
        current_time = get_time()
        time_since_last_update = current_time - self.last_login_time
        earned_coins = calculate_coins(time_since_last_update)
        self.balance += earned_coins
        self.last_login_time = current_time
        player_data_file = os.path.join(os.path.expanduser("~"), "Videos", "OpenSpades+MyServer", "OpenSpades-0.1.3-Windows", "Resources", "player_data.json")
        with open(player_data_file, 'r+') as f:
            data = json.load(f)
            if name not in data:
                self.send_chat("You have 0 coins in your balance. Register to gain coins every time you log in!")
        return connection.on_login(self, name)

def apply_script(protocol, connection, config):
    return protocol, CryptoConnection
