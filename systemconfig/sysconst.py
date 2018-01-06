import os,sys
dir = os.path.dirname(__file__)
TOOL_HOME=os.path.realpath('.')
LOG_HOME=TOOL_HOME+"/log"
CONFIG_HOME=TOOL_HOME+"/priv"

ORDER_ACCEPTED = 'ORDER_ACCEPTED'
ORDER_EXPIRED = 'ORDER_EXPIRED'

SKIP_ORDER_TYPE='SKIP'
BUY_ORDER_TYPE='BUY'
SELL_ORDER_TYPE='SELL'
SKIP_ORDER_ID='00000000skip0000'

PRICE_CHECKER_RUNNING_STATUS="RUNNING"
PRICE_CHECKER_STOP_STATUS="STOP"


#email

sender = 'skyford2006@hotmail.com'
receivers = 'skyford2006@hotmail.com'
