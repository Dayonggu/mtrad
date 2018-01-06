import gdax
import pprint
import datetime
import time
import json
import uuid
from systemconfig import sysconst as sc
import util.trade_logger as loggers


def create_simu_order(type, size, price, product_id, ttl_sec):
    order = {}
    order["type"] = type
    order["size"] = size
    order["price"] = price
    order["product_id"] = product_id
    order["ttl_sec"] = ttl_sec
    order["id"] = uuid.uuid4()
    return order

def get_current_price(client, product_id):
    try:
        tick = client.get_product_ticker(product_id)
    except Exception as gdaxError:
        err_msg = 'gdexError! {}'.format(gdaxError)
        loggers.general_logger.error(err_msg)
        loggers.summary_logger.error(err_msg)
        return None
    except:
        err_msg = 'Unexcepted Error!'
        loggers.general_logger.error(err_msg)
        loggers.summary_logger.error(err_msg)
        return None

    if tick is None:
        return None
    price = tick.get("price", None)
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
