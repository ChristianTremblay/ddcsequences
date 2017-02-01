#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This modules contains helper functions to be used with BAC0 to test
DDC Sequences of operation
"""
from threading import Thread
from . import ddclog

from collections import deque
import logging


class Sequence(object):
    def __init__(self, name = None):

        if name:
            self._create_logger(name)
        else:
            raise NameError('You must give a name to the sequence')
        self.tasks_processor = Tasks_Processor()
        self.start()
        
    def _create_logger(self, name):
        self.log = ddclog.createLogger('sequence', filename = name)
        self.log.info('log (sequence) has been created. Use log.level(message) to add something')
        fh = self.log.handlers[0]
        fn = fh.baseFilename
        self.log.info('A file with all logs can be found here : %s' % fn)
    
    def add_task(self, task, *, name = 'unknown'):
        self.tasks_processor.add_task(task, name)
    
    @property    
    def tasks(self):
        return self._tasks
        
    def start(self):
        self.tasks_processor.start()

    def stop(self):
        self.tasks_processor.stop()  
        self.tasks_processor.join()
        

            
class Tasks_Processor(Thread):

        # Init thread running server
        def __init__(self,*, daemon = True):
            Thread.__init__(self, daemon = daemon)
            self._tasks = deque()
            self.exitFlag = False
            self.log = logging.getLogger('sequence')
            
        def add_task(self, task, name = 'unknown'):
            self.log.debug('Added task : %s' % name)
            self._tasks.append((task, name))
            
        def run(self):
            self.log.debug('Starting task processor')
            self.process()
    
        def process(self):
            while not self.exitFlag:
            #    self.task()
                while self._tasks:
                    task, name = self._tasks.popleft()
                    self.log.info('Running : %s' % name)
                    task()

        def stop(self):
            self.log.debug('Stopping task processor')
            self.exitFlag = True
    
        def beforeStop(self):
            """
            Action done when closing thread
            """
            pass