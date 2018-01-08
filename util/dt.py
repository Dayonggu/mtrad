import gdax
import pprint
import datetime
import time
import json
import uuid
from systemconfig import sysconst as sc
import util.trade_logger as loggers


def create_suggest_order(type, size, price, product_id, ttl_sec):
    order = {}
    order["type"] = type
    order["size"] = size
    order["price"] = price
    order["product_id"] = product_id
    order["ttl_sec"] = ttl_sec
    order["internal_id"] = uuid.uuid4()
    return order

def get_uuid():
    return uuid.uuid4()

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

def get_on_market_orders(client, product_id):
    try:
        orders = client.get_orders(product_id)
        if len(orders)>0:
            return orders[0]
        else:
            return None
    except:
        return None
    if orders is not None:
        return orders[0]

def get_on_market_order_by_id(client, id):
    try:
        order = client.get_order(id)
        return order
    except:
        return None

def check_on_market_order_status(order):
    if order is None:
        return None
    status = order.get('status', None)
    if status is None:
        status = order.get('message', None)
    return status




def is_order_type(order, type):
    order_type = order.get('type', sc.SKIP_ORDER_TYPE)
    return order_type == type

def is_skip_order(order):
    return is_order_type(order, sc.SKIP_ORDER_TYPE)

def is_buy_order(order):
    return is_order_type(order, sc.BUY_ORDER_TYPE)

def is_sell_order(order):
    return is_order_type(order, sc.SELL_ORDER_TYPE)

def get_time_to_now_sec(timestr, format):
    try:
        change_to_time = datetime.datetime.strptime(timestr,format)
        now = datetime.datetime.now()
        return (now-change_to_time).seconds
    except ValueError as verr:
        return None

def list_filter_out(field, value, from_list):
    return list(filter(lambda x: x[field]!=value, from_list))

def get_from_list(field, value, from_list):
    return list(filter(lambda x: x[field]== value, from_list))
