# -*- coding: utf-8 -*-
"""
Created on Sun Apr 19 10:29:28 2015

@author: CTremblay
"""
import os
import logging 
from os.path import expanduser

from datetime import datetime

def createLogger(name, filepath = None, filename = None):
    # create logger with 'spam_application'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    if filepath == None:
        logUserPath = expanduser('~')
        logSaveFilePath = r'%s\.ddcsequences' %(logUserPath)
    else:
        logSaveFilePath = filepath
    dt = datetime.now().strftime('%Y-%m-%dT%H%M%S')

    logFile = logSaveFilePath+'\\' + filename + '_' + dt + '.log'
    if not os.path.exists(logSaveFilePath):
        os.makedirs(logSaveFilePath)
    fh = logging.FileHandler(logFile)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger