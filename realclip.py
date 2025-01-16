from pyspades.constants import *
import commands

R_EARLY_RELOAD_TRIG = 0.66
R_EARLY_RELOAD_MSG = "Don't throw your bullets away, you could need them"
R_GOOD_RELOAD_MSG = "You did not waste a single bullet, here's some health"
R_GOOD_RELOAD_HEAL = 5

def apply_script(protocol, connection, config):
    class RealclipConnection(connection):
    
        def on_reload(self):
            self.reloading = False
            if self.slow_reload:
                self.current_ammo += 1
                self.current_stock -= 1
                self.reload_callback()
                self.reload()
            else:
                if (self.current_ammo / self.ammo) >= R_EARLY_RELOAD_TRIG:
                    self.send_chat(R_EARLY_RELOAD_MSG)
                if self.current_ammo <= 0:
                    self.send_chat(R_GOOD_RELOAD_MSG)
                    self.set_hp(self.get_hp() + R_GOOD_RELOAD_HEAL)
                new_stock = max(0, self.current_stock - self.ammo)
                self.current_ammo = self.current_stock - new_stock
                self.current_stock = new_stock
                self.reload_callback()

    
    return protocol, RealclipConnection