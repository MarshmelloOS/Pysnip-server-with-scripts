"""
Logs when players are on and off the server. Can find what players were on the server during a specific time interval by
using /findusers timeinterval1 timeinterval2 day month year. Each time interval should be in the form hour:minute:second
If the intervals are the same it finds the users logged on at that point in time. If day, month, or year is left out it
will use the current day, month, or year at the time the command is used. Logs are saved to logs\playerlog.db
"""

import sqlite3
import os
import time
import datetime
import commands

PATH = r'\logs\playerlog.db'

COMMANDS_CREATE_TABLES = [
    ''' CREATE TABLE IF NOT EXISTS display_names (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )''',
    ''' CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            name_id INTEGER NOT NULL REFERENCES display_names(id)
        )''',
    ''' CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time INTEGER NOT NULL
        )''',
    ''' CREATE TABLE IF NOT EXISTS connection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER UNIQUE NOT NULL REFERENCES events(id),
            connection_id INTEGER UNIQUE NOT NULL REFERENCES connections(id)
        )''',
    ''' CREATE TABLE IF NOT EXISTS disconnection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER UNIQUE NOT NULL REFERENCES events(id),
            connection_id INTEGER UNIQUE NOT NULL REFERENCES connections(id)
        )'''
]

COMMAND_SELECT_NAME = '''\
    SELECT id
    FROM display_names
    WHERE name == ?'''

COMMAND_INSERT_NAME = '''\
    INSERT INTO display_names (name)
    VALUES (?)'''

COMMAND_INSERT_CONNECTION = '''\
    INSERT INTO connections (ip, name_id)
    values (?, ?)'''

COMMAND_INSERT_EVENT = '''\
    INSERT INTO events (time)
    VALUES (?)'''

COMMAND_INSERT_CONNECTION_EVENT = '''
    INSERT INTO connection_events (event_id, connection_id)
    values (?, ?)'''

COMMAND_INSERT_DISCONNECTION_EVENT = '''
    INSERT INTO disconnection_events (event_id, connection_id)
    values (?, ?)'''

COMMAND_SELECT_CONNECTION_EVENTS = '''\
    SELECT connection_id
    FROM events INNER JOIN connection_events 
        ON connection_events.event_id == events.event_id
    WHERE time <= ?'''

COMMAND_SELECT_DISCONNECTION_EVENTS = '''\
    SELECT connection_id
    FROM events INNER JOIN disconnection_events 
        ON disconnection_events.event_id == events.event_id
    WHERE time >= ?'''

COMMAND_SELECT_CONNECTION_NAME = '''\
    SELECT name
    FROM connections INNER JOIN display_names
        ON connections.name_id == display_names.id
    WHERE connections.id == ?'''


def get_seconds(time_string):
    hours, minutes, seconds = time_string.split(':')
    return int(hours)*3600 + int(minutes)*60 + seconds


def get_from_to_seconds(time1, time2, day, month, year):
    current_time = time.localtime()
    if day is None:
        day = current_time.tm_mday
    if month is None:
        month = current_time.tm_mon
    if year is None:
        year = current_time.tm_year
    timestamp = time.mktime(time.gmtime(datetime.datetime(int(year), int(month), int(day)).timestamp()))
    return timestamp + get_seconds(time1), timestamp + get_seconds(time2)


@commands.admin
def findusers(connection, time1, time2, day=None, month=None, year=None):
    from_time, to_time = get_from_to_seconds(time1, time2, day, month, year)
    cur = connection.protocol.cursor
    cur.execute(COMMAND_SELECT_CONNECTION_EVENTS, [to_time])
    before_end_connections = set(cur.fetchall())
    cur.execute(COMMAND_SELECT_DISCONNECTION_EVENTS, [from_time])
    after_beginning_disconnections = set(cur.fetchall())
    logged_in_ids = before_end_connections.intersection(after_beginning_disconnections)
    cur.execute(COMMAND_SELECT_CONNECTION_NAME, [logged_in_ids])
    names = cur.fetchall()
    if names:
        message = ' , '.join(names)
        message += ' were logged on'
    else:
        message = 'No one logged on at that time'
    return message
commands.add(findusers)


def apply_script(protocol, connection, config):
    class UserLogConnection(connection):
        def __init__(self, *args, **kwargs):
            connection.__init__(*args, **kwargs)
            self.connection_id = None

        def on_login(self, name):
            cur = self.protocol.cursor
            cur.execute(COMMAND_SELECT_NAME, [name])
            result = cur.fetchone()
            if result is None:
                cur.execute(COMMAND_INSERT_NAME, [name])
                name_id = cur.lastrowid
            else:
                name_id = result[0]
            cur.execute(COMMAND_INSERT_CONNECTION, [self.address[0], name_id])
            self.connection_id = cur.lastrowid
            cur.execute(COMMAND_INSERT_EVENT, [time.time()])
            event_id = cur.lastrowid
            cur.execute(COMMAND_INSERT_CONNECTION_EVENT, [event_id, self.connection_id])
            self.protocol.log_connection.commit()
            return connection.on_login(self, name)

        def on_disconnect(self):
            cur = self.protcol.cursor
            cur.execute(COMMAND_INSERT_EVENT, [time.time()])
            event_id = cur.lastrowid
            cur.execute(COMMAND_INSERT_DISCONNECTION_EVENT, [event_id, self.connection_id])
            self.protocol.log_connection.commit()
            return connection.on_disconnect(self)

    class LoggerProtocol(protocol):
        def __init__(self, *args, **kwargs):
            protocol.__init__(self, *args, **kwargs)
            self.log_connection = sqlite3.connect(os.path.join(os.getcwd(), PATH))
            self.cursor = self.log_connection.cursor()

    return LoggerProtocol, UserLogConnection
