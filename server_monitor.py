#!/usr/bin/env python2.7
"""A python project for managing Minecraft servers hosted on MineOS (http://minecraft.codeemo.com)
"""

import sys
import os
import logging
import argparse
from time import sleep
import subprocess
import db_controller

sys.path.append('/usr/games/minecraft')  # Strange path issue, only appears when run from local console, not IDE

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
        print('Debug Mode Enabled')
    else:
        logging.basicConfig(filename=LOG_FILENAME,
                            format="[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
                            level=logging.WARNING)
        print('Normal Boot')

    mode = modes(base_directory=args.base_directory, owner=args.owner, sleep_delay=args.delay)
    # Create new mode object for flow, I'll buy that :)

    if len(sys.argv) == 1:  # Displays help and lists servers (to help first time users)
        parser.print_help()
        sys.exit(1)

    if args.list:
        mode.list_servers()

    if args.remove_password_store:
        db_controller.db_helper().clear_password_store()

    if args.configure_db_settings:
        db_controller.db_helper().configure()

    db_controller.db_helper().test_db_setup()
    logging.error('hi')

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
        logging.debug("Modes obj created" + str(self.base_directory) + '  ' + str(self.owner))

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
                server_logger(server_name=i, owner=self.owner, base_directory=self.base_directory).check_server_status()
            self.sleep()

    def multi_server(self):
        print("Multi Server mode")
        print("Press Ctrl-C to quit")

        while True:
            server_list = mc.list_servers(self.base_directory)
            logging.debug(server_list)

            for i in server_list:
                server_logger(server_name=i, owner=self.owner, base_directory=self.base_directory).check_server_status()
            self.sleep()

    def single_server(self, server_name):
        print("Single Server Mode: " + server_name)
        print("Press Ctrl-C to quit")

        while True:
            logging.debug(self.owner)
            server_logger(server_name=server_name, owner=self.owner,
                          base_directory=self.base_directory).check_server_status()
            self.sleep()


class server_logger(mc):
    def check_server_status(self):
        if self.up and self.ping[3] > 0:  # Server is up and has players
            logging.info("Checking server {0}".format(self.server_name))
            self.send_active_players()

    def send_active_players(self):
        logging.debug(self.ping[3])  # number of player
        logging.debug('PID: ' + str(self.screen_pid))
        # self._command_stuff('/say lol')

        # FIXME Command not working, but attaching to screen
        # See http://www.cyberciti.biz/faq/python-run-external-command-and-get-output/

        logging.debug(os.getcwd())

        cmd = 'screen -r ' + str(self.screen_pid) + ' -X /list'
        # cmd = 'ls'
        # os.system(cmd)
        process = subprocess.Popen(cmd)
        (output, err) = process.communicate()
        logging.debug('Output: ' + str(output))
        logging.debug('Err: ' + str(err))
        status_code = process.wait()
        logging.debug('Status Code: ' + str(status_code))


        # TODO Should send player list to db_helper.log_active_players_to_db





if __name__ == "__main__":
    main()

