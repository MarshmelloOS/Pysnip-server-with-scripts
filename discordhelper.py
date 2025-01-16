#*-* coding: utf-8

#Coded by ImChris
#https://imchris.tk
#https://ubge.org

import thread
import urllib
import urllib2

USER_AGENT = "User-Agent", "Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11"
BAN_WEBHOOK = "https://discord.com/api/webhooks/972607321375133726/3-veJzWvY5N8Qi_GwsxQMsJsvSPmsBfz_tb0Z0uaRgrnfrv7TzdG4ufbOWy_UTcnB8VT" #Banimentos
LOGIN_WEBHOOK = "https://discord.com/api/webhooks/972367910393761883/JjEbvJAFhv8gW4YHcgxH0ZwIXJQtaCjo1HPayEj7vksjlSfCYP2N446VKtRWKFpnfK1s" 	#Logins

def send_discord_message(connection, message, url=""):
	connection.protocol.discord_say(message, url)

def apply_script(protocol, connection, config):

	class DiscordHelperProtocol(protocol):

		def discord_say(self, message, url=BAN_WEBHOOK):
			data = urllib.urlencode({"content": message})
			post_request = urllib2.Request(url, data)
			post_request.add_header("User-Agent", USER_AGENT)
			return urllib2.urlopen(post_request).read()

	class DiscordHelper(connection):

		def on_user_login(self, user_type, verbose = True):
			protocol = self.protocol
			message = '`%s` efetuou login como `%s` no servidor `%s`' % (self.name, user_type, protocol.name)
			thread.start_new_thread(send_discord_message, (self, message, 
				LOGIN_WEBHOOK))
			connection.on_user_login(self, user_type, verbose)

	return DiscordHelperProtocol, DiscordHelper
