import json,os,sys
import util.dt as dt
import uuid
import datetime
import time
import pprint
import random
import util.trade_logger as loggers
from systemconfig import sysconst as sc
import pricebuffer
import pricetracker

SKIP_ORDER= {
"type" : sc.SKIP_ORDER_TYPE,
"internal_id" : sc.SKIP_ORDER_ID
}

class BasePolicy(object):
    def __init__(self, config_file, auth_client):
        self.config = json.loads(open(config_file).read())
        self.client = auth_client
        self.buy_orders = []
        self.sell_orders = []

    def get_name(self):
        return  self.config.get('name', "Unknown")

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
        logString = 'Create Sell Order {} at {:12.2f}, based on buy {} at {:12.2f}, cur sell queue {:d}'.format(sell_order['internal_id'], sell_order['price'], buy_order['internal_id'],buy_order['price'], len(self.sell_orders))
        loggers.general_logger.info(logString)
        loggers.summary_logger.info(logString)
        return sell_order

    def get_all_buy_orders(self):
        return self.buy_orders;

    def get_all_sell_orders(self):
        return self.sell_orders;

    def get_client(self):
        return self.client

    def remove_order(self, order):
        if dt.is_buy_order(order):
            self.buy_orders = list(filter(lambda x: x["internal_id"]!= order["internal_id"], self.buy_orders))
            pprint.pprint('after remove buy order')
            pprint.pprint(self.buy_orders)
        elif dt.is_sell_order(order):
            self.sell_orders = list(filter(lambda x: x["internal_id"]!= order["internal_id"], self.sell_orders))
            pprint.pprint('after remove sell order')
            pprint.pprint(self.sell_orders)

    def simulate_fill_order(self, order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} filled'.format(order["type"], order["internal_id"], order["price"] ))

    def failed_to_file_order(self, order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} failed to file'.format(order["type"], order["internal_id"], order["price"] ))

    def cancel_order(self,order):
        self.remove_order(order)
        loggers.general_logger.info('{} order id [{}] with price {} cancelled'.format(order["type"], order["internal_id"], order["price"] ))

    def is_order_filled(self, order):
        product_id = order.get('product_id', 'BTC-USD')
        order_price = order['price']
        order_type =  order['type']
        order_id =  order['internal_id']
        cur_price = dt.get_current_price(self.client, product_id)
        if cur_price is None:
            loggers.general_logger.error('Cannot get tick at this moment')
            return False
        loggers.general_logger.info('Check {} order {} price {:8.2f} / ({:8.2f})'.format(order_type, order_id, order_price, cur_price))

        if dt.is_buy_order(order):
            return order_price>=cur_price
        elif dt.is_sell_order(order):
            return order_price<=cur_price
        return False

    def preparation(self):
        pass

    def finalize(self):
        pass


