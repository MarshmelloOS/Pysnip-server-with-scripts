#Script by Kuma
#Colours stolen from polm's worldedit script (edited)
#Also a line of code was copied from dynfog.py (edited)

from commands import add, admin, name

colours={
    "black":(0,0,0),"white":(255,255,255),"grey":(127,127,127),"red":(255,0,0),
    "lime":(0,255,0),"blue":(0,0,255),"yellow":(255,255,0),"magneta":(255,0,255),
    "cyan":(0,255,255),"orange":(255,165,0),"pink":(255,130,108),"violet":(148,0,211),
    "purple":(155,48,255),"indigo":(75,0,130),"orchid":(218,112,214),"lavender":(230,230,250),
    "navy":(0,0,127),"peacock":(51,161,201),"azure":(240,255,255),"aqua":(0,238,238),
    "turquoise":(64,224,208),"teal":(56,142,142),"aquamarine":(127,255,212),"emerald":(0,201,87),
    "sea":(84,255,159),"cobalt":(61,145,64),"mint":(189,252,201),"palegreen":(152,251,152),
    "forest":(34,139,34),"green":(0,128,0),"grass":(124,252,0),"chartreuse":(127,255,0),
    "olive":(142,142,56),"ivory":(238,238,224),"beige":(245,245,220),"khaki":(240,230,140),
    "banana":(227,207,87),"gold":(201,137,16),"goldenrod":(218,165,32),"lace":(253,245,230),
    "wheat":(245,222,179),"moccasin":(255,222,173),"papaya":(255,239,213),"eggshell":(252,230,201),
    "tan":(210,180,140),"brick":(178,34,34),"skin":(255,211,155),"melon":(227,168,105),
    "carrot":(237,145,33),"peru":(205,133,63),"linen":(250,240,230),"peach":(238,203,173),
    "chocolate":(139,69,19),"sienna":(160,82,45),"coral":(255,127,80),"sepia":(94,38,18),
    "salmon":(198,113,113),"tomato":(205,55,0),"snow":(255,250,250),"brown":(165,42,42),
    "maroon":(128,0,0),"beet":(142,56,142),"gray":(91,91,91),"crimson":(220,20,60),
    "dew":(240,255,240),"dirt":(71,48,35),"bronze":(150,90,56),"wood":(193,154,107),
    "silver":(168,168,168),"lava":(205,53,39),"oakwood":(115,81,58),"redwood":(165,42,42),
    "sand":(244,164,96),"chestnut":(149,69,53),"russet":(128,70,27),"cream":(255,253,208),
    "sky":(135,206,235),"water":(65,105,225),"smoke":(245,245,245), "classic":(128, 232, 255)
}

default_server_fog = (128, 232, 255)

@name('cfog')
@admin
def name_fog(connection, name = None):
    if name is not None:
        name = str(name.lower())
        if name in colours:
            connection.protocol.set_fog_color(colours.get(name))
            return "Fog set to %s" % name
        else:
            return "Colour not present in the database"
    else:
        connection.protocol.set_fog_color(getattr(connection.protocol.map_info.info, 'fog', default_server_fog))
        return "Fog set to default map/server value"        

add(name_fog)

def apply_script(protocol, connection, config):
    return protocol, connection
