import os

# Function to set spawn position for a player
def set_spawn(player_name, x, y, z):
    spawn_data = "{},{},{}".format(x, y, z)
    if not os.path.exists("spawns"):
        os.makedirs("spawns")
    with open("spawns/{}.txt".format(player_name), "w") as file:
        file.write(spawn_data)
    print("Spawn position set for {}: ({}, {}, {})".format(player_name, x, y, z))

# Function to get spawn position for a player
def get_spawn(player_name):
    spawn_file = "spawns/{}.txt".format(player_name)
    if os.path.exists(spawn_file):
        with open(spawn_file, "r") as file:
            spawn_data = file.read().split(",")
            spawn_pos = tuple(map(int, spawn_data))
            return spawn_pos
    else:
        print("No spawn position set for {}.".format(player_name))
        return None

# Example usage:
# Assuming a player named "example_player" with coordinates (100, 100, 10)
# To set spawn:
set_spawn("example_player", 100, 100, 10)

# To get spawn:
spawn_position = get_spawn("example_player")
if spawn_position:
    print("Spawn position for example_player: {}".format(spawn_position))
