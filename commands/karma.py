import re
from random import randint
from time import time

from util import *
from hangups.bot.commands.command import Command

class ChangeKarma(Command):
    """ Change Karma
        Take a list of groups gathered by karma regular expressions and
        parse out any increments or decrements which need to be applied
    """

    tokens = {}

    def __init__(self):
        self.help = """Change Karma Command - example 'poop++' Give
                       an entity karma with <entity>++ or take it away 
                       with <entity>--. From there, you can check a 
                       given entity's karma with 'karma <entity>'. To 
                       use an entity that's name is multiple words, be
                       sure to surround its name in parenthesis
                       (example '(more poop)++') Be careful, as karma
                       changes are limited."""
        self.help_name = 'change karma'
        self.syntax =  "<target>++, <target>--, (<multiword target>)++, (<mutiword target>)--"


    def parse(self, bot, message, user_priv):
        if not bot.karma[bot.conversation.id_]:
            self.parsed = False
            return False
        re_base = re.compile('((?:\w|\d)+(?:\+\+|\-\-))')
        re_paren = re.compile('(\((?:(?:\w|\d)+ )*(?:\w|\d)+\)(?:\+\+|\-\-))')
        changes = re_base.findall(message) 
        for change in re_paren.findall(message): # Trim the compound karma changes of their parentheses
            change = change.replace('(', '') 
            change = change.replace(')', '')
            changes.append(change)
        if not changes:
            self.parsed = False
            return False
        # Separate our changes into increments and decrements
        inc = []
        dec = []
        for change in changes:
            if change.endswith('++'):
                target = change[:-2] # Cut off the '++'
                target = resolve_alias(bot.db, target)
                link = resolve_full(bot.db, target)
                # Don't let people give themselves karma
                if link.lower() == bot.user.full_name.lower():
                    dec.append(target)
                else:
                    inc.append(target)
            elif change.endswith('--'): # Just to be safe
                target = change[:-2]
                target = resolve_alias(bot.db, target)
                dec.append(target) # Cut off the '--'
        self.cmd_args['inc'] = inc
        self.cmd_args['dec'] = dec
        self.parsed = True
        self.user_priv = user_priv
        self.bot = bot
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info('Executing Change Karma')
            for target in self.cmd_args['inc']:
                can_change = self._change_karma(target, 1)
                update_honorifics(self.bot.db, self.bot.conversation.id_)
                if not can_change:
                    self.bot.say('Bitch, be cool! Stop spamming me with karma')
                else:
                    username = target
                    if target in get_users(self.bot.db):
                        username = resolve_nick(target)
                        username = get_honorific_name(self.bot.db, username, self.bot.conversation.id_)
                    karma = get_karma(self.bot.db, target)
                    self.bot.say('Gave karma to {}, total: {}'.format(username, karma))
            for target in self.cmd_args['dec']:
                can_change = self._change_karma(target, -1)
                update_honorifics(self.bot.db, self.bot.conversation.id_)
                if not can_change:
                    self.bot.say('Bitch, be cool! Stop spamming me with karma')
                else:
                    karma = get_karma(self.bot.db, target)
                    username = target
                    if target in get_users(self.bot.db):
                        username = resolve_nick(target)
                        username = get_honorific_name(self.bot.db, username, self.bot.conversation.id_)
                    self.bot.say('Took karma from {}, total: {}'.format(username, karma))
        except Exception as error:
            self.bot.log.warn('Error in Change Karma:\n{}'.format(error))


    def _change_karma(self, name, change):
        """ Change Karma
            Make sure that the user can make a karma change using rate
            limiting and return whether or not the karma value was
            added or changed
        """
        can_change = self._apply_rate_limit()
        if not can_change: return False
        res = self.bot.db.execute('SELECT target, karma FROM karma')
        for target in res.fetchall():
            if target[0].lower() == name.lower():
                self.bot.db.execute('UPDATE karma SET karma = karma + ? WHERE target = ?', (change, target[0],))
                self.bot.db.commit()
                return True
        self.bot.db.execute("INSERT INTO karma (target, karma) VALUES(?, 0)", (name,))
        self.bot.db.execute("UPDATE karma SET karma = karma + ? WHERE target = ?", (change, name,))
        self.bot.db.commit()
        return True


    def _apply_rate_limit(self):
        """ Apply Rate Limit
            Check how frequently the current user has run karma commands
            and, if they exceed a certain threshold (30 seconds) return
            False so they don't make any karma changes
        """
        update_time = time()
        user_name = self.bot.user.full_name
        if user_name in self.tokens.keys():
            last_change = self.tokens[user_name][0]
            # Add 1 token for every 30 seconds from the last change
            added_tokens = int((update_time - last_change) / 30)
            self.tokens[user_name][1] += added_tokens
            # Max at 5 self.tokens
            if self.tokens[user_name][1] > 5:
                self.tokens[user_name][1] = 5
        else:
            # Initialize the users token pair (last change, # of self.tokens)
            self.tokens[user_name] = [update_time, 5] # Start with 5 self.tokens
        if self.tokens[user_name][1] <= 0:
            return False
        self.tokens[user_name][1] -= 1
        return True


