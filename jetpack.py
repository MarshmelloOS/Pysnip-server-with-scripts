from pyspades.server import input_data
from twisted.internet.reactor import callLater, seconds
from commands import add

#script by MegaStar (27/10/2020)

TOTAL_FUEL = 60.0 #the maximum fuel per jetpack
FUEL_PER_SECONDS = 4.0 #the amount of fuel that will be obtained every 1 second while a player is crouching
JETPACK = True #all players start with the jetpack on (default)
JETPACK_Z_LIMIT = 0 #if the player exceeds this height, he will no longer be able to continue using the jetpack (z pos)


def jetpack(connection):
   connection.jetpack = False if connection.jetpack else True
   connection.send_chat('Your jetpack is turned {0}.'.format(['off', 'on'][int(connection.jetpack)]))

add(jetpack)


def apply_script(protocol, connection, config):
   class JetPackConnection(connection):

      def __init__(self, *args, **kwargs):
         self.charge = TOTAL_FUEL
         self.jetpack = JETPACK
         self.can_fly = JETPACK
         self.sc = None
         self.start_charge = False
         connection.__init__(self, *args, **kwargs)


      def on_spawn(self, pos):
         if self.jetpack:
            self.charge = TOTAL_FUEL
            self.jetpack = JETPACK
            self.can_fly = JETPACK
            self.sc = None
            self.start_charge = False
            self.send_chat('jetpack fuel: ({0}/100)%, press V to use it!'.format(int((self.charge*100)/TOTAL_FUEL)))
         return connection.on_spawn(self, pos)

      
      def can_use_jetpack(self):
         if not self.world_object or not self.jetpack or not self.can_fly:
            return False
         return True


      def use_jetpack(self):
         if self.can_use_jetpack():
            if self.charge > 0:
               if self.world_object.position.z > JETPACK_Z_LIMIT:
                  self.charge -= 1
                  self.world_object.jump = True
                  input_data.player_id = self.player_id
                  input_data.up = self.world_object.up
                  input_data.down = self.world_object.down
                  input_data.left = self.world_object.left
                  input_data.right = self.world_object.right
                  input_data.crouch = self.world_object.crouch
                  input_data.sneak = self.world_object.sneak
                  input_data.sprint = self.world_object.sprint
                  input_data.jump = True
                  self.protocol.send_contained(input_data)
                  callLater(0.12, self.use_jetpack)
               else:
                  self.can_fly = False                  
            else:
               self.send_chat('Oops, there is no more fuel in your jetpack, crouch to reload it (dont move)')


      def on_animation_update(self, jump, crouch, sneak, sprint):
         if self.jetpack:
            if sneak:
               if not self.can_fly:
                  self.can_fly = True
                  self.use_jetpack()
            else:
               if self.can_fly:
                  self.can_fly = False
               if crouch:
                  if self.charge < TOTAL_FUEL:
                     self.start_charge = True
                     self.sc = seconds()
               else:
                  if self.start_charge:
                     self.start_charge = False
                     diff = int(seconds() - self.sc)
                     if diff > 0:
                        self.charge += diff * FUEL_PER_SECONDS
                        if self.charge > TOTAL_FUEL:
                           self.charge = TOTAL_FUEL
                        self.send_chat('jetpack fuel: ({0}/100)%, press V to use it!'.format(int((self.charge*100)/TOTAL_FUEL)))
                  
            return connection.on_animation_update(self, jump, crouch, sneak, sprint)

   return protocol, JetPackConnection


      
