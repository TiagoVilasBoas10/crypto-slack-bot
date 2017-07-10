# coding: utf-8

import re
import json
import requests
import sqlite3

from coinmarketcap import Market
from slackbot.bot import listen_to


class Apollo11Bot(object):
    @staticmethod
    def request(coin, exchange, euro=True):
        url = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms=%s&tsyms=USD" % coin

        if euro:
            url += ",EUR"

        if exchange:
            url += "&e=%s" % exchange

        try:
            response = requests.get(url)
            return json.loads(response.text)
        except:
            return ['Error']

    def request_crypto_compare(self, symbol, exchange):
        euro = True
        result = self.request(symbol, exchange)

        if "DISPLAY" not in result:
            euro = False
            result = self.request(symbol, exchange, False)

        if "DISPLAY" not in result:
            return self.coinmarket(symbol, result['Message'])

        result = result["DISPLAY"][symbol]

        return self.handle_result_crypto_compare(symbol,exchange, result, euro)

    @staticmethod
    def handle_result_crypto_compare(symbol, exchange, result, euro=True):
        symbolIco = result["USD"]["FROMSYMBOL"]
        market_cap_usd = result["USD"]["MKTCAP"]
        h_volume_usd = result["USD"]["VOLUME24HOURTO"]
        price_usd = result['USD']["PRICE"]
        dayHigh = result["USD"]["HIGH24HOUR"]

        change24h = result["USD"]["CHANGEPCT24HOUR"]
        change24hprice = result["USD"]["CHANGE24HOUR"]

        market = result["USD"]["MARKET"]

        if euro:
            price_eur = result['EUR']["PRICE"]
        else:
            price_eur = ' - '

        coin = '```'
        coin += '%s ::: %s ::: %s ::: MktCap: %s :: 24h volume: %s ::: 24h High: %s\n' \
                'Percent change::: 24h: %s%% :: %s \n' \
                'Price: %s / %s' % \
                (market, symbolIco, symbol, market_cap_usd, h_volume_usd, dayHigh,
                 change24h, change24hprice, price_usd, price_eur)

        coin += '```'

        return coin

    def coinmarket(self, symbol, message):
        coinmarketcap = Market()
        try:
            result = coinmarketcap.ticker(symbol, limit=3, convert='EUR')
        except:
            return self.getCoinNotFoundError(message, 'Id not found')

        return self.handle_result_coinmarket(result)

    @staticmethod
    def handle_result_coinmarket(result):
        coin = '```'
        for y in result:
            market_cap_usd = '{:0,.0f}'.format(float(y['market_cap_usd']))
            h_volume_usd = '{:0,.0f}'.format(float(y['24h_volume_usd']))
            price_eur = '{:0,.2f}'.format(float(y['price_eur']))
            price_usd = '{:0,.2f}'.format(float(y['price_usd']))

            coin += '%s ::: %s ::: Rank: %s ::: MktCap: $%s :: 24h volume: $%s \n' \
                    'Percent change::: 1h: %s%% ::: 24h: %s%% ::: 7d: %s%% \n' \
                    'Price: $%s / €%s' % \
                    (y['name'], y['symbol'], y['rank'], market_cap_usd, h_volume_usd, y['percent_change_1h'],
                     y['percent_change_24h'], y['percent_change_7d'], price_usd, price_eur)

        coin += '```'
        return coin

    @staticmethod
    def getExchangesError():
        message = '`ERROR` Invalid exchange. Please use one from above: \n '

        message += '```'

        db = sqlite3.connect('bot.db')
        cursor = db.cursor()

        cursor.execute('select * from exchanges')

        result = cursor.fetchall()

        for i in result:
            message += " %s \n" % i[0]

        message += '\n'
        message += '\n'
        message += 'Example: !btc coinbase'
        message += '```'

        return message

    @staticmethod
    def getCoinNotFoundError(message=None, subMessage=None):
        message = '`ERROR` %s.' % message
        if subMessage:
            message += ' - %s \n' % subMessage
        else:
            message += '\n'
        message += 'Please a different combination: \n '
        message += '\n'
        message += '```Examples:\n'
        message += ' !xrp kraken\n'
        message += ' !eos kraken\n'
        message += '```'

        return message

    @staticmethod
    def find_exchange(user_input):
        db = sqlite3.connect('bot.db')
        cursor = db.cursor()

        cursor.execute('select * from exchanges where id like :id;',{"id":user_input})

        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None

instance = Apollo11Bot()

@listen_to('^!(.*) ?(.*)?', re.IGNORECASE)
def star(*arg):
    message = arg[0]
    query = arg[1]

    query = query.split(' ')

    if len(query) > 2:
        message.send("`ERROR - usage !<symbol> <market>`")
        return False

    star = query[0]
    star = star.upper()

    exchange = None
    user_input = False
    try:
        user_input = query[1]
    except IndexError:
        exchange = 'Kraken'

    if exchange:
        response = instance.request_crypto_compare(star, exchange)
    else:
        exchange = instance.find_exchange(user_input)
        if exchange:
            response = instance.request_crypto_compare(star, exchange)
        else:
            response = instance.getExchangesError()

    message.send(response)
