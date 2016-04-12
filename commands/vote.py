from random import randint
from util import *
import re
from hangups.bot.commands.command import Command

class Vote:
    """ Vote
        A class representing the current state of a bot-level vote
        Note that votes are tied to an instance of the bot, and all data
        is lost if the bot is restarted
    """
    
    def __init__(self, owner_priv, question, options=[], mutable=False):
        # Note that all votes ARE mutable, the mutable option dictates whether the vote can
        # be altered by anyone or just admins and the owner
        self.owner_priv = owner_priv
        self.options = []
        for option in options:
            self.options.append(option.lower())
        self.mutable = mutable
        self.votes = {}
        self.question = question


    def add_option(self, option, user_priv):
        """ Add Option
            Check if a user has permission to add an option and, if so, add
            it to the vote list and return True, otherwise return
            False
        """
        # Only add an option if the user is an admin or the vote is mutable
        if not self.mutable and user_priv < self.owner_priv:
            return False
        if option == 'invalid':
            return False
        self.options.append(option.lower())
        return True


    def remove_option(self, option, user_priv):
        """ Remove Option
            Check if a user has permission to remove an option from  the vote
            Because there are multiple failure states, return an
            exit code which corresponds to an exit state
        """
        # Only remove an option if the user is an admin or the vote is mutable
        if not self.mutable and user_priv < self.owner_priv:
            return 1
        if option.lower() not in self.options: return 2
        self.options.remove(option.lower())
        to_remove = []
        for voter in self.votes:
            if self.votes[voter] == option.lower(): to_remove.append(voter)
        for voter in to_remove:
            del(self.votes[voter])
        return 0
   

    def vote(self, name, vote):
        """ Vote
            Cast a vote and store it in the object
        """
        if vote.lower() not in self.options:
            return False
        self.votes[name] = vote
        return True


    def end_vote(self, bot, user_priv):
        """ End Vote
            If the user has permission to end the vote, end it and determine
            which option won. Resolve ties with karma, then resolve karma ties
            at random
            Return an error status
        """
        if user_priv < self.owner_priv:
            return 'invalid'
        if len(self.votes.keys()) == 0:
            return None
        totals = {}
        for vote in self.votes:
            if self.votes[vote] not in totals.keys():
                totals[self.votes[vote]] = 0
            totals[self.votes[vote]] += 1
        # We want to account for ties
        max_votes = None
        for option in totals:
            if max_votes is None or totals[option] > max_votes: max_votes = totals[option]
        winners = []
        for option in totals:
            if totals[option] == max_votes:
                winners.append(option)
        # Try to break ties with karma
        if len(winners) > 1:
            karma_totals = {}
            for winner in winners:
                karma_totals[winner] = 0
            for vote in self.votes:
                if self.votes[vote] in winners:
                    karma_totals[winner] += get_karma(bot, resolve_nick(bot, vote))
            max_karma = None
            for option in totals:
                if totals[option] > max_karma: max_karma = totals[option]
            winners = []
            for option in karma_totals:
                if karma_totals[option] == max_karma:
                    winners.append(option)
        winner = winners[randint(0, len(winners) - 1)]
        return winner


class StartVote(Command):
    """ Start Vote
        Create a vote object - store it in the bot instance and say
        that the vote has started
    """

    def __init__(self):
        self.help = """Start Vote Command - example 'gambit: start
                       vote does voting work?'. Start a vote with a
                       specific question for all users to respond to
                       and come to a decision."""
        self.help_name = "start vote"
        self.syntax = "gambit: start vote, gambit: start open vote"


    def parse(self, bot, message, user_priv):
        re_start = re.compile("^.*gambit[:,]? start (open )? ?vote (.+).*$", re.IGNORECASE)
        res = re_start.match(message)
        if res is None or bot.vote is not None:
            self.parsed = False
            return False
        groups = res.groups()
        if len(groups) > 1:
            self.cmd_args['mutable'] = True
            self.cmd_args['question'] = groups[1]
        else:
            self.cmd_args['mutable'] = False
            self.cmd_args['question'] = groups[0]
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Start Vote")
            self.bot.vote = Vote(self.user_priv, self.cmd_args['question'], mutable=self.cmd_args['mutable'])
            self.bot.say("Vote Started: {}".format(self.cmd_args['question']))
        except Exception as error:
            self.bot.log.warn("Error in Start Vote:\n{}".format(error))


