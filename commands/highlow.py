import re
from util import *
from random import randint

from hangups.bot.commands.command import Command

class PlayHighLow(Command):
    """ Play High Low
        Run through the dice game of high low given a self.bet and a 
        prediction on how the dice will fall
    """

    def __init__(self):
        self.help = """Play High-Low Command - example: 'gambit:
                       high-low 3 high'. Gamble karma on the simple 
                       dice game of high low. place a bet and call
                       'high', 'low', or 'seven' the bot then rolls 
                       two dice and you win if you called low and the 
                       roll was under 7, you called high and the roll 
                       was over 7, or you called seven and the roll 
                       was 7. Payoff for normal calls is 2x the placed 
                       bet. Payoff for seven is 4x the placed bet."""
        self.help_name = "high-low"
        self.syntax = "gambit: high-low <bet> <call>"



    def parse(self, bot, message, user_priv):
        re_play = re.compile("^.*gambit[:,]? high(?:-| )low (\d+) (high|low|7|seven).?!?\??.*$", re.IGNORECASE)
        res = re_play.match(message)
        if res is None:
            self.parsed = False
            return False
        self.cmd_args['bet'], self.cmd_args['call'] = res.groups()
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Play High Low")
            # Check the player's karma
            nick = resolve_nick(self.bot.db, self.bot.user.full_name)
            karma = get_karma(self.bot.db, nick)
            if not karma:
                self.bot.say("There's no karma for your linked name.")
            self.cmd_args['bet'] = int(self.cmd_args['bet'])
            if self.cmd_args['bet'] > karma:
                say = "You can't bet more karma than you have!\n"
                say += "You have a gambling addiction. Get help."
                self.bot.say(say)
                return
            elif self.cmd_args['bet'] < 1:
                self.bot.say("Go big or go home. bet a natural number.")
                return
            multiplier = 1
            if self.cmd_args['call'] == "7" or self.cmd_args['call'].lower() == "seven":
                multiplier = 4
            first_roll = randint(1, 6)
            second_roll = randint(1, 6)
            if "Bradley Johns" in self.bot.last_message.keys() \
                and self.bot.last_message["Bradley Johns"].lower() == "dovie'andi se tovya sagain":
                # WoT Easter Eggs, yo
                pairs = [ (1, 6), (6, 1), (2, 5), (5, 2), (4, 3), (3, 4) ]
                roll = pairs[randint(0, len(pairs) - 1)]
                first_roll = roll[0]
                second_roll = roll[1]
            total = first_roll + second_roll
            self.bot.say("Rolled {} and {}".format(first_roll, second_roll))
            change = self.cmd_args['bet'] * multiplier
            # Calculate your winnings
            if self.cmd_args['call'].lower() == "low" and total > 6:
                change *= -1
            elif self.cmd_args['call'].lower() == "high" and total < 8:
                change *= -1
            elif (self.cmd_args['call'].lower() == "seven" or self.cmd_args['call'] == "7") and total != 7:
                change = -1 * self.cmd_args['bet']
            # Update the player's karma
            self.bot.db.execute("UPDATE karma SET karma = karma + ? WHERE target = ?", (change, nick,))
            self.bot.db.commit()
            res = self.bot.db.execute("SELECT karma FROM karma WHERE target = ?", (nick,))
            karma = res.fetchone()[0]
            username = get_honorific_name(self.bot.db, self.bot.user.full_name, self.bot.conversation.id_)
            if change < 0:
                self.bot.say('Took {} karma from {}, total: {}.'.format(abs(change), username, karma))
            else:
                self.bot.say('Gave {} karma to {}, total: {}.'.format(change, username, karma))
        except Exception as error:
            self.bot.log.warn("Error in Play High Low:\n{}".format(error))