class GetKarma(Command):
    """ Get Karma
        Resolve a targets name after aliasing and state its karma
    """

    def __init__(self):
        self.help = """Get Karma Command - example 'Karma poop' 
                       Retrieves and states the karma of a given
                       entity. Like with the change karma command,
                       entities to access karma from can be wrapped in
                       parenthesis (example karma (even more poop))."""
        self.help_name = "get karma"
        self.syntax = "karma <target>, karma (<multiword target>)"


    def parse(self, bot, message, user_priv):
        if not bot.karma[bot.conversation.id_]:
            self.parsed = False
            return False
        re_karma = re.compile('^(?:gambit[:,]? )?karma ((?:\w|\d)+|\((?:(?:\w|\d)+ )*(?:\w|\d)+\))$', re.IGNORECASE)
        targets = re_karma.findall(message)
        if len(targets) == 0:
            self.parsed = False
            return False
        for i, target in enumerate(targets):
            target = target.replace('(','')
            target = target.replace(')','')
            targets[i] = target
        self.cmd_args['targets'] = targets
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info('Executing Get Karma')
            for target in self.cmd_args['targets']:
                target = resolve_alias(self.bot.db, target)
                karma = get_karma(self.bot.db, target)
                self.bot.say('Karma for {}: {}.'.format(target, karma))
        except Exception as error:
            self.bot.log.warn('Error in Get Karma:\n{}'.format(error))


