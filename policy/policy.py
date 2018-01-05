import json,os,sys
import util.dt as dt
import uuid
import datetime
import pprint
import random
import util.trade_logger as loggers
from systemconfig import sysconst as sc

SKIP_ORDER= {
"type" : sc.SKIP_ORDER_TYPE,
"id" : sc.SKIP_ORDER_ID
}

class BasePolicy(object):
    def __init__(self, config_file, auth_client):
        self.config = json.loads(open(config_file).read())
        self.client = auth_client
        self.buy_orders = []
        self.sell_orders = []

    def get_buy_order(self, product_id):
        if len(self.buy_orders) >= int(self.config.get('max_buy_orders', 3)):
            return SKIP_ORDER
        if len(self.sell_orders) >= int(self.config.get('max_sell_orders', 3)):
            pprint.pprint('should skip order!!')
            return SKIP_ORDER
        logStr = 'sell order que len {},  max {}'.format(len(self.sell_orders), self.config.get('max_sell_orders', 3))
        pprint.pprint(logStr)
        return self.get_buy_order_by_policy(product_id)

    def add_sell_order(self, buy_order):
        if len(self.sell_orders) >= self.config.get('max_sell_orders', 3):
            return SKIP_ORDER
        sell_order = self.get_sell_order_by_policy(buy_order)
        logString = 'Create Sell Order {} at {:12.2f}, based on buy {} at {:12.2f}, cur sell queue {:d}'.format(sell_order['id'], sell_order['price'], buy_order['id'],buy_order['price'], len(self.sell_orders))
        loggers.general_logger.info(logString)
        loggers.summary_logger.info(logString)
        return sell_order

    def get_all_buy_orders(self):
        return self.buy_orders;

    def get_all_sell_orders(self):
        return self.sell_orders;

    def get_client(self):
        return self.client




class BltPolicy(BasePolicy):
    def __init__(self, config_file, client):
        super(BltPolicy, self).__init__(config_file, client)

    def get_buy_order_by_policy(self, product_id):

        x = random.randint(1, int(self.config.get('max_sell_orders', 3))+1)
        #add a random number, more cautious where there is a long sell-queue
        if x<len(self.sell_orders):
            return SKIP_ORDER

        cur_price = dt.get_current_price(self.client, product_id)
        if cur_price is None:
            loggers.general_logger.error('Cannot get tick at this moment')
            return SKIP_ORDER
        buy_price = cur_price - float(self.config.get('buy_limit_gap_dollar', '0.5'))
        order = {}
        order["type"] = sc.BUY_ORDER_TYPE
        order["size"] = float(self.config.get('size', '0.0001'))
        order["price"] = buy_price
        order["product_id"] = product_id
        order["ttl_sec"] = int(self.config.get('buy_ttl_sec', '3600'))
        order["id"] = uuid.uuid4()
        self.buy_orders.append(order)
        self.buy_orders.sort(key=lambda x: x["price"], reverse=True)
        return order

    def get_sell_order_by_policy(self, buy_order):
        buy_order_price = float(buy_order.get("price", '-0.1'))
        order = {}
        order["type"] = sc.SELL_ORDER_TYPE
        order["size"] = float(buy_order.get("size", '0.0001'))
        order["price"] = buy_order_price*float(self.config.get("profit_target", '1.0075'))
        order["product_id"] = buy_order.get("product_id", "BTC-USD")
        order["ttl_sec"] = int(self.config.get('sell_ttl_sec', '3600'))
        order["id"] = uuid.uuid4()
        self.sell_orders.append(order)
        self.sell_orders.sort(key=lambda x: x["price"], reverse=False)
        return order

    def remove_order(self, order):
        if dt.is_buy_order(order):
            self.buy_orders = list(filter(lambda x: x["id"]!= order["id"], self.buy_orders))
            pprint.pprint('after remove buy order')
            pprint.pprint(self.buy_orders)
        elif dt.is_sell_order(order):
            self.sell_orders = list(filter(lambda x: x["id"]!= order["id"], self.sell_orders))
            pprint.pprint('after remove sell order')
            pprint.pprint(self.sell_orders)

    def simulate_fill_order(self, order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} filled'.format(order["type"], order["id"], order["price"] ))

    def cancel_order(self,order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} cancelled'.format(order["type"], order["id"], order["price"] ))

    def is_order_filled(self, order):
        product_id = order.get('product_id', 'BTC-USD')
        order_price = order['price']
        order_type =  order['type']
        order_id =  order['id']
        cur_price = dt.get_current_price(self.client, product_id)
        if cur_price is None:
            loggers.general_logger.error('Cannot get tick at this moment')
            return False
        loggers.general_logger.info('Check {} order {} price {} / ({})'.format(order_type, order_id, order_price, cur_price))

        if dt.is_buy_order(order):
            return order_price>=cur_price
        elif dt.is_sell_order(order):
            return order_price<=cur_price
        return False

    def is_order_filled_old(self, order):
        check_interval_sec = int(self.config.get('check_interval_sec',30))
        product_id = order.get('product_id', 'BTC-USD')
        price = order['price']
        now = datetime.datetime.now()
        start = now - datetime.timedelta(seconds=check_interval_sec)
        hist = self.client.get_product_historic_rates(product_id, start=start, end=now, granularity=check_interval_sec)
        # just use the first one
        pprint.pprint(hist)
        low = sys.maxint
        high = -1.0

        for p in  hist:
            if low>p[1]:
                low = p[1]
            if high<p[2]:
                high = p[2]
        loggers.general_logger.info('order price {}, low {}, high {}'.format(price, low, high))

        if dt.is_buy_order(order):
            return price>=low
        elif dt.is_sell_order(order):
            return price<=high
        return False
