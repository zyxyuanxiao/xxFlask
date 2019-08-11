# -*- coding:utf-8 -*-

import log_helper as helper

DEBUG = helper.debug
INFO = helper.info
WARN = helper.warning
ERROR = helper.err
LOGGING_INIT = helper.init

LOG_LEVEL_ERROR = helper.LOG_LEVEL_ERROR
LOG_LEVEL_WARNING = helper.LOG_LEVEL_WARNING
LOG_LEVEL_INFO = helper.LOG_LEVEL_INFO
LOG_LEVEL_DEBUG = helper.LOG_LEVEL_DEBUG

__all__ = ["LOGGING_INIT",
           "DEBUG",
           "INFO",
           "WARN",
           "ERROR",
           "LOG_LEVEL_ERROR",
           "LOG_LEVEL_WARNING",
           "LOG_LEVEL_INFO",
           "LOG_LEVEL_DEBUG"]
