import logging
import os
import sys
import json
import getpass
import datetime

sys.path.append(os.getcwd() + '/keyring')  # Strange path issue, only appears when run from local console, not IDE
sys.path.append(os.getcwd() + '/pg8000-1.08')  # Strange path issue, only appears when run from local console, not IDE
import pg8000
from pg8000 import errors
import keyring
from keyring.errors import PasswordDeleteError

__author__ = 'Jesse'


class db_settings():
    """ Container class for load/save """
    USERNAME = 'postgres'
    # Password should be stored with keyring
    DB_HOST = '127.0.0.1'
    PORT = 5432
    DATABASE = 'player_stats'


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


class DBConnection(object):
    def __init__(self, context):
        pass


    def __del__(self):
        print 'WithinContext.__del__'


class DbConnectionManager(object):

    @staticmethod
    def get_db_objs(self):
        self.connection = pg8000.DBAPI.connect(
            user=db_settings.USERNAME,
            password=keyring.get_password(SettingsHelper.KEYRING_APP_ID, db_settings.USERNAME),
            host=db_settings.DB_HOST,
            port=str(db_settings.PORT),
            database=db_settings.DATABASE)
        self.cursor = self.connection.cursor()
        return self.connection.cursor

    def __enter__(self):

        return self.get_db_objs(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if isinstance(exc_val, Exception):
            self.connection.rollback()
        else:
            self.connection.commit()
            self.connection.close()
            logging.debug('Closed DB Connection')


class db_helper(object, SettingsHelper):
    """ Lets users send email messages """
    # db = postgresql.open(user = 'usename', database = 'datname', port = 5432)
    # http://python.projects.pgfoundry.org/docs/1.1/

    # TODO Maybe implement other mail providers
    def __init__(self):
        self.loadSettings()
        self.PASSWORD = keyring.get_password(self.KEYRING_APP_ID, self.USERNAME)  # Loads password from secure storage

    def _create_database(self):
        """ Creates the database using template1 """
        try:
            try:
                logging.info("Check if Database Exists")
                connection = pg8000.DBAPI.connect(
                    user=self.USERNAME, password=self.PASSWORD, host=self.DB_HOST, database='template1')
                cursor = connection.cursor()
                connection.autocommit = True
                cursor.execute('''CREATE DATABASE player_stats''')
                connection.close()
            except errors.ProgrammingError:
                logging.info('Database (Player_Stats) Already Exists')
        except pg8000.errors.InterfaceError:
            logging.error("DB Connection Interface Error")
            print('Please check the user settings')

    def __create_table(self):
        DDL_Query = '''
        CREATE TABLE player_activity (
        "Index" SERIAL NOT NULL,
        "Time_Stamp" TIMESTAMP(6) NOT NULL,
        "Player_Count" INT4,
        "Player_Names" TEXT,
        "Server_Name" TEXT,
        CONSTRAINT "player_activity_pkey"
        PRIMARY KEY ("Index"))'''

        # TODO Execute on first run

    # noinspection PyMethodMayBeStatic
    def test_login(self):
        """ Gets run on startup """
        # with DbConnectionManager as cur
        # cur.execute('SELECT * FROM player_activity')
        logging.debug(db_settings.__dict__)
        logging.debug(datetime.datetime.today())
        logging.debug(keyring.get_password(SettingsHelper.KEYRING_APP_ID, db_settings.USERNAME))

        insert_query = 'INSERT INTO player_activity ("Time_Stamp","Player_Count","Player_Names","Server_Name") \
                        VALUES (%s, %s, %s,%s)', (datetime.datetime.now(), 16, 'jelloeater', 'MagicFarm')

        with DbConnectionManager as conn:
            conn.execute(insert_query)
            conn.execute('SELECT * FROM player_activity')
            logging.debug(conn.fetchall())




            # connection = pg8000.DBAPI.connect(
            # user='postgres', password='test', host='192.168.1.165', database='player_stats')
            # cursor = connection.cursor()
            #
            #

            # connection.commit()



            # FIXME Get insert statement working



            # try:
            # with DbConnectionManager as c:
            # c('SELECT * FROM player_activity')
            # except:
            # print("DB Access Error")
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

        print("Enter database server HOST Address to edit (127.0.0.1) or press enter to skip")
        DB_HOST = raw_input('({0})>'.format(self.DB_HOST))
        if DB_HOST:
            db_settings.DB_HOST = DB_HOST

        print("Enter database server port to edit (playerStats) or press enter to skip")
        port = raw_input('({0})>'.format(str(self.PORT)))
        if port:
            db_settings.PORT = int(port)
        self.saveSettings()

        print("Settings Updated")
        sys.exit(0)

    def clear_password_store(self):
        try:
            keyring.delete_password(self.KEYRING_APP_ID, self.USERNAME)
            print("Password removed from Keyring")
        except PasswordDeleteError:
            logging.error("Password cannot be deleted or already has been removed")

        sys.exit(0)
