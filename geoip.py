import urllib.requests
import GeoIP

DATABASE = GeoIP.open('./data/GeoLiteCity.dat')
FRENCH_COUNTRIES = ('fr', 'mq', 'gf', 'ht', 'ca', 'be', 'ch', 'tn')
SPANISH_COUNTRIES = ('mx', 'es', 'gt', 'ar', 'bo', 'cl', 've', 'pe', 'py', 'uy', 'ec', 'sr', 'gy', 'co', 'dr',
                     'hn', 'ni', 'sv', 'cr', 'pa', 'do')
PORTUGUESE_COUNTRIES = ('br', 'pt')
ARAB_COUNTRIES = ('il', 'dz', 'ma', 'af', 'eg', 'bh', 'iq', 'sa', 'lb')


class NativeCommand:
    def __init__(self, protocol):
        self.protocol = protocol

    def run(self, connection, user=None):
        if user is not None:
            connection = self.protocol.get_player(user)
        if connection not in self.protocol.players.values():
            raise ValueError()
        if not user:
            return "We believe you speak {}!".format(connection.language)
        else:
            return "We believe {} speaks {}!".format(connection.name, connection.language)


def get_country_code(ip_address):
    response = urllib.requests.urlopen("http://ip-api.com/json/{}".format(ip_address))
    data = response.read()
    data = data.decode("utf-8")
    country_code = "Unknown"
    if '"status":"success"' in data:
        country_code = data.split('"countryCode":"')[1].split('"')[0].lower()
    return country_code


def apply_script(protocol, connection, config):
    class LocalizeConnection(connection):

        def __init__(self, *args, **kwargs):
            connection.__init__(self, *args, **kwargs)
            # anglocentrism for countries unaccounted for
            self.language = 'English'
            self.localized = False

        def on_join(self):
            if not self.localized:
                country = get_country_code(self.address[0])
                if country in FRENCH_COUNTRIES:
                    self.language = 'French'
                elif country in SPANISH_COUNTRIES:
                    self.language = 'Spanish'
                elif country in PORTUGUESE_COUNTRIES:
                    self.language = 'Portuguese'
                elif country in 'dk':
                    self.language = 'Danish'
                elif country in 'se':
                    self.language = 'Swedish'
                elif country in 'no':
                    self.language = 'Norwegian'
                elif country in 'fi':
                    self.language = 'Finnish'
                elif country in 'de':
                    self.language = 'German'
                elif country in ('sr', 'nl'):
                    self.language = 'Dutch'
                elif country in 'gr':
                    self.language = 'Greek'
                elif country in 'it':
                    self.language = 'Italian'
                elif country in 'po':
                    self.language = 'Polish'
                elif country in 'ru':
                    self.language = 'Russian'
                elif country in 'sk':
                    self.language = 'Slovak'
                elif country in 'ua':
                    self.language = 'Ukrainian'
                elif country in 'in':
                    self.language = 'Hindi'
                elif country in 'kr':
                    self.language = 'Korean'
                elif country in 'kp':  # north korea
                    self.language = 'Korean, but with vpn'
                elif country in 'jp':
                    self.language = 'Japanese'
                elif country in ('cn', 'tw'):
                    self.language = 'Mandarin/Cantonese'
                elif country in ARAB_COUNTRIES:
                    self.language = 'Arab'
                elif country in 'va':  # vatican city
                    self.language = 'the Holy Tongue of God'
                self.localized = True
            return connection.on_join(self)

    protocol.commands['native'] = NativeCommand(protocol)
    return protocol, LocalizeConnection
