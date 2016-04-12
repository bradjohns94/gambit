class Command:
    """ Command
        A class representing the base interface to run and interact with a
        command trigger for the bot
    """
    cmd_args = {}
    cmd_priv = 0 # Privilege level required to execute command
    parsed = False
    help = None
    help_name = None
    syntax = None


    def parse(self, bot, message, user_priv):
        """ Parse
            Given a message sent to the bot, determine and return whether or
            not the message is a trigger for the given command. If so, fill
            the command argument dictionary with appropriate data to run the
            command itself
        """
        pass


    def execute(self):
        """ Execute
            After the command has been parsed and the arguments dictionary
            filled, execute the command itself
        """
        pass
