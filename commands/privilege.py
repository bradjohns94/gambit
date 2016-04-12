import re

from util import *
from hangups.bot.commands.command import Command

class SetUserPrivilege(Command):
    """ Set User Privilege
        Let any user change any user of lower privilege's level to
        a value less than or equal to their own. Store updated
        privilege values in the privilege database
    """

    def __init__(self):
        self.help = """Set User Privilege Command - example 'gambit
                       set user privilege brad 10'. Updates the
                       privilege of a user who's current level is less
                       than yours to a value less than or equal to
                       your privilege level."""
        self.help_name = "set user privilege"
        self.syntax = "gambit: set user privilege <user> <level>"


    def parse(self, bot, message, user_priv):
        re_set = re.compile('^gambit[:,]? set user (?:priv|privilege) (\w+) (\d+)[.!\?]?$', re.IGNORECASE)
        res = re_set.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['user'], self.cmd_args['priv'] = res.groups()
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        # Get the current user privilege of the desired user
        try:
            self.bot.log.info("Executing Set User Privilege")
            user = resolve_alias(self.bot.db, self.cmd_args['user'])
            user = resolve_full(self.bot.db, user)
            current_priv = get_privilege(self.bot.db, user, self.bot.conversation)
            if current_priv is None:
                self.bot.say("{} is not a valid user".format(self.cmd_args['user']))
                return
            if self.user_priv <= current_priv:
                self.bot.say("{} has a higher privilege than you can change.".format(self.cmd_args['user']))
                return
            new_priv = int(self.cmd_args['priv'])
            if new_priv > self.user_priv:
                self.bot.say("You can't give someone higher privilege than you have.")
                return
            if new_priv < 0:
                self.bot.say("Don't be a dick. You can't give someone negative privilege.")
                return
            # If we've reached this point the change is valid
            self.bot.db.execute("UPDATE users SET privilege = ? WHERE full_name = ? AND conversation_id = ?",
                    (new_priv, user, self.bot.conversation.id_))
            self.bot.db.commit()
            self.bot.say("Gave {} a privilege of {}".format(self.cmd_args['user'], new_priv))
        except Exception as error:
            self.bot.log.warn("Error in Set User Privilege:\n{}".format(error))


class GetUserPrivilege(Command):
    """ Get User Privilege
        Have the bot retrieve and output the privilege level of
        a given user
    """


    def __init__(self):
        self.help = """Get User Privilege Command - example 'gambit
                       get user privilege brad'. Retrieves the
                       privilege of a user and outputs the value."""
        self.help_name = "get user privilege"
        self.syntax = "gambit: get user privilege <user>"


    def parse(self, bot, message, user_priv):
        re_get = re.compile('^gambit[:,]? get user (?:priv|privilege) (\w+)[.!\?]?$', re.IGNORECASE)
        res = re_get.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['user'] = res.groups()[0]
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        # Get the current user privilege of the desired user
        try:
            self.bot.log.info("Executing Get User Privilege")
            user = resolve_alias(self.bot.db, self.cmd_args['user'])
            user = resolve_full(self.bot.db, user)
            current_priv = get_privilege(self.bot.db, user, self.bot.conversation)
            if current_priv is None:
                self.bot.say("{} is not a valid user".format(self.cmd_args['user']))
                return
            self.bot.say("Privilege for {} is {}".format(self.cmd_args['user'], current_priv))
        except Exception as error:
            self.bot.log.warn("Error in Get User Privilege:\n{}".format(error))


class SetCommandPrivilege(Command):
    """ Set Command Privilege
        Admin only - set the privilege of a command so only users
        of equal or higher privilege can use it.
    """

    def __init__(self):
        self.help = """Set Command Privilege Command - example 'gambit
                       set command privilege wat 10'. Updates the
                       privilege of a command to be usable only by
                       users with equal or higher privilege"""
        self.help_name = "set command privilege"
        self.syntax = "gambit: set command privilege <command> <level>"
        self.cmd_priv = float('inf')


    def parse(self, bot, message, user_priv):
        re_set = re.compile("^gambit[:,]? set (?:cmd|command) (?:priv|privilege) ((?:(?:\w+) )*(?:\w+)) (\d+)[.!\?]?$", re.IGNORECASE)
        res = re_set.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['cmd'], self.cmd_args['priv'] = res.groups()
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Set Command Privilege")
            cmd = None
            for command in self.bot.cmd_list.keys():
                if command.help_name == self.cmd_args['cmd'] or\
                        command.__class__.__name__ == self.cmd_args['cmd']:
                    cmd = command.__class__.__name__
                    break
            if cmd is None:
                self.bot.say("{} is not a valid command".format(self.cmd_args['cmd']))
                return
            new_priv = int(self.cmd_args['priv'])
            self.bot.db.execute("UPDATE commands SET privilege = ? WHERE name = ?", (new_priv, cmd,))
            self.bot.db.commit()
            self.bot.cmd_list[self] = new_priv
            self.bot.say("Set privilege of {} to {}".format(self.cmd_args['cmd'], new_priv))
        except Exception as error:
            self.bot.log.warn("Error in Set Command Privilege:\n{}".format(error))


class GetCommandPrivilege(Command):
    """ Get Command Privilege
        Have the bot retrieve and output the privilege level of
        a given command
    """


    def __init__(self):
        self.help = """Get Command Privilege Command - example 'gambit
                       get command privilege wat'. Retrieves the
                       privilege of a command and outputs the value."""
        self.help_name = "get command privilege"
        self.syntax = "gambit: get command privilege <command>"



    def parse(self, bot, message, user_priv):
        re_get = re.compile("^gambit[:,]? get (?:cmd|command) (?:priv|privilege) ((?:(?:\w+) )*(?:\w+))[.!\?]?$", re.IGNORECASE)
        res = re_get.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['cmd'] = res.groups()[0]
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Get Command Privilege")
            cmd = None
            for command in self.bot.cmd_list.keys():
                if command.help_name == self.cmd_args['cmd'] or\
                        command.__class__.__name__ == self.cmd_args['cmd']:
                    cmd = command.__class__.__name__
                    break
            if cmd is None:
                self.bot.say("{} is not a valid command".format(self.cmd_args['cmd']))
                return
            current_priv = self.bot.db.execute("SELECT privilege FROM commands WHERE name = ?", (cmd,))
            current_priv = current_priv.fetchone()[0]
            self.bot.say("Privilege for {} is {}".format(self.cmd_args['cmd'], current_priv))
        except Exception as error:
            self.bot.log.warn("Error in Get Command Privilege:\n{}".format(error))
