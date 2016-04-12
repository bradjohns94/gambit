import re
from hangups.bot.commands.command import Command


class AddNickname(Command):
    """ Add Nickname
        Give a user in the current chat a nickname which associates
        their full name to their karma value
    """

    def __init__(self):
        self.cmd_priv = float('inf')


    def parse(self, bot, message, user_priv):
        re_add = re.compile("^gambit[:,]? nickname (\w+ \w+) ((?:\w|\d)+|\((?:(?:\w|\d)+ )*(?:\w|\d)+\))[.!\?]?$", re.IGNORECASE)
        res = re_add.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['full'], self.cmd_args['nick'] = res.groups()
        self.bot = bot
        self.message = message
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Add Nickname")
            exists = self.bot.db.execute("SELECT COUNT(*) FROM users WHERE conversation_id = ? AND full_name = ?",
                                         (self.bot.conversation.id_, self.cmd_args['full'],))
            exists = exists.fetchone()[0] > 0
            if not exists:
                self.bot.say("No user found with that name.")
                return
            unique = self.bot.db.execute("SELECT COUNT(*) FROM users WHERE nickname = ?", (self.cmd_args['nick'],))
            unique = unique.fetchone()[0] == 0
            if not unique:
                self.bot.say("Someone already exists with that nickname.")
                return
            self.bot.db.execute("UPDATE users SET nickname = ? WHERE conversation_id = ? AND full_Name = ?",
                                (self.cmd_args['nick'], self.bot.conversation.id_, self.cmd_args['full'],))
            self.bot.db.commit()
            self.bot.say("Gave {} nickname {}".format(self.cmd_args['full'], self.cmd_args['nick']))
        except Exception as error:
            self.bot.log.warn("Error in Add Nickname:\n{}".format(error))


class ResolveUnknownUser(Command):
    """ Resolve Unknown User
        A fix to an issue with the hangups client which occassionally
        associates users with certain privacy settings as 'Unknown'
        Add an 'unknown' user to the database - associating the last
        'unknown' user to speak in the given conversation to a
        provided full name.
    """

    def __init__(self):
        self.cmd_priv = float('inf')


    def parse(self, bot, message, user_priv):
        re_resolve = re.compile('^gambit[:,]? resolve unknown (\w+ \w+)[.!\?]?$', re.IGNORECASE)
        res = re_resolve.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['name'] = res.groups()[0]
        self.parsed = True
        self.bot = bot
        self.user_priv = user_priv
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Resolve Unknown User")
            exists = self.bot.db.execute("SELECT COUNT(*) FROM users WHERE conversation_id = ? AND full_name = ?",
                    (self.bot.conversation.id_, self.cmd_args['name']))
            exists = exists.fetchone()[0] > 0
            if exists or self.cmd_args['name'] in self.bot.ids[self.bot.conversation.id_]:
                self.bot.say("A user with that name already exists.")
                return
            user_id = self.bot.ids[self.bot.conversation.id_]['Unknown']
            self.bot.db.execute("INSERT INTO users (user_id, conversation_id, full_name) VALUES (?, ?, ?)",
                    (user_id, self.bot.conversation.id_, self.cmd_args['name']))
            self.bot.db.commit()
            self.bot.say("Resolved User {}".format(self.cmd_args['name']))
        except Exception as error:
            self.bot.log.warn("Error in Resolve Unknown User:\n{}".format(error))
