import re
from util import *
from random import randint
from hangups.bot.commands.command import Command

class CreateQuote(Command):
    """ Create Quote
        Take the last statement made by a given person in chat and save it
        into the quotes database.
    """

    def __init__(self):
        self.help = """Create Quote Command - example 'gambit: quote
                       Mess' saves a quote from a given user in the
                       database to be stated later through the random 
                       quote command."""
        self.help_name = "quote"
        self.syntax = "gambit: quote <person>"


    def parse(self, bot, message, user_priv):
        re_add = re.compile("^(?:gambit[:,]? )?quote (.+)$", re.IGNORECASE)
        res = re_add.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['user'] = res.groups()[0]
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Create Quote")
            name = resolve_alias(self.bot.db, self.cmd_args['user'])
            name = resolve_full(self.bot.db, name).lower()
            if name not in self.bot.last_message.keys():
                self.bot.say("I don't know what they said.")
                return
            quote = self.bot.last_message[name]
            self.bot.db.execute("INSERT INTO quotes (quote, said_by) VALUES(?, ?)", (quote, name,))
            self.bot.db.commit()
            res = self.bot.db.execute("SELECT quote, said_by, said_at FROM quotes WHERE quote = ?", (quote,))
            res = res.fetchall()[0]
            date = res[2].split(' ')[0] # Get just the date in YYYY-MM-DD
            re_date = re.compile('^(\d{4})-(\d{1,2})-(\d{1,2})$')
            year, month, dat = re_date.match(date).groups()
            month = {'01': 'January',
                     '02': 'February',
                     '03': 'March',
                     '04': 'April',
                     '05': 'May',
                     '06': 'June',
                     '07': 'July',
                     '08': 'August',
                     '09': 'September',
                     '10': 'October',
                     '11': 'November',
                     '12': 'December'}[month]
            self.bot.say('"{}" - {}, {} {}'.format(res[0], res[1], month, year))
        except Exception as error:
            self.bot.log.warn("Error in Create Quote:\n{}".format(error))


class SayRandomQuote(Command):
    """ Say Random Quote
        Spit out a random quote from the database either in general or for a 
        specific user
    """

    def __init__(self):
        self.help = """Random Quote Command - example 'gambit: random
                       quote' have the bot state a random quote from
                       its database. The command can also quote a
                       specific user (example: 'gambit random mess 
                       quote')"""
        self.help_name = "random quote"
        self.syntax = "gambit: random quote, gambit: random <person> quote"


    def parse(self, bot, message, user_priv):
        re_say = re.compile("^gambit[:,]? (?:rand|random) (\w+)? ?quote.?!?\??", re.IGNORECASE)
        res = re_say.match(message)
        if res is None:
            self.parsed = False
            return False
        user = res.groups()[0]
        if user:
            self.cmd_args['user'] = user
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Say Random Quote with args {}".format(self.cmd_args))
            if 'user' in self.cmd_args.keys():
                name = resolve_alias(self.bot.db, self.cmd_args['user'])
                name = resolve_full(self.bot.db, name)
                res = self.bot.db.execute("SELECT quote, said_by, said_at FROM quotes WHERE said_by = ?", (name,))
            else:
                res = self.bot.db.execute("SELECT quote, said_by, said_at FROM quotes")
            quotes = res.fetchall()
            if len(quotes) == 0:
                self.bot.say("I couldn't find a quote!")
                return
            selected = quotes[randint(0, len(quotes) - 1)]
            date = selected[2].split(' ')[0]
            re_date = re.compile('^(\d{4})-(\d{1,2})-(\d{1,2})$')
            year, month, date = re_date.match(date).groups()
            month = {'01': 'January',
                     '02': 'February',
                     '03': 'March',
                     '04': 'April',
                     '05': 'May',
                     '06': 'June',
                     '07': 'July',
                     '08': 'August',
                     '09': 'September',
                     '10': 'October',
                     '11': 'November',
                     '12': 'December'}[month]
            self.bot.say('"{}" - {}, {} {}'.format(selected[0], selected[1], month, year))
        except Exception as error:
            self.bot.log.warn("Error in Say Random Quote:\n{}".format(error))
