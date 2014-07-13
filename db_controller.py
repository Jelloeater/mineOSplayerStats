import logging
import os
import sys
import json
import getpass
sys.path.append(os.getcwd() + '/keyring')  # Strange path issue, only appears when run from local console, not IDE
sys.path.append(os.getcwd() + '/postgres')  # Strange path issue, only appears when run from local console, not IDE
import postgresql
import keyring
from keyring.errors import PasswordDeleteError

__author__ = 'Jesse'


class DbConnectionManager():
    def __init__(self, dbCursor):
        self.dbCursor = dbCursor

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Cursor(object):
    def __init__(self,
                 cursorclass=Cursor,
                 host=config.HOST, user=config.USER,
                 passwd=config.PASS, dbname=config.MYDB,
                 driver=MySQLdb,
    ):
        self.cursorclass = cursorclass
        self.host = host
        self.user = user
        self.passwd = passwd
        self.dbname = dbname
        self.driver = driver
        self.connection = self.driver.connect(
            host=host, user=user, passwd=passwd, db=dbname,
            cursorclass=cursorclass)
        self.cursor = self.connection.cursor()

    def __iter__(self):
        for item in self.cursor:
            yield item

    def __enter__(self):
        return self.cursor

    def __exit__(self, ext_type, exc_value, traceback):
        self.cursor.close()
        if isinstance(exc_value, Exception):
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()


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