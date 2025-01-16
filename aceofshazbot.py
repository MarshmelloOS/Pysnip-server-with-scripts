"""
Introduces Tribes: Ascend VGS commands to Ace of Spades.

Maintainer: Nate Shoffner
"""

SHOW_COMMAND_IN_MESSAGE = True


def apply_script(protocol, connection, config):

    vgs_commands_global = {
        'VGY': 'Yes.',
        'VGN': 'No.',
        'VGH': 'Hi.',
        'VGB': 'Bye.',
        'VGO': 'Ooops.',
        'VGQ': 'Quiet!',
        'VGS': 'Shazbot!',
        'VGW': 'Woohoo!',

        # compliments
        'VGCA': 'Awesome!',
        'VGCG': 'Good game.',
        'VGCN': 'Nice move!',
        'VGCS': 'Great shot!',
        'VGCY': 'You Rock!',

        # responses
        'VGRA': 'Any time.',
        'VGRD': 'I don\'t know.',
        'VGRT': 'Thanks.',
        'VGRW': 'Wait.',

        # taunts
        'VGTA': 'Aww, that\'s too bad!',
        'VGTB': 'Is that the best you can do?',
        'VGTG': 'I am the greatest!',
        'VGTT': 'THAT was graceful!',
        'VGTW': 'When will you learn?'
    }

    vgs_commands_team = {
        'VAA': 'Attack!',
        'VAB': 'Attack the enemy base!',
        'VAC': 'Chase the enemy flag carrier!',
        'VAD': 'Disrupt the enemy defense!',
        'VAF': 'Get the enemy flag!',
        'VAG': 'Destroy the enemy generator!',
        'VAR': 'Reinforce the offense!',
        'VAS': 'Destroy enemy sensors!',
        'VAT': 'Destroy enemy turrets!',
        'VAV': 'Destroy the enemy vehicle!',
        'VAW': 'Wait for my signal before attacking!',

        # defend
        'VDB': 'Defend our base!',
        'VDC': 'Defend the flag carrier!',
        'VDE': 'Defend the entrances!',
        'VDF': 'Defend our flag!',
        'VDG': 'Defend our generator!',
        'VDM': 'Cover me!',
        'VDR': 'Reinforce our defense!',
        'VDS': 'Defend our sensors!',
        'VDT': 'Defend our turrets!',
        'VDV': 'Defend our vehicle!',

        # repair
        'VRG': 'Repair our generator!',
        'VRS': 'Repair our sensors!',
        'VRT': 'Repair our turrets!',
        'VRV': 'Repair the vehicle!',

        # base
        'VBC': 'Our base is clear.',
        'VBE': 'The enemy is in our base.',
        'VBR': 'Retake our base!',
        'VBS': 'Secure our base!',

        # commands
        'VCA': 'Acknowledged.',
        'VCC': 'Completed.',
        'VCD': 'Declined.',
        'VCW': 'What\'s my assignment?',

        # enemy
        'VED': 'The enemy is in disarray.',
        'VEG': 'The enemy generator is destroyed.',
        'VES': 'The enemy sensors are destroyed.',
        'VET': 'The enemy turrets are destroyed.',
        'VEV': 'The enemy vehicle is destroyed.',

        # flag
        'VFD': 'Defend our flag!',
        'VFF': 'I have the flag!',
        'VFG': 'Give me the flag!',
        'VFR': 'Retrieve our flag!',
        'VFS': 'Our flag is secure.',
        'VFT': 'Take the flag from me!',
        'VFQ': 'I\'ll retrieve our flag!',

        # need
        'VNC': 'Need covering fire.',
        'VND': 'I need a driver.',
        'VNE': 'I need an escort.',
        'VNH': 'Hold that vehicle! I\'m coming!',
        'VNR': 'I need a ride!',
        'VNS': 'I need support!',
        'VNV': 'Vehicle ready. Need a ride?',
        'VNW': 'Where to?',

        # self attack
        'VSAA': 'I will attack.',
        'VSAB': 'I will attack the enemy base.',
        'VSAF': 'I\'ll go for the enemy flag.',
        'VSAG': 'I\'ll attack the enemy generator.',
        'VSAS': 'I\'ll attack the enemy sensors.',
        'VSAT': 'I\'ll attack the enemy turrets.',
        'VSAV': 'I\'ll attack the enemy vehicle.',

        # self defend
        'VSDB': 'I will defend our base.',
        'VSDD': 'I will defend.',
        'VSDF': 'I will defend our flag.',
        'VSDG': 'I\'ll defend our generator.',
        'VSDS': 'I\'ll defend our sensors.',
        'VSDT': 'I\'ll defend our turrets.',
        'VSDV': 'I\'ll defend our vehicle.',

        # self repair
        'VSRG': 'I\'ll repair our generator.',
        'VSRS': 'I\'ll repair our sensors.',
        'VSRT': 'I\'ll repair our turrets.',
        'VSRV': 'I\'ll repair the vehicle.',

        # self task
        'VSTC': 'I\'ll cover you.',
        'VSTD': 'I\'ll set up defenses.',
        'VSTF': 'I\'ll deploy forcefields.',
        'VSTO': 'I\'m on it.',
        'VSTS': 'I\'m deploying sensors.',
        'VSTT': 'I\'m deploying turrets.',
        'VSTV': 'I\'ll get a vehicle ready.',

        # self upgrades
        'VSUG': 'I\'ll upgrade our generator.',
        'VSUS': 'I\'ll upgrade our sensors.',
        'VSUT': 'I\'ll upgrade our base turrets.',

        # target
        'VTA': ' Target acquired.',
        'VTB': ' Target the enemy base! I\'m in position.',
        'VTD': ' Target destroyed.',
        'VTF': ' Target the enemy flag! I\'m in position.',
        'VTM': ' Fire on my target!',
        'VTN': ' I need a target painted!',
        'VTS': ' Target the sensors! I\'m in position.',
        'VTT': ' Target the turret! I\'m in position.',
        'VTV': ' Target the vehicle! I\'m in position.',
        'VTW': ' Wait! I\'ll be in range soon.',

        # warning
        '[VWE]': 'Incoming hostiles!',
        '[VWV]': 'Incoming enemy vehicle!',

        # very quick
        'VVY': 'Yes.',
        'VVN': 'No.',
        'VVA': 'Anytime.',
        'VVB': 'Is our base secure?',
        'VVC': 'Cease fire!',
        'VVD': 'I don\'t know.',
        'VVH': 'Help!',
        'VVM': 'Move!',
        'VVS': 'Sorry.',
        'VVT': 'Thanks.',
        'VVW': 'Wait.'
    }

    class AceofShazbotConnection(connection):

        def on_chat(self, value, global_message):
            upper = value.upper()

            if upper in vgs_commands_global:
                return connection.on_chat(self,
                                          vgs_commands_global[upper], True)
            if upper in vgs_commands_team:
                return connection.on_chat(self,
                                          vgs_commands_team[upper], False)

            return connection.on_chat(self, value, global_message)

    return protocol, AceofShazbotConnection
