import pprint
import gdax
import util.dt as dt
from threading import Thread
import numpy as np
import datetime
import time
import json
import util.trade_logger as loggers
from systemconfig import sysconst as sc

class PriceTracker(Thread):
    def __init__(self, price_buffer, client, product_id, check_interval=5):
        Thread.__init__(self)
        self.pb = price_buffer
        self.client = client
        self.last_price = -10.0
        self.product_id = product_id
        self.status = 'RUNNING'
        self.check_interval = check_interval

    def get_current_price(self, product_id):
        price = dt.get_current_price(self.client, product_id)
        if price is None:
            return None
        if abs(price-self.last_price)<0.05:
            loggers.price_tracker_logger.info('{}: {:10.2f}, skipped'.format(product_id, price))
            return price
        self.last_price = price
        self.pb.put(price)
        loggers.price_tracker_logger.info('{}: {:10.2f}, taken'.format(product_id, price))

    def run(self):
        while self.status == sc.PRICE_CHECKER_RUNNING_STATUS:
            self.get_current_price(self.product_id)
            time.sleep(self.check_interval)
        loggers.price_tracker_logger.info('Exit, status is set to {} '.format(self.status))

    def set_status(self, status):
        self.status = status
