"""
intelimode; Inteligent gamemodes
by thepolm3
"""
from random import randint

def get_mode_index(threshold,nop):
        index = 0
	for i in range(len(threshold)-1):
            if threshold[i] == threshold[i+1]:
                for a in range(i,len(threshold)-1):
                    if threshold[a] != threshold[i]:
                        break
                if threshold[a-1]<= nop < threshold[a]:
                    index=randint(i,a-1)
                    break
                else:
                    i=a
            elif threshold[i] <= nop < threshold[i+1]:
                index=i
                break
        else:
            index=len(threshold)-1
	return index

def apply_script(protocol,connection,config):

        class InteliModeProtocol(protocol):
	
		def on_mode_advance(self,mode,map):
			threshold = config.get("game_mode_threshold",[])
			threshold.append(32)
			if self.map:
                                return config.get("game_modes",[])[get_mode_index(threshold,len(self.players))]
			if "on_mode_advance" in dir(protocol):
                                return protocol.on_mode_advance(self.mode,map)
	return InteliModeProtocol,connection
