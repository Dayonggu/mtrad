import logging
import sys,os
from systemconfig import sysconst as sc

general_log_format = "%(asctime)s|%(levelname)s|%(filename)s|%(funcName)s|%(lineno)d|%(message)s"
summary_log_format = "%(asctime)s|%(levelname)s|%(message)s"

def setup_logger(name, file, formatter, level=logging.INFO):
    logger = logging.getLogger(name)
    fileHandler = logging.FileHandler(file, mode="aw")
    fileHandler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(fileHandler)

    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

setup_logger('general',  sc.LOG_HOME+'/tradelog.txt', logging.Formatter(general_log_format))
setup_logger('sum', sc.LOG_HOME+'/summarylog.txt', logging.Formatter(summary_log_format))

general_logger = logging.getLogger('general')
summary_logger = logging.getLogger('sum')
