from pyspades.server import buildingserver, Protocol, grenade_exploded
from pyspades.common import SColor
from twisted.internet import reactor

class BuildingServer(Protocol):
    def __init__(self, *args, **kwargs):
        Protocol.__init__(self, *args, **kwargs)
        self.balances = {}  # Player balances (crypto currency)
        self.transaction_fee = 0.05  # Fee for each transaction (5%)

    def on_load(self):
        pass

    def on_save(self):
        pass

    def on_block_build(self, x, y, z, mode, player, value):
        # Charge a fee for building blocks
        cost = 1
        if self.can_afford(player, cost):
            self.subtract_balance(player, cost)
            return True

    def on_kill(self, victim, attacker, type, grenade):
        # Reward the attacker for killing a player
        if attacker is not None:
            reward = 2
            self.add_balance(attacker, reward)

    def on_pickup(self, player, pickup_entity):
        # Reward players for picking up items
        if pickup_entity.value == 1:  # Assume PICKUP_NORMAL has a value of 1
            reward = 1
            self.add_balance(player, reward)

    def can_afford(self, player, amount):
        return self.get_balance(player) >= amount

    def get_balance(self, player):
        return self.balances.get(player.name, 0)

    def add_balance(self, player, amount):
        player_name = player.name
        self.balances[player_name] = self.get_balance(player) + amount

    def subtract_balance(self, player, amount):
        player_name = player.name
        current_balance = self.get_balance(player)
        if current_balance >= amount:
            self.balances[player_name] = current_balance - amount
            return True
        else:
            return False

    def on_trade(self, sender, receiver, amount):
        # Implement a basic trading system
        if amount <= 0 or not self.can_afford(sender, amount):
            return False

        # Apply transaction fee
        fee = amount * self.transaction_fee
        amount_after_fee = amount - fee

        if self.subtract_balance(sender, amount):
            self.add_balance(receiver, amount_after_fee)
            return True
        else:
            return False


def apply_building_server_script(protocol, connection, config):
    protocol.grenade_exploded = grenade_exploded
    protocol.apply_script(building_server_script)
    return protocol


if __name__ == "__main__":
    apply_building_server_script(BuildingServer)
    reactor.run()
