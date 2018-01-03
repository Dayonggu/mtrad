import os,sys
dir = os.path.dirname(__file__)
TOOL_HOME=os.path.realpath('.')
LOG_HOME=TOOL_HOME+"/log"
CONFIG_HOME=TOOL_HOME+"/priv"

ORDER_ACCEPTED = 'ORDER_ACCEPTED'
ORDER_EXPIRED = 'ORDER_EXPIRED'
