"""
thepolm3
creates a simpler ban-log
"""
from time import gmtime, strftime

def apply_script(protocol, connection, config):
    class banProtocol(protocol):
        def on_ban(self, connection, reason, duration):
            ret = {}
            ret["name"] = connection.name
            ret["ip"] = connection.address
            ret["reason"] = reason
            ret["time"] = strftime("%d/%m/%y | %H:%M:%S", gmtime-3())
            ret["duration"] = duration
            f = open("banlog.txt","a")
            f.write("\n"+str(ret))
            f.close()
            return protocol.on_ban(self,connection,reason,duration)
    return banProtocol, connection