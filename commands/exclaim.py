import re
from random import randint
from urllib import parse, request
from bs4 import BeautifulSoup

from util import *
from hangups.bot.commands.command import Command

class SayHi(Command):
    """ Say Hi
        Respond to a greeting with a greeting
    """

    greetings = ["hi", "hello", "hey", "howdy", "salutations",
                 "greetings", "'ello", "hola"]

    def parse(self, bot, message, user_priv):
        exp = re.compile("^(.+)[:,]? gambit[.!?]?$", re.IGNORECASE)
        res = exp.match(message)
        if res is None or res.groups()[0].lower() not in self.greetings:
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
            self.bot.log.info("Executing Say Hi")
            greeting = self.greetings[randint(0, len(self.greetings)-1)]
            username = get_honorific_name(self.bot.db, self.bot.user.full_name, self.bot.conversation.id_)
            self.bot.say("{}, {}!".format(greeting.capitalize(), username))
        except Exception as error:
            self.bot.log.warn("Error in Say Hi:\n{}".format(error))



class SayURL(Command):
    """ Say URL
        Respond to text containing a URL with the link title
    """

    def parse(self, bot, message, user_priv):
        self.parsed = False
        pieces = parse.urlparse(message)
        if pieces.hostname:
            self.bot = bot
            self.user_priv = user_priv
            self.message = message
            self.parsed = True
        return self.parsed


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info('Executing Say URL')
            res = request.urlopen(self.message)
            html = res.read()
            soup = BeautifulSoup(html)
            title = soup.html.head.title.text
            self.bot.say(title)
        except Exception as error:
            self.bot.log.warn('Error in Say URL:\n{}'.format(error))


