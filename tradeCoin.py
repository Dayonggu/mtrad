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
import util.trade_logger as loggers
import policy.policy as po
from systemconfig import sysconst as sc
import util.dt as dt

'''
simulator
'''

bar1 = '--------------------------------------------'
bar2 = '============================================'
barS = '********************************************'

class TradeCoin:
    @staticmethod
    def helloWorld():
        print (" -- Hellow User :")

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
    def apply_trading(round=10):
        auth_client = TradeCoin.get_auth_client()
        policy = po.BltPolicy(sc.CONFIG_HOME+"/bltp.json", auth_client)
        trader = Trader(policy)
        trader.get_all_balance()

        product_id = 'BTC-USD'
        strline = 'start a new trade for product {}, with round {} '.format(product_id, round)
        loggers.general_logger.info(strline)
        loggers.summary_logger.info(strline)
        total_profit=0.0

        unsold_order=[]
        total_unsold_price=0.0

        cancelled_buy = 0
        cancelled_sell = 0

        cur_round  = 0
        while cur_round < round:
            loggers.general_logger.info('round {:d}/{:d}'.format(cur_round, round))
            price = trader.get_current_price(product_id)
            buy_order = trader.get_buy_order(product_id)


            if  dt.is_skip_order(buy_order):
                loggers.general_logger.info('cur price={}, SKIP'.format(price))
                continue

            pprint.pprint(buy_order)
            sell_order = trader.get_sell_order(buy_order)
            buy_price = float(buy_order["price"])
            sell_price = float(sell_order["price"])
            target_profit=sell_price-buy_price

            # wait for buy order to be filled
            result = TradeCoin.wait_order_to_fill(trader,buy_order,10)
            if result == sc.ORDER_EXPIRED:
                trader.cancel_order(buy_order)
                cancelled_buy += 1
                trader.cancel_order(sell_order)
                continue

            trader.simulate_fill_order(buy_order)
            # wait for sell order to be filled
            result = TradeCoin.wait_order_to_fill(trader,sell_order,10)
            if result == sc.ORDER_EXPIRED:
                unsold_order.append(buy_order)
                total_unsold_price += buy_price
                trader.cancel_order(sell_order)
                cancelled_sell += 1
                continue

            # now we finish a whole round 
            trader.simulate_fill_order(sell_order)
            total_profit += target_profit
            loggers.general_logger.info('round {} done, cur price={:18.2f}, {} order price ={:18.2f} filled, get profit {:18.2f}, total profit ={:18.2f}, total unsold ={:18.2f}'.format(cur_round, price, sell_order["type"], sell_order["price"], target_profit, total_profit, total_unsold_price))
            cur_round+=1

        count_of_unsold = len(total_unsold_price)
        loggers.general_logger.info('all round done, total profit {:18.2f}, with {d} unsold, with total value {:18.2f}, cancelled_buy {}, cancel_sell {} '.format(total_profit, count_of_unsold, total_unsold_price, cancelled_buy, cancelled_sell))

    @staticmethod
    def wait_order_to_fill(trader, order,check_interval_sec):
        sec_to_wait = int(order.get('ttl_sec', 3600))
        while  sec_to_wait>0:
            price = trader.get_current_price(order["product_id"])
            order_price = float(order["price"])

            if trader.is_order_filled(order):
                loggers.general_logger.info('cur price={:18.2f}, {} order price ={:18.2f} filled'.format(price, order["type"], order_price))
                return sc.ORDER_ACCEPTED
            sec_to_wait -= check_interval_sec
            time.sleep(check_interval_sec)
            loggers.general_logger.info('cur price={:18.2f}, {} order price ={:18.2f} not filled, waiting for another {:d}'.format(price, order["type"], order_price, sec_to_wait))
        return sc.ORDER_EXPIRED



    @staticmethod
    def get_auth_client():
        config = json.loads(open('priv/cred.json').read())
        key = config["key"]
        pf = config["pf"]
        se = config["se"]
        api_url = config["api_url"]
        return gdax.AuthenticatedClient(key, se, pf, api_url=api_url)



class Trader:
    def __init__(self, policy):
        self.policy = policy
        self.client = policy.get_client()

    def get_all_balance(self):
        accounts = self.client.get_accounts()
        #now = self.client.get_time()
        #start = now - datetime.timedelta(seconds=15)
        now = datetime.datetime.now()
        start = now - datetime.timedelta(seconds=45)

        pprint.pprint(now)
        pprint.pprint(start)


        hist = self.client.get_product_historic_rates('BTC-USD', start=start, end=now, granularity="15")

        for d in hist:
            pprint.pprint(d)

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
            line_str = '{},{:>8},{:15.4f},{:18.2f},{:18.2f}'.format(now, currency, balance, rate, usd_balance)
            #print("%s,%s,%.4f,%.2f,%.2f"%(now["iso"], currency, balance, rate, usd_balance))
            loggers.general_logger.info(line_str)
        line_str ='{:10} : {:18.2f}'.format('total(usd)',total_balance)
        loggers.general_logger.info(line_str)
        return total_balance
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

    def get_buy_order(self, product_id):
        return self.policy.get_buy_order(product_id)


    def sell(self,price,size,product_id):
        res = self.client.sell(price=price, #USD
               size=size, #BTC
               order_type='limit',
               product_id=product_id)
        return res["id"]

    def get_sell_order(self, buy_order):
        return self.policy.get_sell_order(buy_order)

    def cancel_order(self, order):
        #res = self.client.cancel_order(order_id)
        return self.policy.cancel_order(order)

    def get_current_price(self, product_id):
        return dt.get_current_price(self.client, product_id)

    def simulate_fill_order(self, order):
        self.policy.simulate_fill_order(order)

    def is_order_filled(self, order):
        return self.policy.is_order_filled(order)



if __name__ == "__main__":
	_ = TradeCoin.apply_trading(10)