class Spot(Command):
    """ Spot
        Transfer karma from the calling user to the borrower. The total
        karma is specified as an arguments and any outstanding debts are
        logged in the debts table of the database
    """

    def __init__(self):
        self.help = """Spot Command - example: 'Gambit: spot Goofy 1'
                       Lend some karma to another user. The karma is
                       taken from the callers total and added to the
                       borrower and the current debt is tracked and
                       can be viewed by the 'show debts' command."""
        self.help_name = "spot"
        self.syntax = "gambit: spot <borrower> <amount>"


    def parse(self, bot, message, user_priv):
        if not bot.karma[bot.conversation.id_]:
            self.parsed = False
            return False
        re_spot = re.compile("^.*gambit[:,]? spot (\w+) (\d+).?!?\??.*$", re.IGNORECASE)
        res = re_spot.match(message)
        if res is None:
            self.parsed = False
            return False
        borrower, amount = res.groups()
        self.cmd_args['borrower'] = borrower
        self.cmd_args['amount'] = amount
        self.user_priv = user_priv
        self.bot = bot
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info('Excecuting Spot')
            lender = resolve_nick(self.bot.db, self.bot.user.full_name)
            borrower = resolve_alias(self.bot.db, self.cmd_args['borrower'])
            amount = int(self.cmd_args['amount'])
            borrower_username = resolve_full(self.bot.db, borrower)
            borrower_username = get_honorific_name(self.bot.db, borrower_username, self.bot.conversation.id_)
            # Check to make sure the loan isn't invalid
            if amount > get_karma(self.bot.db, lender):
                self.bot.say("You're a bit too generous, friend. Don't lend what you don't have.")
                return
            if borrower.lower() == 'gambit':
                self.bot.say("I don't need your charity!")
                return
            if borrower.lower() not in get_users(self.bot.db):
                self.bot.say("You can only lend to another user")
                return
            # Check if there are pre-existing debts
            debt_exists = self.bot.db.execute("SELECT COUNT(*) FROM debt WHERE lender = ? AND borrower = ?", (lender, borrower,))
            debt_exists = debt_exists.fetchone()[0] > 0
            if not debt_exists:
                bot.db.execute("INSERT INTO debt VALUES(?, ?, 0)", (lender, borrower,))
                bot.db.commit()
            # Check if this is repaying an existing debt
            change = amount
            return_loan = self.bot.db.execute("SELECT COUNT(*) FROM debt WHERE lender = ? AND borrower = ?", (borrower, lender,))
            return_loan = return_loan.fetchone()[0] > 0
            if return_loan:
                current_debt = self.bot.db.execute("SELECT amount FROM debt WHERE lender = ? AND borrower = ?", (borrower, lender,))
                current_debt = current_debt.fetchone()[0]
                if amount >= current_debt: # Debt was paid in full
                    self.bot.db.execute("UPDATE debt SET amount = 0 WHERE lender = ? AND borrower = ?", (borrower, lender,))
                    self.bot.db.commit()
                    change -= current_debt
                else: # Partial payment
                    self.bot.db.execute("UPDATE debt SET amount = amount - ? WHERE lender = ? AND borrower = ?", (amount, borrower, lender,))
                    self.bot.db.commit()
                    self.bot.say("Gave {} karma to {}. You now owe them {} karma".format(amount, borrower_username, current_debt - amount))
                    # Get subtract the given karma before we return
                    self.bot.db.execute("UPDATE karma SET karma = karma - ? WHERE target = ?", (amount, lender,))
                    self.bot.db.commit()
                    return
            # Apply the remaining changes
            self.bot.db.execute("UPDATE debt SET amount = amount + ? WHERE lender = ? AND borrower = ?", (change, lender, borrower,))
            self.bot.db.commit()
            total_debt = self.bot.db.execute("SELECT amount FROM debt WHERE lender = ? AND borrower = ?", (lender, borrower,))
            total_debt = total_debt.fetchone()[0]
            self.bot.db.execute("UPDATE karma SET karma = karma - ? WHERE target = ?", (change, lender,))
            self.bot.db.execute("UPDATE karma SET karma = karma + ? WHERE target = ?", (change, borrower,))
            self.bot.db.commit()
            self.bot.say("Spotted {} {} karma, they now owe you {}".format(borrower_username, amount, total_debt))
        except Exception as error:
            self.bot.log.warn('Error in Spot:\n{}'.format(error))


class ShowDebts(Command):
    """ Show Debts
        List out all currently outstanding debts held in the database
    """

    def __init__(self):
        self.help = """Show Debts - example 'Gambit: show debts'
                       has the bot list out all current debts in the
                       database where the current amount owed is
                       greater than 0."""
        self.help_name = "show debts"
        self.syntax = "gambit: show debts" 


    def parse(self, bot, message, user_priv):
        if not bot.karma[bot.conversation.id_]:
            self.parsed = False
            return False
        re_debt = re.compile("^.*gambit[:,]? (show|list) debts.?!?\??.*$", re.IGNORECASE)
        res = re_debt.match(message)
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
            self.bot.log.info('Executing Show Debts')
            debts = self.bot.db.execute('SELECT * FROM debt')
            for debt in debts.fetchall():
                if debt[2] > 0:
                    self.bot.say("{} owes {} {} karma.".format(debt[1],debt[0],debt[2]))
        except Exception as error:
            self.bot.log.warn('Error in Show Debts:\n{}'.format(error))


