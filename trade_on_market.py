'''
actaully trader on market
'''

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
from trader import gtrader as gt

def get_auth_client():
    config = json.loads(open('priv/cred.json').read())
    key = config["key"]
    pf = config["pf"]
    se = config["se"]
    api_url = config["api_url"]
    return gdax.AuthenticatedClient(key, se, pf, api_url=api_url)

product_id = 'LTC-USD'
#product_id = 'BTC-USD'
#product_id = 'ETH-USD'
#product_id = 'BCH-USD'
auth_client = get_auth_client()
policy = po.PriceBufferPolicy(sc.CONFIG_HOME+"/spbp.json", auth_client, product_id)
trader = gt.gTrader(policy)

trader.trading(product_id, round=20)
trader.finalize()
