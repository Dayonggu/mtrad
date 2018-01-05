import gdax
import pprint
import datetime
import time
import json
from systemconfig import sysconst as sc
import util.trade_logger as loggers



def get_current_price(client, product_id):
    try:
        tick = client.get_product_ticker(product_id)
    except gdaxError:
        err_msg = 'gdexError! {}'.format(gdaxError)
        loggers.general_logger.error(log_str)
        loggers.summary_logger.error(log_str)
        return none

    if tick is None:
        return None
    price = tick["price"]
    if price is None:
        return None
    return float(price)

def is_order_type(order, type):
    order_type = order.get('type', sc.SKIP_ORDER_TYPE)
    return order_type == type

def is_skip_order(order):
    return is_order_type(order, sc.SKIP_ORDER_TYPE)

def is_buy_order(order):
    return is_order_type(order, sc.BUY_ORDER_TYPE)

def is_sell_order(order):
    return is_order_type(order, sc.SELL_ORDER_TYPE)
