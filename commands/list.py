import re
from hangups.bot.commands.command import Command

class ListCommands(Command):
    """ List Commands
        Print out the basic syntax for every command the bot
        knows
    """

    def parse(self, bot, message, user_priv):
        re_list = re.compile("^gambit[:,]? (show|list) commands$", re.IGNORECASE)
        res = re_list.match(message)
        if res is None:
            self.parsed = False
            return False
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing List Commands.")
            response = ''
            for command in self.bot.cmd_list:
                syntax = command.syntax
                if syntax is not None:
                    response += syntax + "\n"
            self.bot.say(response)
        except Exception as error:
            self.bot.log.warn("Error in list commands:\n{}".format(error))
