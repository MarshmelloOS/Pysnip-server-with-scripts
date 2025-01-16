

def apply_script(protocol, connection, config):

    class blackprotocol(protocol):
        
        def on_map_change(self, map):
            #for x in range(512):
            #    for y in range(220):
            #        map.remove_point(x,y,63) # not 218<y<301 or not 86<x<429 

            for x in range(512):
                for y in range(512):
                    if not map.get_solid(x,y,62) and x<510: map.remove_point(x,y,63) #not 218<y<301 or not 86<x<429 


    return blackprotocol, connection