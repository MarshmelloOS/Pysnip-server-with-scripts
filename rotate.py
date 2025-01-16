from math import cos,sin,pi
from commands import add,admin

theta=90
degrees=True #degrees or radians
clockwise=True #cloakwise or counter-clockwise
always_rotate=False #rotates every map you load

if degrees:
    theta /= 180 / pi
if clockwise:
    theta = ( 2 * pi ) - theta

@admin
def rotatemap(connection,*args): #this will kick everyone
    global theta
    temp=theta
    if args:
        try:
            theta=int(args[0])
        except Exception:
            return "Invalid degrees"
    if len(args)>1:
        theta /= 180 / pi
    if len(args)>2:
        theta = ( 2 * pi ) - theta
    connection.protocol.rotate_map()
    theta=temp
add(rotatemap)
    

def get_new_coord(x,y,z):
    x,y=x-255,y-255
    x2 = x*cos(theta) - y*sin(theta)
    y2 = x*sin(theta) + y*cos(theta)
    return int(x2+255),int(y2+255),z

def apply_script(protocol,connection,config):
    class RotateProtocol(protocol):

        def rotate_map(self):
            map=self.map
            newmap=map.copy()
            print("Rotating map")
            for x in range(512):
                if x%50==0:
                    print(str(x/5)+"% done")
                for y in range(512):
                    for z in range(64):
                        a,b,c=get_new_coord(x,y,z)
                        solid,colour=newmap.get_point(a,b,c)
                        if solid and 0<x<511>y>0<a<511>b>0:
                            map.set_point(x,y,z,colour)
                        else:
                            if z==63:
                                map.set_point(x,y,z,(0,0,0))
                            else:
                                map.remove_point(x,y,z)
            self.map=map

        def on_map_change(self,map):
            if always_rotate:
                self.rotate_map()
            return protocol.on_map_change(self,self.map)
    return RotateProtocol,connection
