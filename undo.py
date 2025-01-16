from pysnip.server import Server, Packet, IP

class UndoRedoServer(Server):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_actions = {}

    def on_command(self, player, command, args):
        if command == "undo":
            self.undo_last_action(player)
        elif command == "redo":
            self.redo_last_action(player)
        else:
            # Handle other commands here
            self.handle_custom_command(player, command, args)

    def handle_custom_command(self, player, command, args):
        # Replace this with your actual logic for handling custom commands
        # For demonstration purposes, let's print a message.
        print("{} executed {} command with arguments: {}".format(player.name, command, args))
        self.add_player_action(player, (command, args))

    def add_player_action(self, player, action):
        if player not in self.player_actions:
            self.player_actions[player] = []
        self.player_actions[player].append(action)

    def undo_last_action(self, player):
        if player in self.player_actions and self.player_actions[player]:
            action = self.player_actions[player].pop()
            self.undo_action(player, action)
            print("Undid last action for {}".format(player.name))
        else:
            print("No actions to undo for {}".format(player.name))

    def redo_last_action(self, player):
        # Implement redo logic similar to undo logic based on your needs
        # You'll need to store the undone actions separately and redo them when requested.
        pass

    def undo_action(self, player, action):
        # Replace this with your actual logic for undoing commands
        # For demonstration purposes, let's print a message.
        command, args = action
        print("Undoing {} command for {}".format(command, player.name))

if __name__ == "__main__":
    server = UndoRedoServer((IP(""), 32887))
    server.run()
