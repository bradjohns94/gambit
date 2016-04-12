import re
from hangups.bot.commands.command import Command

class Help(Command):
    """ Help
        Provide help on using any command the bot knows
    """
    
    def parse(self, bot, message, user_priv):
        re_help = re.compile('^(?:gambit[:,]? )?help(?: (.+))?$', re.IGNORECASE)
        res = re_help.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['cmd'] = res.groups()[0]
        if self.cmd_args['cmd'] is not None:
            self.cmd_args['cmd'] = self.cmd_args['cmd'].lower()
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        # There's no such thing as a privilege level for help
        try:
            self.bot.log.info("Executing Help.")
            help_dict = {}
            # Build a help dictionary
            for cmd in self.bot.cmd_list:
                if cmd.help is not None and cmd.help_name is not None:
                    if cmd.help_name.lower() in help_dict.keys():
                        # Don't allow duplicate names
                        continue
                    help_dict[cmd.help_name.lower()] = cmd.help.lower()
            if self.cmd_args['cmd'] in help_dict.keys():
                response = help_dict[self.cmd_args['cmd']]
                response = response.replace('\n', ' ')
                response = ' '.join(response.split())
                self.bot.say(response)
                return
            response = 'help options: '
            for option in help_dict.keys():
                response += '{}, '.format(option)
            response = response[:-2] # Chop off trailing ', '
            self.bot.say(response)
        except Exception as error:
            self.bot.log.warn("Error in Help:\n{}".format(error))
