from random import randint, choice
from commands import add, admin, alias


watercolors = [(0,0,0), (255,0,0), (0,255,0), (0,0,255), (255,255,0), (0,255,255), (255,255,255), (255,0,255), (125,0,125)]


@alias('wc')
@admin
def watercolor(self, r, g, b, *offset):
    self.protocol.watercolor_r = int(r)
    self.protocol.watercolor_g = int(g)
    self.protocol.watercolor_b = int(b)
    if offset: self.protocol.watercolor_offset = int(offset[0])
    if not self.protocol.watercolor_enabled: self.protocol.watercolor_teams = True
    return 'Done. Meow'
add(watercolor)

@alias('wco')
@admin
def watercoloroffset(self, value):
    if int(value) < 0: return 'Come on boy, you should know that a positive value would be for the best for both of us.'
    else:
        self.protocol.watercolor_offset = int(value)
        return 'Offset value set to %i.' % int(value)
add(watercoloroffset)
        
@alias('twc')
@admin
def togglewatercolor(self):
    self.protocol.watercolor_enabled = not self.protocol.watercolor_enabled
    if self.protocol.watercolor_enabled: return 'Watercolors will be modified.'
    else: return 'Watercolors return to their original values.'
add(togglewatercolor)

@alias('wct')
@admin
def watercolorteams(self):
    self.protocol.watercolor_teams = not self.protocol.watercolor_teams
    if self.protocol.watercolor_teams: return "Watercolors will be changed to the winning team's color."
    else: return "Alright, watercolors will not be affected by the winning team's color."
add(watercolorteams) 

@alias('wcr')
@admin
def watercolorrandom(self):
    self.protocol.watercolor_randomized = not self.protocol.watercolor_randomized
    if self.protocol.watercolor_randomized: return "Watercolors will be randomly chosen."
    else: return "Watercolors will be set manually." 
add(watercolorrandom)

@alias('wcp')
@admin
def watercolorprevent(self):
    self.protocol.watercolor_prevent = not self.protocol.watercolor_prevent
    if self.protocol.watercolor_prevent: 
        self.protocol.watercolor_enabled = False
        return "Watercolor changes will be deactivated after each map change."
    else: 
        self.protocol.watercolor_enabled = True
        return "Watercolor changes will be applied again."
add(watercolorprevent)

@alias('wcm')
@admin
def watercolormap(self):
    self.protocol.watercolor_map = not self.protocol.watercolor_map
    if self.protocol.watercolor_map: return "Map extensions may influence watercolors again."
    else: return "Watercolors will not be affected by map extensions."
add(watercolormap)

@alias('wcmd')
@admin
def watercolorcommands(self):
    return "/watercolor <R><G><B> [offset] | /watercoloroffset <value> | /togglewatercolor /watercolorteams /watercolorrandom /watercolorprevent /watercolormap"
add(watercolorcommands)


def apply_script(protocol, connection, config):


    class pinkwaterconnection(connection):

        def on_flag_capture(self):

            if self.team.id == 0: self.protocol.score_blue  += 1
            if self.team.id == 1: self.protocol.score_green += 1

            return connection.on_flag_capture(self)


    class pinkwaterprotocol(protocol):

        watercolor_r = 255 
        watercolor_g = 0
        watercolor_b = 255
        watercolor_offset = 60
        watercolor_enabled = True
        watercolor_prevent = False
        watercolor_randomized = True
        watercolor_map = True
        watercolor_teams = False
        watercolor_team_id = -1
        score_green = 0
        score_blue = 0

        def on_map_change(self, map):

            if self.watercolor_enabled:

                offset_r = offset_g = offset_b = self.watercolor_offset
                red   = self.watercolor_r 
                green = self.watercolor_g 
                blue  = self.watercolor_b 
                works = False

                if self.watercolor_map:
                    try:
                        offset_r = offset_g = offset_b = self.map_info.extensions['water_color_offset']
                        red, green, blue  = choice(self.map_info.extensions['water_color'])
                        works = True
                    except: pass

                if self.watercolor_teams : #and (self.watercolor_map is False or works is False)

                    if     self.score_blue > self.score_green: self.watercolor_team_id = self.blue_team.id
                    elif   self.score_blue < self.score_green: self.watercolor_team_id = self.green_team.id
                    else:  self.watercolor_team_id = self.spectator_team.id

                    if    self.watercolor_team_id == 0: red, green, blue = self.blue_team.color
                    elif  self.watercolor_team_id == 1: red, green, blue = self.green_team.color
                    else: red, green, blue = self.spectator_team.color

                if self.watercolor_randomized and (self.watercolor_map is False or works is False) and self.watercolor_teams is False: red, green, blue = choice(watercolors)

                if red < self.watercolor_offset: offset_r = red
                else: offset_r = self.watercolor_offset
                if green < self.watercolor_offset: offset_g = green
                else: offset_g = self.watercolor_offset
                if blue < self.watercolor_offset: offset_b = blue
                else: offset_b = self.watercolor_offset

                for x in range(512):
                    for y in range(512):
                        map.set_point(x,y,63,(red   - randint(0, offset_r),
                                              green - randint(0, offset_g),
                                              blue  - randint(0, offset_b)))

            if self.watercolor_prevent: self.watercolor_enabled = False

            self.score_green = 0
            self.score_blue = 0
            
            return protocol.on_map_change(self, map)


    return pinkwaterprotocol, pinkwaterconnection # i love cats
