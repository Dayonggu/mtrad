import gdax
import pprint
import datetime
import time
import json

SKIP_ORDER_TYPE='SKIP'
BUY_ORDER_TYPE='BUY'
SELL_ORDER_TYPE='SELL'

def get_current_price(client, product_id):
    tick = client.get_product_ticker(product_id)
    price = float(tick["price"])
    return price

def is_order_type(order, type):
    order_type = order.get('type', SKIP_ORDER_TYPE)
    return order_type == type

def is_skip_order(order):
    return is_order_type(order, SKIP_ORDER_TYPE)

def is_buy_order(order):
    return is_order_type(order, BUY_ORDER_TYPE)

def is_sell_order(order):
    return is_order_type(order, SELL_ORDER_TYPE)
