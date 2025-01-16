#No Empty Chat by Kuma

NO_WHITESPACE = "Your message cannot be empty."

def apply_script(protocol, connection, config):

    class chatConnection(connection):
        def on_chat(self, value, global_message):
            if value.isspace():
                self.send_chat(NO_WHITESPACE)
                return False
            return connection.on_chat(self, value, global_message)
    return protocol, chatConnection