class AddVoteOption(Command):
    """ Add Vote Option
        Allow a user to add an option to the current vote
    """
    
    def __init__(self):
        self.help = """Add Vote Option Command - example: 'gambit: add
                       vote option yes'. Add an option to the
                       currently existing vote."""
        self.help_name = "add vote option"
        self.syntax =  "gambit: add vote option <option>"


    def parse(self, bot, message, user_priv):
        re_add = re.compile("^gambit[:,]? add vote option (.+)$", re.IGNORECASE)
        res = re_add.match(message)
        if res is None or bot.vote is None:
            self.parsed = False
            return False
        self.cmd_args['option'] = res.groups()[0]
        self.user_priv = user_priv
        self.bot = bot
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Add Vote Option")
            success = self.bot.vote.add_option(self.cmd_args['option'], self.user_priv)
            if success:
                self.bot.say("Added option: {}".format(self.cmd_args['option']))
            else:
                self.bot.say("You don't have permission to add an option.")
        except Exception as error:
            self.bot.log.warn("Error in Add Vote Option:\n{}".format(error))


class RemoveVoteOption(Command):
    """ Remove Vote Option
        Allow a user to remove an option from the current vote
    """

    def __init__(self):
        self.help = """Remove Vote Option Command - example: 'gambit:
                       remove vote option yes'. Remove an option from 
                       the currently existing vote."""
        self.help_name = "remove vote option"
        self.syntax = "gambit: remove vote option <option>"


    def parse(self, bot, message, user_priv):
        re_remove = re.compile("^gambit[:,]? remove vote option (.+)$", re.IGNORECASE)
        res = re_remove.match(message)
        if res is None or bot.vote is None:
            self.parsed = False
            return False
        self.cmd_args['option'] = res.groups()[0]
        self.user_priv = user_priv
        self.bot = bot
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Remove Vote Option")
            status = self.bot.vote.remove_option(self.cmd_args['option'], self.user_priv)
            if status == 0:
                self.bot.say("Removed option: {}, anyone who voted for it must vote again.".format(self.cmd_args['option']))
            elif status == 1:
                self.bot.say("You don't have permission to remove an option.")
            else:
                self.bot.say("Option does not exist.")
        except Exception as error:
            self.bot.log.warn("Error in Remove Vote Option:\n{}".format(error))


class CastVote(Command):
    """ Cast Vote
        Actually place a vote in the currently existing vote. One vote
        allowed per user
    """

    def __init__(self):
        self.help = """Cast Vote Command - example 'gambit: vote for 
                       yes' Cast your opinion in the currently open 
                       vote. Only one vote is allowed per person."""
        self.help_name = "vote for"
        self.syntax = "gambit: vote for <option>"


    def parse(self, bot, message, user_priv):
        re_cast = re.compile("^gambit[:,]? vote for (.+)$", re.IGNORECASE)
        res = re_cast.match(message)
        if res is None or bot.vote is None:
            self.parsed = False
            return False
        self.cmd_args['option'] = res.groups()[0]
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info("Executing Cast Vote")
            resolved = resolve_nick(self.bot.db, self.bot.user.full_name)
            success = self.bot.vote.vote(resolved, self.cmd_args['option'])
            if success:
                self.bot.say("{} voted for {}".format(resolved, self.cmd_args['option']))
            else:
                self.bot.say("That's not an option!")
        except Exception as error:
            self.bot.log.warn("Error in Cast Vote:\n{}".format(error))


