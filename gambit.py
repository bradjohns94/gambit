import asyncio
import hangups
import logging
import re
import sqlite3
import os
import sys
import glob
import importlib
import inspect

from hangups.bot.commands.command import Command
from hangups.bot.commands import *

class Gambit:
    """ Gambit Hangouts Bot
        A google hangouts chat bot, currently implemented via a kind of hacky
        funnel through the "Hangups" client (https://github.com/tdryer/hangups).
        All commands read into the client are processed through a list of
        classes implementing the "Command" interface and then parsed into bot
        responses
    """
    # Declare class level variables
    admins = []
    user_priv = {}
    # TODO make these configurable
    root_dir = "/usr/local/lib/python3.4/dist-packages/hangups/"
    bot_src = root_dir + "bot/"
    image_src = bot_src + "images/"
    log_dir = "/var/"
    vote = None
    last_message = {}
    ids = {}
    cmd_list = {}

    def __init__(self, client, conversation_list):
        """ init
            Start up all class level variables for the bot instance for future
            use
        """
        try:
            # Set up logging
            self.log = logging.getLogger('gambit')
            handler = logging.FileHandler(self.log_dir + 'gambit.log')
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            handler.setFormatter(formatter)
            self.log.addHandler(handler)
            self.log.setLevel(logging.INFO)
            # Initialize the database
            self.log.info('Connecting to gambit.db...')
            self.db = sqlite3.connect(self.bot_src + 'gambit.db')
            # Specify our initial state
            self.karma = {}
            for conversation in conversation_list.get_all():
                self.karma[conversation.id_] = True
            self.update_users(conversation_list.get_all())
            self.client = client
            self.conv_list = conversation_list
            # Add our commands to the command list
            self.init_commands()
            self.load_admins()
        except Exception as error:
            if 'log' in dir(self):
                self.log.warn('Error while initializing:\n{}'.format(error))


    def init_commands(self):
        """ Init Commands
            Import any classes in the command directory that extends
            the command superclass and add them to the command list
        """
        command_directory = os.path.join(os.path.dirname(os.path.abspath(self.bot_src + 'commands/command.py')))
        sys.path.append(command_directory)
        for file in glob.glob(command_directory + '/*.py'):
            name = os.path.splitext(os.path.basename(file))[0]
            # Filter out __ files
            if name.startswith('__'):
                continue
            module = importlib.import_module(name)
            for member in dir(module):
                # We don't want to have the Command class in our list
                if member == 'Command': continue
                handler_class = getattr(module, member)
                # Handle weird cases to make sure its a command
                if not inspect.isclass(handler_class): continue
                if not issubclass(handler_class, Command): continue
                if handler_class:
                    # Add the command to the database if it's not already there
                    exists = self.db.execute("SELECT COUNT(*) FROM commands WHERE name = ?", 
                            (handler_class.__name__,))
                    exists = exists.fetchone()[0] > 0
                    if not exists:
                        self.db.execute("INSERT INTO commands (name) VALUES (?)",
                                (handler_class.__name__,))
                        self.db.commit()
                    cmd_priv = self.db.execute("SELECT privilege FROM commands WHERE name == ?", 
                            (handler_class.__name__,))
                    cmd_priv = cmd_priv.fetchone()[0]
                    self.cmd_list[handler_class()] = cmd_priv
    

    def load_admins(self):
        """ Load Admins
            Populate the bot-level admin list with the contents of the
            admins.txt file
        """
        admins_file = open(self.bot_src + 'admins.txt')
        for admin in admins_file.readlines():
            self.admins.append(admin.replace('\n',''))


    def reply(self, user, message, conversation):
        """ reply
            Take information gathered from the hangups modification to get
            the last message sent, the user who sent it, and the conversation
            it was set over, then prepare the bot to process and respond to
            what was said
        """
        try:
            self.user = user
            self.message = message
            self.conversation = conversation
            if self.user.full_name == 'Unknown':
                db_user = self.db.execute("SELECT full_name FROM users WHERE user_id = ? AND conversation_id = ?",
                        (user.id_[0], conversation.id_))
                db_user = db_user.fetchall()
                if len(db_user) > 0:
                    user.full_name = db_user[0][0]
                    user.first_name = db_user[0][0].split(' ')[0]
            self.log.info('Received message:')
            self.log.info('\tuser: {}'.format(self.user.full_name))
            self.log.info('\tmessage: {}'.format(self.message))
            if user.is_self: return # Ignore responses from the bot itself
            self.process_request()
        except Exception as error:
            self.log.warn('Error parsing message:\n{}'.format(error))


    def process_request(self):
        """ Process Request
            Look through the bot's list of commands and determine which, if
            any, the last message sent matches. If a match is found, execute
            the command
        """
        user_priv = 0
        res = self.db.execute("SELECT privilege FROM users WHERE user_id = ? AND conversation_id = ?",
                              (self.user.id_[0], self.conversation.id_)).fetchall()
        if len(res) > 0:
            user_priv = res[0][0]
        if self.user.full_name in self.admins: user_priv = float('inf')
        was_cmd = False
        for cmd in self.cmd_list.keys():
            try:
                is_valid = cmd.parse(self, self.message, user_priv)
                was_cmd |= is_valid
                if is_valid:
                    if cmd.cmd_priv != float('inf'):
                        cmd.cmd_priv = self.cmd_list[cmd]
                    cmd.execute()
                cmd.cmd_args = {} # Clear the arguments
                cmd.parsed = False
            except Exception as error:
                self.log.warn("Error: {} in command {}. Ignoring.".format(error, cmd.__class__.__name__))
        # Add the message to the last message dictionary
        self.last_message[self.user.full_name] = self.message
        # Map user name to ID for resolving unknowns
        if self.conversation.id_ not in self.ids.keys():
            self.ids[self.conversation.id_] = {}
        self.ids[self.conversation.id_][self.user.full_name] = self.user.id_[0]


    def say(self, text, conversation=None):
        """ Say
            Output some set of text in a specified (or most recent) conversation
        """
        if not conversation:
            conversation = self.conversation
        if len(text) == 0:
            return
        elif text.startswith('/image') and len(text.split(' ')) == 2:
            filename = text.split(' ')[1]
            image_file = open(filename, 'rb')
            text = ''
        else:
            image_file = None
        segments = hangups.ChatMessageSegment.from_str(text)
        asyncio.async(
            conversation.send_message(segments, image_file=image_file)
        ).add_done_callback(self._on_message_sent)


    def send_private_message(self, user, text):
        """ Send Private Message
            Send an individual user in a conversation a private message
        """
        try:
            self.log.info("Attempting to send private message")
            conv = get_private_conversation(self, user)
            if not conv: # There's no pre-existing conversation
                """
                self.log.info("Resolving chat ids")
                ids = [self.get_gambit_user_id(), user.id_.chat_id]

                self.log.info("Creating conversation")
                conv = self.client.createconversation(ids, force_group=True)
                conv_id = conv['conversation']['id']['id']
                self.log.info("Conversation created")
                conv = self.conv_list.get(conv_id)
                """
                # We'll leave this commented in case we figure out a way to do it
                self.log.info("Conversation does not yet exist with user")
                self.say("You need to message me first!")
                return
            self.log.info("Sending PM")
            self.say(text, conv)
        except Exception as err:
            self.log.warn("Failed to send private message:\n{}".format(err))


    def update_conv_list(self, conv_list):
        """ Update Conversation List
            Revise what conversations the bot is part of
        """
        self.conv_list = conv_list
        self.update_users(conv_list.get_all())


    def update_users(self, conversations):
        """ Update Users
            Given a list of conversations - add any users the bot
            is not yet familiar other than 'Unknown's to the database
        """
        for conversation in conversations:
            for user in conversation.users:
                exists = self.db.execute("SELECT COUNT(*) FROM users WHERE user_id = ? AND conversation_id = ?", (user.id_[0], conversation.id_,))
                exists = exists.fetchone()[0] > 0
                if user.full_name == 'Unknown' or user.full_name == 'Gambit Bot':
                    continue
                if not exists: # Add the user to the database
                    self.db.execute("INSERT INTO users (user_id, conversation_id, full_name) VALUES(?, ?, ?)", (user.id_[0], conversation.id_, user.full_name,))
                    self.db.commit()


    def _on_message_sent(self, future):
        """ On Message Sent
            Catch whether or not the last message sent properly
        """
        try:
            future.result()
        except Exception as err:
            self.log.warn('Failure when sending message:\n{}'.format(err))
