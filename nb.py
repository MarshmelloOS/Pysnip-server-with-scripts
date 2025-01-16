from commands import add, admin, name, alias
from twisted.internet.reactor import callLater

# Define the time options for countdown
TIME_OPTIONS = {
    '3s': 3,
    '5s': 5,
    '10s': 10,
    '30s': 30,
    '1m': 60,
    '3m': 180,
    '5m': 300,
    '10m': 600
}

# Function to start the countdown
def start_countdown(protocol, player, time):
    # Check if the time option is valid
    if time in TIME_OPTIONS:
        duration = TIME_OPTIONS[time]
        # Check if the player is an admin
        if player.admin:
            # Start the countdown
            player.send_chat("Countdown started for {}.".format(time))
            if duration <= 5:
                # If duration is less than or equal to 5 seconds, show countdown every second
                for i in range(duration, 0, -1):
                    callLater(duration - i, player.send_chat, str(i))
                callLater(duration, player.send_chat, "Countdown finished!")
            else:
                # If duration is greater than 5 seconds, show stamps every 10 seconds
                for i in range(duration, 0, -10):
                    callLater(duration - i, player.send_chat, "{} seconds left.".format(i))
                callLater(duration, player.send_chat, "Countdown finished!")
        else:
            player.send_chat("You must be an admin to start a countdown.")
    else:
        player.send_chat("Invalid time option.")

# Command to start the countdown
@alias("cn")
@name("countdown")
def countdown(connection, *args):
    if len(args) == 1:
        time = args[0]
        start_countdown(connection.protocol, connection, time)
    else:
        connection.send_chat("Usage: /countdown <time_option>")
add(countdown)
