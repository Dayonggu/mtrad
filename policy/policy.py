import json,os,sys
import util.dt as dt
import uuid
import datetime
import pprint
import util.trade_logger as loggers

SKIP_ORDER= {"type" : 'SKIP_ORDER'}
class BasePolicy(object):
    def __init__(self, config_file, auth_client):
        self.config = json.loads(open(config_file).read())
        self.client = auth_client
        self.buy_orders = []
        self.sell_orders = []

    def get_buy_order(self, product_id):
        max_order_limit=self.config.get('max_buy_orders', 3)
        if len(self.buy_orders) >= max_order_limit:
            return SKIP_ORDER
        return self.get_buy_order_by_policy(product_id)

    def get_sell_order(self, product_id):
        if len(self.buy_orders) == 0:
            return SKIP_ORDER
        return self.get_sell_order_by_policy(product_id)

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
        cur_price = dt.get_current_price(self.client, product_id)
        buy_price = cur_price - float(self.config.get('buy_limit_gap_dollar', '0.5'))
        order = {}
        order["type"] = 'BUY'
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
        order["type"] = 'SELL'
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
        elif dt.is_sell_order(order):
            self.sell_orders = list(filter(lambda x: x["id"]!= order["id"], self.sell_orders))

    def simulate_fill_order(self, order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} filled'.format(order["type"], order["id"], order["price"] ))

    def cancel_order(self,order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} cancelled'.format(order["type"], order["id"], order["price"] ))

    def is_order_filled(self, order):
        product_id = order.get('product_id', 'BTC-USD')
        order_price = order['price']
        cur_price = dt.get_current_price(self.client, product_id)
        loggers.general_logger.info('order price {}, cur prices {}'.format(order_price, cur_price))

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
