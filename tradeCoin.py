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
        cash_balance=0.0
        total_coin_size = 0.0

        unsold_order=[]
        total_unsold_price=0.0

        cancelled_buy = 0
        cancelled_sell = 0

        cur_round  = 0
        #buy_order = trader.get_buy_order(product_id)

        while cur_round < round:
            loggers.general_logger.info('round {:d}/{:d}'.format(cur_round, round))
            buy_order = trader.get_buy_order(product_id)
            filled_order = TradeCoin.wait_orders_to_fill(trader,5)
            if filled_order is not None:
                loggers.general_logger.info('***  Fill {} order {} with price {:12.2f}'.format(filled_order['type'], filled_order['id'], filled_order['price']))
                order_price = float(filled_order["price"])
                coin_size = float(filled_order["size"])
                if dt.is_buy_order(filled_order):
                    total_coin_size += coin_size
                    cash_balance -= order_price*coin_size
                    pprint.pprint(bar2)
                    sell_order = trader.add_sell_order(filled_order)
                    pprint.pprint(sell_order)
                    #time.sleep(20) # sleep a while anyway, don't by too eager
                else:
                    total_coin_size -= coin_size
                    cash_balance += order_price*coin_size
                    cur_price = trader.get_current_price(product_id)
                    coin_value = total_coin_size*cur_price
                    log_str = 'Round {} :, {} order {}  {:12.2f} | {:12.2f} filled, cash ={:12.2f}, coins= {:12.2f}, with value {:12.2f}, balance {:12.2f}'.format(cur_round, filled_order["type"], filled_order["id"], filled_order["price"], cur_price, cash_balance, total_coin_size,coin_value, cash_balance+coin_value)
                    loggers.general_logger.info(log_str)
                    loggers.summary_logger.info(log_str)
                    cur_round+=1
            else:
                # cancel all buy_orders
                all_buy_orders = trader.get_all_buy_orders()
                for buy_order in all_buy_orders:
                    log_str = 'cancelling {} order {} price {:12.2f}'.format(buy_order['type'], buy_order['id'], float(buy_order['price']))
                    loggers.general_logger.info(log_str)
                    loggers.summary_logger.info(log_str)
                    trader.cancel_order(buy_order)


        cur_price = trader.get_current_price(product_id)
        coin_value = total_coin_size*cur_price
        log_str = 'All round done, cash {:12.2f}, coins= {:10.2f}, with value {:12.2f}, total {:12.2f}'.format(cash_balance, total_coin_size, coin_value, cash_balance+coin_value )
        loggers.general_logger.info(log_str)
        loggers.summary_logger.info(log_str)

    @staticmethod
    def wait_orders_to_fill(trader, check_interval_sec):
        orders = []
        orders.extend(trader.get_all_buy_orders())
        orders.extend(trader.get_all_sell_orders())
        if (len(orders)<1):
            return None
        sec_to_wait = int(orders[0].get('ttl_sec', 3600))
        while  sec_to_wait>0:
            for order in orders:
                pprint.pprint(order)
                price = trader.get_current_price(order["product_id"])
                order_price = float(order["price"])
                if trader.is_order_filled(order):
                    logstr = '{} order {} price ={:12.2f} ({:12.2f}) filled'.format(order["type"], order["id"], order_price, price)
                    loggers.general_logger.info(logstr)
                    loggers.summary_logger.info(logstr)
                    trader.simulate_fill_order(order)
                    return order
            sec_to_wait -= check_interval_sec
            time.sleep(check_interval_sec)
            loggers.general_logger.info('No orders filled at price [{:12.2f}], waiting for another {:d} sec'.format(price, sec_to_wait))
        return None



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

        hist = self.client.get_product_historic_rates('BTC-USD', start=start, end=now, granularity="15")

        for d in hist:
            pprint.pprint(d)

        cash_balance=0.0
        for a in accounts:
            currency = a["currency"]
            balance = float(a["balance"])
            rate=1.0
            if currency != 'USD':
                product = currency+'-USD'
                tick = self.client.get_product_ticker(product)
                rate = float(tick["price"])
            usd_balance = balance*rate
            cash_balance += usd_balance
            line_str = '{},{:>8},{:12.4f},{:12.2f},{:12.2f}'.format(now, currency, balance, rate, usd_balance)
            #print("%s,%s,%.4f,%.2f,%.2f"%(now["iso"], currency, balance, rate, usd_balance))
            loggers.general_logger.info(line_str)
        line_str ='{:10} : {:12.2f}'.format('total(usd)',cash_balance)
        loggers.general_logger.info(line_str)
        return cash_balance
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

    def add_sell_order(self, buy_order):
        return self.policy.add_sell_order(buy_order)

    def cancel_order(self, order):
        #res = self.client.cancel_order(order_id)
        return self.policy.cancel_order(order)

    def get_current_price(self, product_id):
        return dt.get_current_price(self.client, product_id)

    def simulate_fill_order(self, order):
        self.policy.simulate_fill_order(order)

    def is_order_filled(self, order):
        return self.policy.is_order_filled(order)

    def get_all_buy_orders(self):
        return self.policy.get_all_buy_orders()

    def get_all_sell_orders(self):
        return self.policy.get_all_sell_orders()



if __name__ == "__main__":
	_ = TradeCoin.apply_trading(50)
