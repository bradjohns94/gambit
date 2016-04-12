# Gambit - Google Hangouts Bot

A very scalable chat bot built off of tdryer's hangups client
(https://github.com/tdryer/hangups).

At the moment, Gambit is implemented through a hacky insertion to the hangups UI files,
but an installation file with a more elegant solution will hopefully be developed in
the next few months for the sake of portability if nothing else.

## Configuration

You should notice that Gambit comes with 3 main files and a "commands" subdirectory:
- `gambit.py` - the bot's main file which processes and runs all commands
- `admins.txt` - a list of high-privilege users who can list admin commands, each line
should represent a different administrator for the bot.
- `schema.sql` - the layout of the bot's database. If nothing else, this will be used
for installation sequences when that's implemented

Of these 3 files, the only one you should ever really need to edit is the admins.txt
file to incorporate the names of any administrators for the bot.

## Commands

Nothing in the commands subdirectory is required for the functionality of the bot with 
the exception of `command.py` itself, which is the prototype structure which all future
commands must follow. That being said, gambit comes with a wide array of commands that
I've worked pretty hard on making. If you want a list of all commands, you can enter
a conversation with the bot and say "gambit: list commands" to see all currently
available commands. Note that there are commands that are closer to easter eggs
(wat, it's a trap, etc.) which will not show up in that command list. Most, if not all,
of these easter eggs are in `exclaim.py`.

Below is a list of the general theme of commands incuded in each file:
- `user.py` - Gambit, by default, loads all unique user id/conversation id pairs that
he can map a name to into his database. That being said, many commands rely on users
having "nicknames" to make resolving users a little bit more natural. Thus, this file
contains administrative commands to give users nicknames and resolve users who hangups
can't match a name to, "Unknown"s.
- `list.py` - Contains any commands used to list off other commands (except help)
- `help.py` - Contains commands which assist users in understanding how to use other
commands
- `karma.py` - Contains commands which pertain to a user's "karma". An internet point
system which the bot associates with its users
- `alias.py` - Sometimes people will refer to things differently, alias commands help
the bot identify them as the same reference.
- `exclaim.py` - Contains commands that make the bot say random things. Like dad jokes!
- `highlow.py` - Contains the command to have users bet their internet points on the
dice game "high-low"
- `privilege.py` - All commandsare assigned a level of "privilege" which defaults to 0
unless otherwise specified (admin commands have a privilege of infinity)
- `quotes.py` - Commands that will store the last message sent by a given user forever
- `vote.py` - Commands that are used for implementing the democratic process over
group chat. Ties are resolved with internet points, because it seems more reasonable
than super delegates.
- `util.py`- Doesn't actually contain any commands, but there are a lot of useful
functions to be run by commands.

## Creating New Commands

Creating new commands is amazingly simple! All you need to do is create a python file
with a class that extends the Command class in `command.py`. Commands have 5 major
components, but only 2 of them are actually required to execute properly:

- **parse() (required)** - a method which takes a reference to Gambit, the recieve
message, and the privilege of the user that sent the message. parse() is expected to
load all needed arguments to run the command into self.cmd_args, a dictionary which 
gets cleared after ever message, and return whether or not the recieved message should 
actually trigger the command.
- **execute() (required)** - a method which actually runs the desired result of the 
command. Gambit should *probably* say something at the end of this method, but that isn't required.
- **syntax** - a class-level string which contains the syntax to run the command. This
is what gets printed out in "list commands"
- **help** - a class-level string of help text to explain to users how to use the
command. This gets printed out when someone runs "help" on the command in question.
- **help_name** - a class-level string containing a shorter or more natural name for
the command. Kind of like an alias for the command name itself.

Below should be sample code to get you started on creating a new command:

```
from hangups.bot.commands.command import Command # import the command class

class TestCommand(Command):
    """ Test Command
        You should put some helpful text here to explain your command
    """
    
    def __init__(self):
        self.help = "An explanation of how to use the command"
        self.help_name = "test command"
        self.syntax = "gambit: do a barrel roll! <arg1> <arg2>"
    
    
    def parse(self, bot, message, user_priv):
        # Determine whether or not the message triggers the command here
        self.bot = bot
        self.user_priv = user_priv
        self.parsed = was_it_valid
        self.cmd_args['example'] = 42
        return was_it_valid


    def execute(self):
        # Actually run your command
        self.bot.say("I did it!")
```

## Questions?

If there's anything unclear or broken with Gambit, feel free to open an issue, post
a message, or send me an email at BradJohns94@gmail.com! I'm happy to help in any
way I can.
