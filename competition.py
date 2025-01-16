from pyspades.constants import BUILD_BLOCK

BUILD_COMPETITION_TIME = 300  # Time in seconds for the building competition

class BuildCompetition:
    def __init__(self, protocol):
        self.protocol = protocol
        self.builders = set()
        self.building_time_remaining = BUILD_COMPETITION_TIME

    def start_competition(self):
        self.protocol.send_chat("Building competition has started! Get ready to build!")
        self.protocol.send_chat("Submit your build with /submitbuild command.")
        self.protocol.set_timer(1, self.update_timer)

    def end_competition(self):
        self.protocol.send_chat("Building competition has ended! No more building.")
        self.protocol.clear_timer(1)
        self.evaluate_builds()

    def update_timer(self):
        self.building_time_remaining -= 1
        if self.building_time_remaining <= 0:
            self.end_competition()
        else:
            self.protocol.set_timer(1, self.update_timer, delay=1)

    def on_block_build(self, x, y, z, block, previous_value):
        if self.building_time_remaining > 0:
            player = self.protocol.players.get(self.protocol.get_picked_entity())
            if player:
                self.builders.add(player)

    def evaluate_builds(self):
        self.protocol.send_chat("Evaluating builds...")
        if not self.builders:
            self.protocol.send_chat("No builds to evaluate.")
            return

        # Implement your logic to evaluate and reward builds here
        # For simplicity, let's just announce the winners
        self.protocol.send_chat("Building competition winners:")
        for i, builder in enumerate(self.builders):
            self.protocol.send_chat("{}. {}".format(i + 1, builder.name))

    def on_chat_message(self, player, message):
        if message.lower() == "/startbuildcompetition" and player.admin:
            self.start_competition()
        elif message.lower() == "/submitbuild" and player in self.builders:
            self.protocol.send_chat("{} has submitted their build!".format(player.name))

def apply_script(protocol, connection, config):
    build_competition_instance = BuildCompetition(protocol)

    class BuildCompetitionConnection(connection):
        def on_block_build(self, x, y, z, block, previous_value):
            build_competition_instance.on_block_build(x, y, z, block, previous_value)

        def on_chat_message(self, message):
            build_competition_instance.on_chat_message(self, message)
            return connection.on_chat_message(self, message)

    return build_competition_instance, BuildCompetitionConnection
