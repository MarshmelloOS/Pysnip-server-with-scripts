#Auto Save Map By Kuma
#Automatically saves the current map in the maps folder
#Some functions are copied and edited from mat^2's savemap.py
#Version 1

from time import strftime, localtime
from twisted.internet.task import LoopingCall
from twisted.internet.reactor import callLater

save_time_min = 1 #Saves the map every X minutes. (Set to 30 by default)
save_time_sec = save_time_min * 60.0 #Don't touch this.

def get_name(map):
    return './maps/{}.vxl'.format(map.rot_info.name)

def apply_script(protocol, connection, config):
    class AutoMapSaveProtocol(protocol):
        def __init__(self, *arg, **kwargs):
            protocol.__init__(self, *arg, **kwargs)
            self.save_loop = LoopingCall(self.save_map)
            callLater(save_time_sec, self.start_save_loop) #To prevent the loop from saving the map at the start.

        def start_save_loop(self, time = save_time_sec):
            self.save_loop.start(time)

        def save_map(self):
            open(get_name(self.map_info), 'wb').write(self.map.generate())

    return AutoMapSaveProtocol, connection 

        