class EndVote(Command):
    """ End Vote
        Finish off the current vote and have the bot state who won
    """

    def __init__(self):
        self.help = """End Vote Command - example: 'gambit: end vote' 
                       ends the current vote if you have the right
                       permission and outputs the winner."""
        self.help_name = "end vote"
        self.syntax = "gambit: end vote"


    def parse(self, bot, message, user_priv):
        re_end = re.compile("^gambit[:,]? end vote$", re.IGNORECASE)
        res = re_end.match(message)
        if res is None or bot.vote is None:
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
            self.bot.log.info("Executing End Vote")
            winner = self.bot.vote.end_vote(self.bot, self.user_priv)
            # If everyone chose the winner of the vote to be "invalid"
            # the vote never ends, and that's kind of shitty... on the
            # other hand... who votes for "invalid"?
            if winner == 'invalid':
                self.bot.say("You don't have permission to end the vote")
                return # At least its better than voting for Trump...
            elif winner is None:
                self.bot.say("No one voted!?!? Lame, ending with no winner")
            else:
                self.bot.say("The votes are in! The winner is: {}".format(winner))
            self.bot.vote = None
        except Exception as error:
            self.bot.log.warn("Error in End Vote:\n{}".format(error))


class ShowVoteOptions(Command):
    """ Show Vote Options
        Show all options currently permitted in the vote. Hopefully
        there's more than one. I'm not if sure gambit is a legitimate
        polling system in the democratic people's republic of north
        korea.
    """

    def __init__(self):
        self.help = """Show Vote Options Command - Example 'gambit: 
                       show vote options'. Show all allowed options in 
                       the current vote."""
        self.help_name = "show vote options"
        self.syntax = "gambit: show vote options"


    def parse(self, bot, message, user_priv):
        re_show = re.compile("^gambit[:,]? show vote options$", re.IGNORECASE)
        res = re_show.match(message)
        if res is None or bot.vote is None:
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
            self.bot.log.info("Exectuing Show Vote Options.")
            response = ''
            for option in self.bot.vote.options:
                response += option + '\n'
            self.bot.say(response)
        except Exception as error:
            self.bot.log.warn("Error in Show Vote Options:\n{}".format(error))


class ShowVotes(Command):
    """ Show Votes
        Show all currently placed votes
    """

    def __init__(self):
        self.help = """Show Votes Command - Example 'gambit: show 
                       votes' Show all currently placed votes."""
        self.help_name = "show votes"
        self.syntax =  "gambit: show vote options"


    def parse(self, bot, message, user_priv):
        re_show = re.compile("^gambit[:,]? show votes$", re.IGNORECASE)
        res = re_show.match(message)
        if res is None or bot.vote is None:
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
            self.bot.log.info("Exectuing Show Votes.")
            response = ''
            for voter in self.bot.vote.votes.keys():
                response += '{} voted for {}\n'.format(voter, self.bot.vote.votes[voter])
            self.bot.say(response)
        except Exception as error:
            self.bot.log.warn("Error in Show Votes:\n{}".format(error))


class ShowVoteQuestion(Command):
    """ Show Vote Question
        State the question be decided by the current vote
    """

    def __init__(self):
        self.help = """Show Vote Question Command - Example 'gambit: 
                       show vote question' show the question being 
                       answered by the current vote."""
        self.help_name = "show vote question"
        self.syntax =  "gambit: show vote question"


    def parse(self, bot, message, user_priv):
        re_show = re.compile("^gambit[:,]? show vote question$", re.IGNORECASE)
        res = re_show.match(message)
        if res is None or bot.vote is None:
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
            self.bot.log.info("Exectuing Show Vote Question.")
            self.bot.say(self.bot.vote.question)
        except Exception as error:
            self.bot.log.warn("Error in Show Vote Question:\n{}".format(error))
