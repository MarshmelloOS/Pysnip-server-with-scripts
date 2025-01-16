"""
switches to arena for an arena map, for example
thepolm3
"""
from random import randint

def get_map_extensions(map):
    extensions = {}
    try:
        f = open("maps/"+str(map)+".txt")
        exec(f.read())
        f.close()
    except Exception, e:
        print(e)
    return extensions

def apply_script(protocol,connection,config):

        class MatchModeProtocol(protocol):
            oldmode = None

            def on_mode_advance(self,mode,map):
                extensions = get_map_extensions(map)
                if extensions:
                    game_modes = config.get("game_modes",[])
                    modes = []
                    for extension in extensions:
                        if extension.lower() == "game_mode":
                            if type(extensions[extension])==list:
                                modes = extensions[extension]
                            else:
                                return extensions["game_mode"]
                        elif extension.lower() in game_modes:
                            if extensions[extension.lower()]:
                                modes.append(extension)
                    if modes:
                        return modes[randint(0,len(modes)-1)]
                if "on_mode_advance" in dir(protocol):
                    returned = protocol.on_mode_advance(self,mode,map)
                    if returned:
                        return returned
                if self.oldmode:
                    returned = self.oldmode
                    self.oldmode = None
                    return returned
        return MatchModeProtocol,connection
