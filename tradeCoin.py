from __future__ import print_function
import os
import sys
from shutil import rmtree
import argparse
import logging as log
import gdax
import pprint
import datetime
import time
import json
'''
simulator
'''

bar1 = '--------------------------------------------'
bar2 = '============================================'
barS = '********************************************'

class TradeCoin:
    @staticmethod
    def helloWorld():
        client = TradeCoin.getClient()
        print (" -- Hellow User :")
        print(client)
        pprint.pprint(TradeCoin.get_currencies(client))
        unit = 6
        ten_min = datetime.timedelta(minutes=10)
        now = datetime.datetime.now()
        start = now - ten_min
        hr = TradeCoin.get_historic_rates(client, start, now, unit)
        pprint.pprint(hr)

        pprint.pprint(bar1)
        orderbook = client.get_product_order_book('BTC-USD', level=10)
        pprint.pprint(orderbook)
        pprint.pprint(bar1)
        pprint.pprint(client.get_product_24hr_stats('BTC-USD'))

        pprint.pprint(barS)

        auth_client = gdax.AuthenticatedClient(key, b64s, pf, api_url="https://api.gdax.com")
        accounts = auth_client.get_accounts()
        for a in accounts:
            pprint.pprint(a)

    @staticmethod
    def getClient():
        return gdax.PublicClient()

    @staticmethod
    def get_time(client):
        t = client.get_time()
        assert type(t) is dict
        assert 'iso' in t
        return t

    @staticmethod
    def get_currencies(client):
        r = client.get_currencies()
        assert type(r) is list
        assert 'name' in r[0]
        return r

    @staticmethod
    def get_historic_rates(client, start, end, granularity):
        r = client.get_product_historic_rates('BTC-USD', start=start, end=end, granularity=granularity)
        assert type(r) is list
        return r
    @staticmethod
    def apply_trading():
        config = json.loads(open('priv/cred.json').read())
        key = config["key"]
        pf = config["pf"]
        se = config["se"]
        api_url = config["api_url"]
        auth_client = gdax.AuthenticatedClient(key, se, pf, api_url=api_url)
        trader = Trader(auth_client)
        trader.get_all_balance()


class Trader:
    def __init__(self, client):
        self.client = client

    def get_all_balance(self):
        accounts = self.client.get_accounts()
        now = self.client.get_time()
        total_balance=0.0
        for a in accounts:
            currency = a["currency"]
            balance = float(a["balance"])
            rate=1.0
            if currency != 'USD':
                product = currency+'-USD'
                tick = self.client.get_product_ticker(product)
                rate = float(tick["price"])
            usd_balance = balance*rate
            total_balance += usd_balance
            print("%s,%s,%.4f,%.2f,%.2f"%(now["iso"], currency, balance, rate, usd_balance))
        print("total(usd):%.2f"%total_balance)
        #buy_order = self.buy('100.0', '0.01', 'BTC-USD')
        #sell_order = self.sell('10000000.0', '0.01', 'BTC-USD')
        #pprint.pprint(buy_order)
        #time.sleep(10)
        #self.cancel_order(buy_order)


    def buy(self,price,size,product_id):
        res = self.client.buy(price=price, #USD
               size=size, #BTC
               order_type='limit',
               product_id=product_id)
        return res["id"]


    def sell(self,price,size,product_id):
        res = self.client.sell(price=price, #USD
               size=size, #BTC
               order_type='limit',
               product_id=product_id)
        return res["id"]

    def cancel_order(self, order_id):
        res = self.client.cancel_order(order_id)
        pprint.pprint(res)


if __name__ == "__main__":
	_ = TradeCoin.apply_trading()
