#!/usr/bin/env python2.7
"""A python project for managing Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""

import sys
import os
import json
import getpass
import logging
import argparse
from time import sleep


sys.path.append(os.getcwd() + '/keyring')  # Strange path issue, only appears when run from local console, not IDE
sys.path.append(os.getcwd() + '/postgres')  # Strange path issue, only appears when run from local console, not IDE
sys.path.append('/usr/games/minecraft')  # Strange path issue, only appears when run from local console, not IDE

import keyring
from keyring.errors import PasswordDeleteError

from mineos import mc

__author__ = "Jesse S"
__license__ = "GNU GPL v2.0"
__version__ = "1.0"
__email__ = "jelloeater@gmail.com"

LOG_FILENAME = "serverMonitor.log"


def main():
    """ Take arguments and direct program """
    parser = argparse.ArgumentParser(description="A MineOS Player Stats Monitor"
                                                 " (http://github.com/jelloeater/mineOSplayerStats)",
                                     version=__version__,
                                     epilog="Please specify mode (-s, -i or -m) to start monitoring")
    server_group = parser.add_argument_group('Single Server Mode')
    server_group.add_argument("-s",
                              "--single",
                              action="store",
                              help="Single server watch mode")
    interactive_group = parser.add_argument_group('Interactive Mode')
    interactive_group.add_argument("-i",
                                   "--interactive",
                                   help="Interactive menu mode",
                                   action="store_true")
    multi_server_group = parser.add_argument_group('Multi Server Mode')
    multi_server_group.add_argument("-m",
                                    "--multi",
                                    help="Multi server watch mode",
                                    action="store_true")

    email_group = parser.add_argument_group('E-mail Alert Mode')
    email_group.add_argument("-c",
                             "--configure_db_settings",
                             help="Configure email alerts",
                             action="store_true")
    email_group.add_argument("-r",
                             "--remove_password_store",
                             help="Removes password stored in system keyring",
                             action="store_true")

    parser.add_argument("-d",
                        "--delay",
                        action="store",
                        type=int,
                        default=60,
                        help="Wait x second between checks (ex. 60)")
    parser.add_argument('-b',
                        dest='base_directory',
                        default='/var/games/minecraft',
                        help='Change MineOS Server Base Location (ex. /var/games/minecraft)')
    parser.add_argument('-o',
                        dest='owner',
                        default='mc',
                        help='Sets the owner of the Minecraft servers (ex mc)')
    parser.add_argument("-l",
                        "--list",
                        action="store_true",
                        help="List MineOS Servers")
    parser.add_argument("--debug",
                        action="store_true",
                        help="Debug Mode Logging")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.DEBUG)
        logging.debug(sys.path)
        logging.debug(args)
        print("")
    else:
        logging.basicConfig(filename=LOG_FILENAME,
                            format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.WARNING)

    mode = modes(base_directory=args.base_directory, owner=args.owner, sleep_delay=args.delay)
    # Create new mode object for flow, I'll buy that :)

    if len(sys.argv) == 1:  # Displays help and lists servers (to help first time users)
        parser.print_help()
        sys.exit(1)

    if args.list:
        mode.list_servers()

    if args.remove_password_store:
        db_helper().clear_password_store()
    if args.configure_db_settings:
        db_helper().configure()

    db_helper().test_login()

    # Magic starts here
    if args.interactive:
        mode.interactive()
    elif args.single:
        mode.single_server(args.single)  # Needs server name to start
    elif args.multi:
        mode.multi_server()


class modes(object):  # Uses new style classes
    def __init__(self, base_directory, owner, sleep_delay):
        self.base_directory = base_directory
        self.sleep_delay = sleep_delay
        self.owner = owner  # We NEED to specify owner or we get a error in the webGUI during start/stop from there

    def sleep(self):
        try:
            sleep(self.sleep_delay)
        except KeyboardInterrupt:
            print("Bye Bye.")
            sys.exit(0)

    def list_servers(self):
        print("Servers:")
        print("{0}{1}".format("Name".ljust(20), 'State'))
        for i in mc.list_servers(self.base_directory):
            print "{0}{1}".format(i.ljust(20), ['down', 'up'][mc(i).up])

    def interactive(self):
        servers_to_monitor = []
        print("Interactive Mode")

        while True:
            self.list_servers()
            print("\n\nCurrently Monitoring: {0}\n".format(', '.join(servers_to_monitor)))
            print("Type name of server to monitor. Enter (d/done) when finished.")
            server_name = raw_input(">")

            if server_name.lower() in ['done', 'd', ''] and servers_to_monitor:
                break  # Only exits if we have work to do
            elif server_name in mc.list_servers(self.base_directory):  # Checks if name is valid
                servers_to_monitor.append(server_name)

        logging.info("Starting monitor")

        while True:
            for i in servers_to_monitor:
                server_logger(server_name=i, owner=self.owner, base_directory=self.base_directory).check_server()
            self.sleep()

    def multi_server(self):
        print("Multi Server mode")
        print("Press Ctrl-C to quit")

        while True:
            server_list = mc.list_servers(self.base_directory)
            logging.debug(server_list)

            for i in server_list:
                server_logger(server_name=i, owner=self.owner, base_directory=self.base_directory).check_server()
            self.sleep()

    def single_server(self, server_name):
        print("Single Server Mode: " + server_name)
        print("Press Ctrl-C to quit")

        while True:
            logging.debug(self.owner)
            server_logger(server_name=server_name, owner=self.owner, base_directory=self.base_directory).check_server()
            try:
                pass
            except RuntimeWarning:
                print("Please enter a valid server name")
                break
            self.sleep()


class server_logger(mc):
    def check_server(self):
        logging.info("Checking server {0}".format(self.server_name))
        logging.debug("Server {0} is {1}".format(self.server_name,
                                                 ['Down', 'Up'][self.up]))

        if self.up:
            self.send_active_players()

    def send_active_players(self):
        logging.info("Checking Server: " + self.server_name)
        logging.debug(str(self._base_directory) + '  ' + str(self.owner))
        # TODO Should send player list to db_helper.log_active_players_to_db


class db_settings():
    """ Container class for load/save """
    USERNAME = ''
    # Password should be stored with keyring
    IP_ADDRESS = ''
    PORT = 5432
    DATABASE = ''


class SettingsHelper(db_settings):
    SETTINGS_FILE_PATH = "settings.json"
    KEYRING_APP_ID = 'mineOSPlayerStats'

    @classmethod
    def loadSettings(cls):
        if os.path.isfile(cls.SETTINGS_FILE_PATH):
            try:
                with open(cls.SETTINGS_FILE_PATH) as fh:
                    db_settings.__dict__ = json.loads(fh.read())
            except ValueError:
                logging.error("Settings file has been corrupted, reverting to defaults")
                os.remove(cls.SETTINGS_FILE_PATH)
        logging.debug("Settings Loaded")

    @classmethod
    def saveSettings(cls):
        with open(cls.SETTINGS_FILE_PATH, "w") as fh:
            fh.write(json.dumps(db_settings.__dict__, sort_keys=True, indent=0))
        logging.debug("Settings Saved")


class db_helper(object, SettingsHelper):
    """ Lets users send email messages """
    # db = postgresql.open(user = 'usename', database = 'datname', port = 5432)
    # http://python.projects.pgfoundry.org/docs/1.1/

    # TODO Maybe implement other mail providers
    def __init__(self):
        self.loadSettings()
        self.PASSWORD = keyring.get_password(self.KEYRING_APP_ID, self.USERNAME)  # Loads password from secure storage


    def test_login(self):
        try:
            pass
            # TODO write db test code
        except:
            print("DB Login Error")
            sys.exit(1)

    def log_active_players_to_db(self, players_list):
        """ Takes active players and logs list to db with timestamp """
        pass

    def configure(self):

        print("Enter database username (postgres) or press enter to skip")
        username = raw_input('({0})>'.format(self.USERNAME))
        if username:
            db_settings.USERNAME = username

        print("Enter database password or press enter to skip")
        password = getpass.getpass(
            prompt='>')  # To stop shoulder surfing
        if password:
            keyring.set_password(self.KEYRING_APP_ID, self.USERNAME, password)

        print("Enter database server IP Address to edit (127.0.0.1) or press enter to skip")
        ip_address = raw_input('({0})>'.format(self.IP_ADDRESS))
        if username:
            db_settings.IP_ADDRESS = ip_address

        print("Enter database server port to edit (playerStats) or press enter to skip")
        port = raw_input('({0})>'.format(str(self.PORT)))
        if username:
            db_settings.PORT = int(port)

        print("Enter database name to edit (playerStats) or press enter to skip")
        database = raw_input('({0})>'.format(self.DATABASE))
        if username:
            db_settings.DATABASE = database

        self.saveSettings()

    def clear_password_store(self):
        try:
            keyring.delete_password(self.KEYRING_APP_ID, self.USERNAME)
            print("Password removed from Keyring")
        except PasswordDeleteError:
            logging.error("Password cannot be deleted or already has been removed")


if __name__ == "__main__":
    main()

