import re
from hangups.bot.commands.command import Command

class AddAlias(Command):
    """ Add Alias
        Create a mapping from some currently non-existant karma value
        to another
    """

    def __init__(self):
        self.help = """Add Alias Command - example: 'gambit: alias 
                       black white' link some valid karma term with a 
                       current karma of to any other karma term, 
                       existing or otherwise."""
        self.help_name = "alias"
        self.syntax = "gambit: alias <old> <new>"


    def parse(self, bot, message, user_priv):
        re_add = re.compile("^.*gambit[:,]? alias ((?:\w|\d)+|\((?:(?:\w|\d)+ )*(?:\w|\d)+\)) ((?:\w|\d)+|\((?:(?:\w|\d)+ )*(?:\w|\d)+\)).*$", re.IGNORECASE)
        res = re_add.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['old'], self.cmd_args['new'] = res.groups()
        self.cmd_args['old'] = self.cmd_args['old'].replace('(', '').replace(')', '')
        self.cmd_args['new'] = self.cmd_args['new'].replace('(', '').replace(')', '')
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Add Alias")
            karma = self.bot.db.execute("SELECT target, karma FROM karma")
            for pair in karma.fetchall():
                if pair[0].lower() == self.cmd_args['old'].lower() and pair[1] != 0:
                    self.bot.say("There's already karma for {}".format(self.cmd_args['old']))
                    return
            aliases = self.bot.db.execute("SELECT old, new FROM aliases")
            for pair in aliases.fetchall():
                if pair[0].lower() == self.cmd_args['old'].lower():
                    self.bot.say("There's already an alias for {}".format(self.cmd_args['old']))
                    return
            self.bot.db.execute("INSERT INTO aliases (old, new) VALUES(?, ?)", (self.cmd_args['old'],self.cmd_args['new'],))
            self.bot.db.commit()
            self.bot.say("Aliased {} to {}".format(self.cmd_args['old'], self.cmd_args['new']))
        except Exception as error:
            self.bot.log.warn("Error in Add Alias:\n{}".format(error))


class RemoveAlias(Command):
    """ Remove Alias
        Remove a link mapping one karma value to another
    """

    def __init__(self):
        self.help = """Remove Alias Command - example 'gambit: remove 
                     alias black' remove from the bots database an 
                     alias that maps the provided word to something 
                     else"""
        self.help_name = "remove alias"
        self.syntax = "gambit: remove alias <old>"


    def parse(self, bot, message, user_priv):
        re_remove = re.compile("^.*gambit[:,]? remove alias ((?:\w|\d)+|\((?:(?:\w|\d)+ )*(?:\w|\d)+\)).*$", re.IGNORECASE)
        res = re_remove.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['alias'] = res.groups()[0].replace('(', '').replace(')', '')
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Remove Alias")
            exists = self.bot.db.execute("SELECT COUNT(*) FROM aliases WHERE old = ?", (self.cmd_args['alias'],))
            exists = exists.fetchone()[0] > 0
            if not exists:
                self.bot.say("There is no alias for that name.")
                return
            self.bot.db.execute("DELETE FROM aliases WHERE old = ?",(self.cmd_args['alias'],))
            self.bot.db.commit()
            self.bot.say("Removed alias for {}".format(self.cmd_args['alias']))
        except Exception as error:
            self.bot.log.warn("Error in Remove Alias:\n{}".format(error))


class ListAliases(Command):
    """ List Aliases
        Print out all current aliases in the bot's database
    """

    def __init__(self):
        self.help = """List Aliases Command - example 'gambit: list 
                       aliases' have the bot list out all aliases 
                       currently in the database"""
        self.help_name = "list aliases"
        self.syntax = "gambit: list aliases"


    def parse(self, bot, message, user_priv):
        re_list = re.compile("^.*gambit[:,]? (show|list) aliases.*")
        res = re_list.match(message)
        if res is None:
            self.parsed = False
            return False
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing List Aliases")
            aliases = self.bot.db.execute("SELECT old, new FROM aliases")
            statement = ''
            statement += "Current aliases are:\n"
            for pair in aliases.fetchall():
                statement += "{} -> {}\n".format(pair[0], pair[1])
            self.bot.say(statement)
        except Exception as error: self.bot.log.warn("Error in List Aliases:\n{}".format(error))