class PriceBufferPolicy(BasePolicy):
    def __init__(self, config_file, client, product_id):
        super(PriceBufferPolicy, self).__init__(config_file, client)
        self.product_id =product_id
        self.last_buy_order_price = 0.0;
        self.buy_to_buy_diff = float(self.config.get('minium_buy_to_buy_diff', '0.01'))
        self.lower_bound_to_buy_in_price_buffer = float(self.config.get('lower_bound_to_buy_in_price_buffer', '0.2'))
        self.higher_bound_to_buy_in_price_buffer = float(self.config.get('higher_bound_to_buy_in_price_buffer', '0.95'))
        self.minium_diff_highest_to_buy = float(self.config.get('minium_diff_highest_to_buy', '0.2'))
        self.min_distance_to_h_idx = int(self.config.get('self.min_distance_to_h_idx',"3"))



    def preparation(self):
        self.price_buffer = pricebuffer.PriceBuffer(int(self.config.get('price_buffer_size', '20')))
        self.price_tracker_thread = pricetracker.PriceTracker(self.price_buffer, self.client, self.product_id, int(self.config.get('price_check_interval_sec', '2')))
        self.price_tracker_thread.start()
        maturity = 0.0001
        mature_thresh = float(self.config.get('price_buffer_mature_thresh', '0.2'))
        while (maturity < mature_thresh):
            time.sleep(10)
            loggers.general_logger.info('price buffer is not ready, please wait: {:5.2f}%'.format(maturity*100.0/mature_thresh))
            maturity = self.price_buffer.get_buffer_maturity()


    def finalize(self):
        if self.price_tracker_thread.isAlive():
            self.price_tracker_thread.set_status(sc.PRICE_CHECKER_STOP_STATUS)
        self.price_tracker_thread.join()

    def in_buy_range(self, cur_price):
        #percentage = self.price_buffer.get_current_price_ranking_perc()
        percentage = self.price_buffer.get_current_price_ranking_perc(cur_price)
        if percentage<self.lower_bound_to_buy_in_price_buffer or percentage>self.higher_bound_to_buy_in_price_buffer:
            loggers.general_logger.info('Current price {:10.2f} percentage in buffer is {:5.2f}, not in range [{},{}], skip'.format(cur_price, percentage, self.lower_bound_to_buy_in_price_buffer, self.higher_bound_to_buy_in_price_buffer))
            return False
        loggers.general_logger.info('Current price {:10.2f} percentage in buffer is {:5.2f},  in range [{},{}], skip'.format(cur_price, percentage, self.lower_bound_to_buy_in_price_buffer, self.higher_bound_to_buy_in_price_buffer))
        return True


    def get_buy_order_by_policy(self, product_id):
        max_sell_queue_size = int(self.config.get('max_sell_orders', 3))

        x = random.randint(1, max_sell_queue_size*max_sell_queue_size+1)
        #add a random number, more cautious where there is a long sell-queue
        if x<len(self.sell_orders)*len(self.sell_orders):
            return SKIP_ORDER


        cur_price = dt.get_current_price(self.client, product_id)
        if cur_price is None:
            loggers.general_logger.error('Cannot get tick at this moment')
            return SKIP_ORDER
        if abs(cur_price-self.last_buy_order_price) < self.buy_to_buy_diff:
            loggers.general_logger.info('Current price {:10.2f} too close to last order {:10.2f} (must with gap > {:5.2f})'.format(cur_price, self.last_buy_order_price, self.buy_to_buy_diff))
            return SKIP_ORDER

        dis_to_h_idx = self.price_buffer.get_distance_to_h_idx()
        if dis_to_h_idx < self.min_distance_to_h_idx:
            loggers.general_logger.info('Current latest is too close to highest {:d}  (must with gap > {:d})'.format(dis_to_h_idx, self.min_distance_to_h_idx))
            return SKIP_ORDER


        latest_price_in_buffer = self.price_buffer.get_latest_price()
        if abs(cur_price-latest_price_in_buffer) < self.buy_to_buy_diff:
            if not self.in_buy_range(cur_price):
                return SKIP_ORDER

        cur_highest = self.price_buffer.get_highest_price_in_buf()
        if (cur_highest-cur_price) < self.minium_diff_highest_to_buy:
            loggers.general_logger.info('Current price {:10.2f} too close to cur highest  {:10.2f} (must with gap > {:5.2f})'.format(cur_price, cur_highest, self.minium_diff_highest_to_buy))
            return SKIP_ORDER



        buy_price = cur_price - float(self.config.get('buy_limit_gap_dollar', '0.5'))
        buy_price = round(buy_price,2)
        order = dt.create_suggest_order(sc.BUY_ORDER_TYPE, float(self.config.get('size', '0.0001')), buy_price, product_id, int(self.config.get('buy_ttl_sec', '3600')))
        logstr = 'Create BUY {} with price {:10.2f} at {:10.2f}'.format(order['internal_id'], buy_price, cur_price)
        loggers.general_logger.info(logstr)
        loggers.general_logger.info(self.price_buffer.dump_price_data())
        loggers.summary_logger.info(logstr)

        self.buy_orders.append(order)
        self.buy_orders.sort(key=lambda x: x["price"], reverse=True)
        self.last_buy_order_price = buy_price
        return order

    def get_sell_order_by_policy(self, buy_order):
        buy_order_price = float(buy_order.get("price", '-0.1'))
        if buy_order_price < 0.0:
            return SKIP_ORDER
        product_id = buy_order.get('product_id', 'BTC-USD')
        sell_order_price = buy_order_price*float(self.config.get("profit_target", '1.0075'))
        cur_price = dt.get_current_price(self.client, product_id)
        if cur_price is None:
            loggers.general_logger.error('Cannot get tick at this moment')
            return SKIP_ORDER
        if (sell_order_price < cur_price):
            sell_order_price = cur_price+0.05

        cur_highest = self.price_buffer.get_highest_price_in_buf()

        if sell_order_price<cur_highest:
            max_speculative_to_highest = float(self.config.get('max_speculative_to_highest', '0.5'))
            sell_order_price += (cur_highest-sell_order_price)*max_speculative_to_highest

        sell_order_price = round(sell_order_price,2)
        order = dt.create_suggest_order(sc.SELL_ORDER_TYPE, float(self.config.get('size', '0.0001')), sell_order_price, buy_order.get("product_id", "BTC-USD"), int(self.config.get('sell_ttl_sec', '3600')))
        logstr = 'Create SELL {} with price {:10.2f} at {:10.2f} based on buy price {:10.2f}'.format(order['internal_id'], sell_order_price, cur_price, buy_order_price)
        loggers.general_logger.info(logstr)
        loggers.summary_logger.info(logstr)
        self.sell_orders.append(order)
        self.sell_orders.sort(key=lambda x: x["price"], reverse=False)
        return order

    def update_market_id(self, order, market_id):
        order[sc.MARKET_ID]=market_id;
        if market_id == sc.FAILED_TO_FILE_ORDER_ID:
            self.failed_to_file_order(order)

    def get_buy_order_ttl(self):
        return self.config.get('buy_ttl_sec', '3600')




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
        order = dt.create_suggest_order(sc.BUY_ORDER_TYPE, float(self.config.get('size', '0.0001')), buy_price, product_id, int(self.config.get('buy_ttl_sec', '3600')))
        self.buy_orders.append(order)
        self.buy_orders.sort(key=lambda x: x["price"], reverse=True)
        return order

    def get_sell_order_by_policy(self, buy_order):
        buy_order_price = float(buy_order.get("price", '-0.1'))
        product_id = buy_order.get('product_id', 'BTC-USD')
        sell_order_price = buy_order_price*float(self.config.get("profit_target", '1.0075'))
        cur_price = dt.get_current_price(self.client, product_id)
        if cur_price is None:
            loggers.general_logger.error('Cannot get tick at this moment')
            return False
        if (sell_order_price < cur_price):
            sell_order_price = cur_price+0.05

        order = dt.create_suggest_order(sc.SELL_ORDER_TYPE, float(self.config.get('size', '0.0001')), sell_order_price, buy_order.get("product_id", "BTC-USD"), int(self.config.get('sell_ttl_sec', '3600')))
        self.sell_orders.append(order)
        self.sell_orders.sort(key=lambda x: x["price"], reverse=False)
        return order


'''
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
'''