class GetTopKarma(Command):
    """ Get Top Karma
        Find the entity in the database with the highest karma value and
        tell everyone how its the best thing ever
    """

    def __init__(self):
        self.help = """Top Karma Command - example 'gambit: top karma'
                       Has the bot state what entity has the highest
                       karma in the database."""
        self.help_name = "top karma"
        self.syntax = "gambit: top karma"



    def parse(self, bot, message, user_priv):
        if not bot.karma[bot.conversation.id_]:
            self.parsed = False
            return False
        re_top = re.compile('^.*gambit[:,]? (top|highest) karma.?!?\??.*$', re.IGNORECASE)
        res = re_top.match(message)
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
            self.bot.log.info("Executing Get Top Karma")
            karma = self.bot.db.execute("SELECT target, karma  FROM karma")
            karma = karma.fetchall()
            top_target = None
            top_karma = 0
            for pair in karma:
                if not top_target or pair[1] > top_karma:
                    top_target = pair[0]
                    top_karma = pair[1]
            self.bot.say("The current best thing ever is {} with {} karma".format(top_target, top_karma))
        except Exception as error:
            self.bot.log.warn("Error in Get Top Karma:\n{}".format(error))


class GetRandomKarma(Command):
    """ Get Random Karma
        Select a random karma from the bot's database and state it in
        chat
    """

    def __init__(self):
        self.help = """Random Karma Command - example 'gambit: random
                       karma' Has the bot state some randomly selected
                       karma value from its database."""
        self.help_name = "random karma"
        self.syntax = "gambit: random karma"


    def parse(self, bot, message, user_priv):
        if not bot.karma[bot.conversation.id_]:
            self.parsed = False
            return False
        re_rand = re.compile('^.*gambit[:,]? random karma.?!?\??.*$', re.IGNORECASE)
        res = re_rand.match(message)
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
            self.bot.log.info("Executing Get Random Karma")
            karma = self.bot.db.execute("SELECT target, karma FROM karma")
            karma = karma.fetchall()
            rand_karma = karma[randint(0, len(karma)-1)]
            self.bot.say("Karma for {} is {}".format(rand_karma[0], rand_karma[1]))
        except Exception as error:
            self.bot.log.warn("Error in Get Random Karma:\n{}".format(error))


class EnableKarma(Command):
    """ Enable Karma
        Admin only. If karma is disabled, re-enable it in the current
        chat
    """

    def __init__(self):
        self.cmd_priv = float('inf')


    def parse(self, bot, message, user_priv):
        re_enable = re.compile("^gambit[:,]? yes\s?karma.?$", re.IGNORECASE)
        res = re_enable.match(message)
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
            self.bot.log.info("Executing Enable Karma")
            if not self.bot.karma[self.bot.conversation.id_]:
                self.bot.say("Enabling karma...")
            self.bot.karma[self.bot.conversation.id_] = True
        except Exception as error:
            self.bot.log.warn("Error in Enable Karma:\n{}".format(error))


class DisableKarma(Command):
    """ Disable Karma
        Admin only. If karma is enabled, disable it in the current
        chat
    """

    def __init__(self):
        self.cmd_priv = float('inf')


    def parse(self, bot, message, user_priv):
        re_disable = re.compile("^gambit[:,]? no\s?karma.?$", re.IGNORECASE)
        res = re_disable.match(message)
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
            self.bot.log.info("Executing Disable Karma")
            if self.bot.karma[self.bot.conversation.id_]:
                self.bot.say("Disabling karma...")
            self.bot.karma[self.bot.conversation.id_] = False
        except Exception as error:
            self.bot.log.warn("Error in Disable Karma:\n{}".format(error))
