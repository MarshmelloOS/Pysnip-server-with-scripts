"""
Translates a players words for all players to understand.

BASED ON THIS https://github.com/mouuff/Google-Translate-API/blob/master/gtranslate.py
all translating done by google translate, all credit to Google

edited for pyspades  by thepolm3
"""

import urllib2
from commands import add,name,get_player

server_lang="en"
force_lang=False

#NOT by thepolm3, script by mouuff; https://github.com/mouuff/Google-Translate-API/blob/master/gtranslate.py
def translate(to_translate, to_langage="auto", langage="auto"):
	agents = {'User-Agent':"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)"}
	before_trans = 'class="t0">'
	link = "http://translate.google.com/m?hl=%s&sl=%s&q=%s" % (to_langage, langage, to_translate.replace(" ", "+"))
	request = urllib2.Request(link, headers=agents)
	page = urllib2.urlopen(request).read()
	result = page[page.find(before_trans)+len(before_trans):]
	result = result.split("<")[0]
	return result


def tr(connection,language=None):
        lps=connection.protocol.langplayers
        if connection.name in lps and not language:
                del(lps[lps.index(connection.name)])
                connection.send_chat("Translating is now off")
        else:
                connection.send_chat(translate("Translating is now on.",language).decode('utf-8'))
                connection.lang=language
                connection.protocol.langplayers.append(connection.name)

add(tr)
def apply_script(protocol, connection, config):
        
	class TranslateConnection(connection):
                lang=None
		def on_chat(self, value, global_message):
                        if force_lang:
                                value=translate(value,server_lang).decode("utf-8")
                        self.protocol.translateForAllPlayers(value,self.name,global_message)
                        return connection.on_chat(self, value, global_message)
        
	class TranslateProtocol(protocol):
                langplayers=[]
                def translateForAllPlayers(self,words,chattername,glob):
                        chatter=get_player(self,chattername)
                        for name in self.langplayers:
                                player=get_player(self,name)
                                trans=translate(words,player.lang).decode('utf-8')
                                if words.lower()!=trans.lower():
                                        if glob:
                                                player.send_chat(chattername+" ("+chatter.team.name+"): "+trans)
                                        elif player.team.name==chatter.team.name:
                                                player.send_chat(chattername+": "+words)
                        if words.lower()!=translate(words,server_lang).decode('utf-8').lower():
                                print("<"+chattername+"> ("+translate(words,server_lang).decode('utf-8')+")")
                                                                
        
	return TranslateProtocol, TranslateConnection
