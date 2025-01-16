"""
colourbyheight by thepolm3

to input colour code:
use this format;
"""
#### n : R , G , B / n : R , G , B / n : R , G , B ####
"""
where n is height, r is red, g is green and b is blue

to make a layer transparent do from one colour to the same colour,
so for example putting
40:0,40,91/50:0,40,91
at the end of your line would make heights 40-50 the original colour.
"""
#examples:
#simple back and white heightmap:
bw="1:0,0,0/63:255,255,255"
#RGB colours heightmap
rgb="1:0,0,0/10:255,0,0/20:0,255,0/30:0,0,255/40:255,0,255/50:0,255,255/60:255,255,0/63:255,255,255"
#earthy heightmap
earth="0:0,0,128/1:0,92,9/10:1,166,17/30:186,159,167/50:255,255,255/63:255,255,255"

#feel free to change this
default=earth

from random import randint
def apply_script(p,c,config):
    class ColourByHeightProtocol(p):
        def on_map_change(self,map):

            try:
                print("Please insert the colour code")
                colourcode=raw_input("")
                colourcode=colourcode.split("/")
                for i in range(len(colourcode)):
                    colourcode[i]=colourcode[i].split(":")
                    colourcode[i][0]=int(colourcode[i][0])
                    colourcode[i][1]=colourcode[i][1].split(",")
                    colourcode[i][1][0]=int(colourcode[i][1][0])
                    colourcode[i][1][1]=int(colourcode[i][1][1])
                    colourcode[i][1][2]=int(colourcode[i][1][2])
                print("Corret colour code")
            except Exception:
                print("Invalid colour code, reverting to default")
                colourcode=default
                colourcode=colourcode.split("/")
                for i in range(len(colourcode)):
                    colourcode[i]=colourcode[i].split(":")
                    colourcode[i][0]=int(colourcode[i][0])
                    colourcode[i][1]=colourcode[i][1].split(",")
                    colourcode[i][1][0]=int(colourcode[i][1][0])
                    colourcode[i][1][1]=int(colourcode[i][1][1])
                    colourcode[i][1][2]=int(colourcode[i][1][2])

            colourcode=sorted(colourcode)
            fullheight=[None]*64
            
            for code in colourcode:
                fullheight[code[0]]=(code[1][0],code[1][1],code[1][2])

            storedindex=0
            rstep=0
            gstep=0
            bstep=0
            if not fullheight[63]:
                fullheight[63]=(code[1][0],code[1][1],code[1][2])

            for height in range(len(fullheight)):
                colour=fullheight[height]
                if colour:
                    storedindex=height
                    for i in range(height+1,64):
                        if fullheight[i]:
                            break
                    if i==64:
                        height=64
                        break
                    rstep=float((colour[0]-fullheight[i][0]))/((i-height) or 1)
                    gstep=float((colour[1]-fullheight[i][1]))/((i-height) or 1)
                    bstep=float((colour[2]-fullheight[i][2]))/((i-height) or 1)
                else:
                    if rstep or gstep or bstep:
                        count=height-storedindex
                        basecol=fullheight[storedindex]
                        fullheight[height]=(basecol[0]-rstep*count,basecol[1]-gstep*count,basecol[2]-bstep*count)

            fullheight=fullheight[::-1]

            for x in range(512):
                if x%50==0:
                    print("%s generated (%s blocks)" %(str(x/5)+"%",str(float(512*63*x)/1000)+" thousand"))
                for y in range(512):
                    for z in range(64):
                        if map.get_solid(x,y,z):
                            if fullheight[z]:
                                r,g,b=fullheight[z]
                                map.set_point(x,y,z,(r,g,b))
            
            return p.on_map_change(self,map)
    return ColourByHeightProtocol,c