class Substitute(Command):
    """ Substitute
        Perform vim-like substitution on the last message someone
        sent on a chat with the bot
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile('^s\/(.+)\/(.+)$')
        res = exp.match(message)
        if res is None:
            self.parsed = False
            return False
        before, after = res.groups()
        self.cmd_args['before'] = before
        self.cmd_args['after'] = after
        self.message = message
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = True
        return True


    def execute(self):
        if not self.parsed: return
        if self.user_priv < self.cmd_priv: return
        try:
            self.bot.log.info('Executing Substitute')
            if self.bot.user.full_name not in self.bot.last_message.keys():
                return
            last = self.bot.last_message[self.bot.user.full_name]
            msg = None
            if last.find(self.cmd_args['before']) != -1:
                msg = last.replace(self.cmd_args['before'], self.cmd_args['after'])
            elif last.find(before.lower() != -1):
                msg = last.replace(self.cmd_args['before'].lower(), self.cmd_args['after'])
            if msg:
                username = get_honorific_name(self.bot.db, self.bot.user.full_name, self.bot.conversation.id_)
                self.bot.say(username + ' MEANT to say: ' + msg)
        except Exception as error:
            self.bot.log.warn('Error in Substitute:\n{}'.format(error))


class TellDadJoke(Command):
    """ Tell Dad Joke
        Have the bot sit down in his laz-y-boy recliner, grow a
        moustache right out of 1976, and share some of his corny,
        non-offensive, punny humor
    """

    def __init__(self):
        self.help = """Dad Joke Command - Example: 'Gambit: dad joke' 
                       Tells a horrible dad joke."""
        self.help_name = "dad joke"
        self.syntax = "gambit: dad joke"


    def parse(self, bot, message, user_priv):
        exp = re.compile('^(?:gambit[:,]?)?\s?dad\s?joke.?$', re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Tell Dad Joke')
            res = self.bot.db.execute("SELECT joke FROM jokes WHERE type = 'dad'")
            jokes = res.fetchall()
            joke = jokes[randint(0, len(jokes) - 1)][0]
            self.bot.say(joke)
        except Exception as error:
            self.bot.log.warn('Error in Tell Dad Joke\n{}'.format(error))


class SayWat(Command):
    """ Say Wat
        Have the bot display one of the lovely images from the destroy
        all software talk
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile("^.*(^|\W)wat($|\W).*$", re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Say Wat')
            filenames = ['watduck.jpg', 'wathorse.jpg', 'wat.jpeg', 'watman.jpg']
            image_file = self.bot.image_src + filenames[randint(0, len(filenames)-1)]
            self.bot.say('/image ' + image_file)
        except Exception as error:
            self.bot.log.warn('Error in Say Wat\n{}'.format(error))


class SayItsATrap(Command):
    """ Say It's a Trap
        Help someone share that they've made a mistake as dire as
        leading a rebel fleet against the second death star
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile("^.*(^|\W)IT'?S A TRAP($|\W).*$", re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Its A Trap')
            filenames = ['hopeitsatrap.jpg', 'itsafrappe.jpg', 'itsaruse.jpeg', 'itsatrap.jpg']
            image_file = self.bot.image_src + filenames[randint(0, len(filenames)-1)]
            self.bot.say('/image ' + image_file)
        except Exception as error:
            self.bot.log.warn('Error in Its A Trap\n{}'.format(error))


class FuckGrails(Command):
    """ Fuck Grails
        'Rails on the JVM, need I say more?' - William Doyle
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile("^.*(^|\W)grails($|\W).*$", re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Fuck Grails')
            image_file = self.bot.image_src + 'grails.png'
            self.bot.say('/image ' + image_file)
        except Exception as error:
            self.bot.log.warn('Error in Fuck Grails\n{}'.format(error))


class TellGoodNews(Command):
    """ Tell Good News
        'Good news everyone! Several years ago I tried to log on to
         AOL, and it just went through! Wheee! We're online!'
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile("^.*(^|\W)good news($|\W).*$", re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Tell Good News')
            image_file = self.bot.image_src + 'goodnews.jpg'
            self.bot.say('/image ' + image_file)
        except Exception as error:
            self.bot.log.warn('Error in Tell Good News\n{}'.format(error))


class SpoilerAlert(Command):
    """ Spoiler Alert
        Vroom VROOM. Yay spoilers.
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile("^.*(^|\W)spoiler alert($|\W).*$", re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Spoiler Alert')
            image_file = self.bot.image_src + 'Spoilers.jpg'
            self.bot.say('/image ' + image_file)
        except Exception as error:
            self.bot.log.warn('Error in Tell Spoiler Alert\n{}'.format(error))


class TellItToTheCleaningLadyOnMonday(Command):
    """ Tell it to the Cleaning Lady on Monday
        Quote the great wisdom of vegan/psychc Todd Ingram, third evil
        ex boyfriend featured in Bryan Lee O'Malley's:
        'Scott Pilgrim and the Infinite Sadness'
        Side-effects may include wanting to eat gelato and having your
        corpse burst into change.
        (P.S. Gelato isn't vegan. It's got milk and eggs, bitch)
        (P.S.S. Gambit is technically vegan!)
    """

    def parse(self, bot, message, user_priv):
        exp = re.compile("^.*(^|\W)cleaning lady($|\W).*$", re.IGNORECASE)
        res = exp.match(message)
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
            self.bot.log.info('Executing Tell it to the Cleaning Lady on Monday')
            self.bot.say("Tell it to the cleaning lady on Monday.")
            self.bot.say("Because you'll be dust by Monday...")
            self.bot.say("Because you'll be pulverized in two seconds...")
            self.bot.say("The cleaning lady? She cleans up... dust. She dusts.")
            self.bot.say("'Cause... it's Friday now, and she has the weekends off, so...")
            self.bot.say("Monday... right?")
        except Exception as error:
            self.bot.log.warn('Error in Tell it to the Cleaning Lady on Monday\n{}'.format(error))


class WOTSwear(Command):
    """ Wheel of Time Swear
        Outburst one of the colorful cursesfrom Robert Jordan's
        'Wheel of Time' series
    """

    def parse(self, bot, message, user_priv):
        if 'light!' not in message.lower():
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
            self.bot.log.info("Executing WOT Swear")
            swears = ["Blood and bloody ashes!",
                      "Mother's milk in a cup!",
                      "Oh sheep swallop!",
                      "Bloddy buttered onions!",
                      "You wool-headed buffoon!",
                      "You hairy lummox!",
                      "You milk-hearted wetlander!",
                      "You bloody ox of a thimble-brained man!"]
            self.bot.say(swears[randint(0, len(swears)-1)])
        except Exception as error:
            self.bot.log.warn('Error in WOT Swear\n{}'.format(error))
