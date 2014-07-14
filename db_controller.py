import logging
import os
import sys
import json
import getpass
import datetime

sys.path.append(os.getcwd() + '/keyring')  # Strange path issue, only appears when run from local console, not IDE
sys.path.append(os.getcwd() + '/pg8000-1.08')  # Strange path issue, only appears when run from local console, not IDE
import pg8000
import keyring
from keyring.errors import PasswordDeleteError

__author__ = 'Jesse'


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


class DbConnectionManager(object, db_settings):
    def __init__(self):
        username = db_settings.USERNAME
        password = keyring.get_password(SettingsHelper.KEYRING_APP_ID, db_settings.USERNAME)
        ip_address = db_settings.IP_ADDRESS
        port = str(db_settings.PORT)
        db_name = db_settings.DATABASE
        self.connection = pg8000.DBAPI.connect(
            user=username, password=password, host=ip_address, port=port, database=db_name)
        self.cursor = self.connection.cursor()

    def __iter__(self):
        for item in self.cursor:
            yield item

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        print('exit')

        # def __exit__(self, ext_type, exc_value, traceback):
        # self.cursor.close()
        #     if isinstance(exc_value, Exception):
        #         self.connection.rollback()
        #     else:
        #         self.connection.commit()
        #     self.connection.close()


class db_helper(object, SettingsHelper):
    """ Lets users send email messages """
    # db = postgresql.open(user = 'usename', database = 'datname', port = 5432)
    # http://python.projects.pgfoundry.org/docs/1.1/

    # TODO Maybe implement other mail providers
    def __init__(self):
        self.loadSettings()
        self.PASSWORD = keyring.get_password(self.KEYRING_APP_ID, self.USERNAME)  # Loads password from secure storage

    def __create_table(self):
        DDL_Query = '''
        CREATE TABLE "public"."player_activity" (
        "Index" SERIAL NOT NULL,
        "Time_Stamp" TIMESTAMP(6) NOT NULL,
        "Player_Count" INT4,
        "Player_Names" TEXT, CONSTRAINT
        "player_activity_pkey"
        PRIMARY KEY ("Index"))'''

        # TODO Execute on first run

    # noinspection PyMethodMayBeStatic
    def test_login(self):
        """ Gets run on startup """
        # with DbConnectionManager as cur:
        # cur.execute('SELECT * FROM player_activity')


        connection = pg8000.DBAPI.connect(
            user='postgres', password='test', host='192.168.1.165', database='player_stats')
        cursor = connection.cursor()
        cursor.execute('INSERT INTO player_activity ("Time_Stamp", "Player_Count", "Player_Names") VALUES (?, ?, ?);'),(datetime.datetime.today(),4,'jelloeater, Kalgaren')
        cursor.execute('SELECT * FROM player_activity')
        print(cursor.fetchall())


        # try:
        #     with DbConnectionManager as c:
        #         c('SELECT * FROM player_activity')
        # except:
        #     print("DB Access Error")
        #     sys.exit(1)


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


