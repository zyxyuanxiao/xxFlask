# -*- coding:utf-8 -*-

import os
import sys
import datetime
import gevent
import concurrent_log_handler
import logging
from logging import handlers

LOG_LEVEL_ERROR = 0
LOG_LEVEL_WARNING = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_DEBUG = 3

messageTemplate = '{{"AscTime":"{}","LOG_LEVEL":"{}","SID":"{}","MODULE":"{}:{}:{}","MSG":"{}"}}'
consoleTemplate = '[{}] {} [{}:{}:{}] - {}'


def exc_line_break(s1):
    return s1.replace('\r', r'\r').replace('\n', r'\n')


def log_pre_fix(frame_level=2):
    current_id = id(gevent.getcurrent()) if gevent else 0
    currentframe = sys._getframe(frame_level)
    module = os.path.splitext(os.path.basename(currentframe.f_code.co_filename))[0]
    func_name = currentframe.f_code.co_name
    line_no = currentframe.f_lineno
    return current_id, module, func_name, line_no


class LogHelper(object):
    def __init__(self):
        self.app_name = "default"
        self.pid = 0
        self.process_seq = 0
        self.is_debug = True
        self.info_logger = {}
        self.log_level_config_dict = {}
        self.sync_log_level_config_switch = False
        self.elk_address = ""
        self.elk_port = 0

    def init_logger(self, app_name, is_debug, pid, elk_address, elk_port, **kwargs):
        self.app_name = app_name
        self.pid = pid
        self.is_debug = is_debug
        self.elk_address = elk_address
        self.elk_port = elk_port

    def get_logger(self, category):
        if category not in self.info_logger:
            log_handler_cls = concurrent_log_handler.ConcurrentRotatingFileHandler if concurrent_log_handler \
                else logging.handlers.RotatingFileHandler
            log_filename = os.path.join("log", '{}_local'.format(category))
            log_handler = log_handler_cls(log_filename, "a", 10 * 1024 * 1024, 1000)
            log_handler.setFormatter(logging.Formatter('%(message)s'))
            logger = logging.getLogger('{}_time_logger'.format(category))
            logger.addHandler(log_handler)
            logger.setLevel(logging.INFO)
            self.info_logger[category] = logger

        return self.info_logger[category]

    def handle_log(self, msg, timestamp, level, sid, module, func_name, line_no, category):
        esc_msg = exc_line_break(msg)
        out_msg = messageTemplate.format(timestamp, level, sid, module, func_name, line_no, esc_msg)
        if self.is_debug:
            console_msg = consoleTemplate.format(timestamp, sid, module, func_name, line_no, esc_msg)
            print console_msg
            logger = self.get_logger(category if category else self.app_name)
            logger.info(out_msg)
        else:
            print out_msg

    def push_message(self, msg, level, sid, module, func_name, line_no, category=None):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        self.process_seq += 1
        sid_pack = (self.pid, self.process_seq, sid)
        self.handle_log(msg, timestamp, level, sid_pack, module, func_name, line_no, category)

    def ignore_log_level(self, log_level_type, log_level):
        if not log_level_type:
            return False
        if self.get_log_level(log_level_type) >= log_level:
            return False
        return True

    def get_sync_log_level_config_switch(self):
        return self.sync_log_level_config_switch

    def set_sync_log_level_config_switch(self, switch):
        self.sync_log_level_config_switch = switch

    def get_log_level(self, log_level_type):
        return self.log_level_config_dict.get(log_level_type, 0)

    def get_log_level_config(self):
        return self.log_level_config_dict


__logger = LogHelper()


def init(app_name, is_debug, pid=0, elk_address="", elk_port=0, **kwargs):
    __logger.init_logger(app_name, is_debug, pid, elk_address, elk_port, **kwargs)
    return __logger


def get_log_level(log_level_type):
    return __logger.get_log_level(log_level_type)


def get_log_level_config():
    return __logger.get_log_level_config()


def log(message, level, category=None, frame_level=2, log_level_type="", log_level=0):
    if __logger.ignore_log_level(log_level_type, log_level):
        return
    current_id, module, func_name, line_no = log_pre_fix(frame_level)
    __logger.push_message(message, level, current_id, module, func_name, line_no, category)


def debug(message, log_level_type="", log_level=0, frame_level=3):
    log(message, 'DEBUG', None, frame_level, log_level_type, log_level)


def info(message, log_level_type="", log_level=0, frame_level=3):
    log(message, 'INFO', None, frame_level, log_level_type, log_level)


def warning(message, log_level_type="", log_level=0, frame_level=3):
    log(message, 'WARNING', None, frame_level, log_level_type, log_level)


def err(message, log_level_type="", log_level=0, frame_level=3):
    log(message, 'ERROR', None, frame_level, log_level_type, log_level)
