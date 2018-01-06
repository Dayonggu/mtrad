import logging
import sys,os
from systemconfig import sysconst as sc
from logging.handlers import RotatingFileHandler

general_log_format = "%(asctime)s|%(levelname)s|%(filename)s|%(funcName)s|%(lineno)d|%(message)s"
summary_log_format = "%(asctime)s|%(levelname)s|%(message)s"
total_log_format = "%(asctime)s|%(levelname)s|%(message)s"
MAX_LOG_BYTES = 1024*1024
LOG_BACKUP_CNT = 10

def setup_logger(name, file_name, formatter, with_stream=True, level=logging.INFO):
    logger = logging.getLogger(name)
    fileHandler = logging.FileHandler(file_name, mode="w")
    #fileHandler = RotatingFileHandler(file_name, MAX_LOG_BYTES, LOG_BACKUP_CNT)
    fileHandler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(fileHandler)

    if with_stream:
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        logger.addHandler(streamHandler)




setup_logger('general',  sc.LOG_HOME+'/tradelog.txt', logging.Formatter(general_log_format))
setup_logger('sum', sc.LOG_HOME+'/summarylog.txt', logging.Formatter(summary_log_format))
setup_logger('price_tracker', sc.LOG_HOME+'/price_tracker_log.txt', logging.Formatter(summary_log_format), with_stream=False)

general_logger = logging.getLogger('general')
summary_logger = logging.getLogger('sum')
price_tracker_logger = logging.getLogger('price_tracker')
