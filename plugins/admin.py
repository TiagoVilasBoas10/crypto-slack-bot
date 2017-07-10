# coding: utf-8

import re
import json
import requests
import sqlite3

from datetime import datetime
from slackbot.bot import listen_to


class AdminBot(object):
    @staticmethod
    def admin_init():
        db = sqlite3.connect('bot.db')
        cursor = db.cursor()
        cursor.executescript("""
                CREATE TABLE exchanges(id TEXT, volume24h REAL, created TIMESTAMP, updated TIMESTAMP);
                CREATE index exchanges_index on exchanges (id collate nocase);
               """)
        db.commit()

        url = "https://min-api.cryptocompare.com/data/top/exchanges?fsym=BTC&tsym=USD&limit=100"
        try:
            response = requests.get(url)
            result = json.loads(response.text)
        except:
            return 'Errorrrr'

        message = 'Added exchanges:'
        message += '```'
        cursor = db.cursor()
        for exchange in result["Data"]:
            message += "%s \n" % exchange["exchange"]
            cursor.execute("""INSERT INTO exchanges(id, volume24h, created, updated) VALUES(?,?,?,?) """,
                           (exchange["exchange"], exchange["volume24h"], datetime.now(), datetime.now()))
        db.commit()
        message += '```'

        return message

    def admin_update_exchanges(self):
        db = sqlite3.connect('bot.db')

        url = "https://min-api.cryptocompare.com/data/top/exchanges?fsym=BTC&tsym=USD&limit=100"
        try:
            response = requests.get(url)
            result = json.loads(response.text)
        except:
            return 'Errorrrr'

        message = 'Updated exchanges:'
        message += '```'
        cursor = db.cursor()
        for exchange in result["Data"]:
            message += "%s - $%s\n" % (exchange["exchange"], exchange["volume24h"])
            result = self.find_exchange(exchange["exchange"])

            if result:
                cursor.execute("""UPDATE exchanges set volume24h=:volume, updated=:updated where id=:id""",
                               (exchange["volume24h"], datetime.now(), exchange["exchange"]))
            else:
                cursor.execute("""INSERT OR IGNORE INTO exchanges(id, volume24h, created, updated) VALUES(?,?,?,?) """,
                               (exchange["exchange"], exchange["volume24h"], datetime.now(), datetime.now()))

        db.commit()
        message += '```'

        return message

    @staticmethod
    def find_exchange(user_input):
        db = sqlite3.connect('bot.db')
        cursor = db.cursor()

        cursor.execute('select * from exchanges where id like :id;', {"id": user_input})

        result = cursor.fetchone()

        if result:
            return result
        else:
            return None

instance = AdminBot()

@listen_to('^.admin init$', re.IGNORECASE)
def init(*arg):
    message = arg[0]

    message.send(instance.admin_init())

@listen_to('^.admin update exchanges$', re.IGNORECASE)
def update_exchanges(*arg):
    message = arg[0]

    message.send(instance.admin_update_exchanges())