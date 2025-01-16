"""
thepolm3
THE END IS NIGH
"""

def invertColour(colour):
    r,g,b = colour
    return (255-r,255-g,255-b)

def apply_script(protocol,connection,config):
    class InverterProtocol(protocol):
        def on_map_change(self,map):
            oldmap = map.copy()
            print("Map flipping in process...")
            for x in range(512):
                if x%50==0:
                    print(str(x/5)+"% done")
                for y in range(512):
                    colour = invertColour(map.get_color(x,y,map.get_z(x,y)))
                    for z in range(63):
                        solid = oldmap.get_solid(x,y,z)
                        if solid:
                            map.remove_point(x,y,63-z)
                        else:
                            map.set_point(x,y,63-z,colour)
            print("Map flipping complete.")
            return protocol.on_map_change(self,map)
    return InverterProtocol,connection
