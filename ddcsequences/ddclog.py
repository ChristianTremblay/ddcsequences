# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 10:29:28 2015

@author: CTremblay
"""
import os
import logging
from os.path import expanduser, join

from datetime import datetime


def createLogger(name, filepath=None, filename=None):
    # create logger with 'spam_application'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    if filepath == None:
        logSaveFilePath = os.getcwd()
        # logUserPath = expanduser('~')
        # logSaveFilePath = join(logUserPath,'.ddcsequences')
    else:
        logSaveFilePath = filepath
    dt = datetime.now().strftime("%Y-%m-%dT%H%M%S")

    logFile = join(logSaveFilePath, "{}_{}.log".format(filename, dt))
    if not os.path.exists(logSaveFilePath):
        os.makedirs(logSaveFilePath)
    fh = logging.FileHandler(logFile)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s [%(funcName)s]"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
