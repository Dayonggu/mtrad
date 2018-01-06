import util.trade_logger as loggers
from systemconfig import sysconst as sc

class PriceBuffer:
    def __init__(self, size):
        if size<1:
            size = 5
        self.prices = [0.0]*size
        self.prices_diff = [0.0]*size
        self.prices[0] = 0.00001
        self.h_idx = 0
        self.cur_idx = 1
        self.size = size
        self.total_count=0

    def put(self, price):
        if self.cur_idx == self.h_idx:
            self.h_idx = self.find_next_highest(self.h_idx )
        self.prices[self.cur_idx]=price
        if price>=self.prices[self.h_idx]:
            self.h_idx = self.cur_idx
        else:
            self.prices_diff[self.cur_idx]=self.prices[self.h_idx]-price
        self.cur_idx+=1
        if self.cur_idx>=self.size:
            self.cur_idx=0
        if self.total_count < self.size:
            self.total_count+=1

    def get_highest_price_in_buf(self):
        return self.prices[self.h_idx]

    def get_latest_idx(self):
        latest_idx = self.cur_idx-1
        if latest_idx <0:
            latest_idx = self.size-1
        return latest_idx

    def get_latest_price(self):
        return self.prices[self.get_latest_idx()]

    def find_next_highest(self, exclusive_idx):
        max_found = -0.1
        max_idx = -1
        cur_highest_value = self.prices[exclusive_idx]
        for i in range(self.size):
            if i != exclusive_idx:
                if self.prices[i]>=max_found:
                    max_found = self.prices[i]
                    max_idx = i
        self.h_idx = max_idx
        #update the differents
        diff_change = cur_highest_value - max_found
        for i in range(self.size):
            self.prices_diff[i] -= diff_change
        return max_idx

    def get_current_price_ranking_perc(self):
        latest_idx = self.get_latest_idx()
        if latest_idx == self.h_idx:
            print(' latest_idx {} = self.h_idx {}'.format(latest_idx, self.h_idx))
            return 1.0
        scan = self.h_idx
        total_cnt = latest_idx - self.h_idx
        if total_cnt <=0:
            total_cnt += self.size
        higher_cnt = 0;
        while scan != latest_idx:
            if self.prices[scan] > self.prices[latest_idx]:
                higher_cnt+=1
            scan +=1
            if scan>=self.size:
                scan = 0
        perc = (total_cnt-higher_cnt)*1.0/total_cnt
        #print(' latest_idx = {} cv={} h_idx={} hv={} higher_cnt {} total_cnt ={}, r {:5.4f} '.format(latest_idx, self.prices[latest_idx], self.h_idx, self.prices[self.h_idx], higher_cnt, total_cnt, perc))
        return perc

    def get_buffer_maturity(self):
        return self.total_count*1.0/self.size
