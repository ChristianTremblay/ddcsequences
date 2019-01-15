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
import queue
from . import ddclog

import logging


class Sequence(object):
    """
    This object stores all the tasks needed to simulate and test the sequence.
    It also contains everything to create the log file that will hold every 
    actions, task and comment made during the tests.
    """

    def __init__(self, name=None):
        if name:
            self._create_logger(name)
        else:
            raise NameError("You must give a name to the sequence of operation")

        self.start()

    def _create_logger(self, name):
        self.log = ddclog.createLogger("sequence", filename=name)
        self.log.info(
            '\n \
                       =====================================================\n \
                       =               MESSAGE TO READER                   =\n \
                       =====================================================\n \
                      \n \
                      This log will hold every note on the test sequence.\n \
                      In the Jupyter Notebook, every usage of log.level(message)\n \
                      will add something to this log.\n \
                      By default, "- INFO -" means the test is succesful.\n \
                      "- ERROR -" will indicate problems in the test and inform you of the trouble\n \
                      In the Notebook, only ERROR will show.\n'
        )
        fh = self.log.handlers[0]
        fn = fh.baseFilename
        self.log.info("A file with all logs can be found here : %s\n" % fn)

    def add_task(self, task, *, name="unknown", callback=None):
        try:
            self.tasks_processor.add_task(task, name)
            if callback:
                self.log.debug("Executing callback")
                self.tasks_processor.add_task(callback, "callback")
        except AttributeError:
            self.log.critical("sequence not running, use start()")

    @property
    def tasks(self):
        return self.tasks_processor._tasks

    def start(self):
        try:
            self.tasks_processor.start()
        except AttributeError:
            self.tasks_processor = Tasks_Processor()
            self.start()

    def stop(self):
        self.tasks_processor.stop()
        del self.tasks_processor

    @property
    def progress(self):
        task_list, processing = self.tasks_processor.tasks_to_process()
        if processing[0]:
            if task_list:
                return "Processing %s. Next tasks : %s" % (processing[1], task_list)
            else:
                return "Processing %s. Nothing more to do." % (processing[1])
        else:
            return "Nothing to process"


class Tasks_Processor(Thread):
    """
    Task processor is a thread that will execute tasks one after another.
    Task are sent to the sequence object and executed as soon as possible.
    """

    # Init thread running server
    def __init__(self, *, daemon=True):
        Thread.__init__(self, daemon=daemon)
        self._tasks = queue.Queue()
        self.exitFlag = False
        self.log = logging.getLogger("sequence")
        self.processing = [False, ""]

    def add_task(self, task, name="unknown"):
        self.log.debug("Added task : %s" % name)
        self._tasks.put((task, name))

    def tasks_to_process(self):
        tasks_list = []
        for each in self._tasks.queue:
            tasks_list.append(each[1])
        return (tasks_list, self.processing)

    def run(self):
        self.log.debug("Starting task processor")
        self.process()

    def process(self):
        """
        Main loop executing tasks.
        """
        while not self.exitFlag:
            #    self.task()
            while self._tasks:
                task, name = self._tasks.get()
                log = logging.getLogger("sequence.%s" % name)
                print(log.name)
                self.processing = [True, name]
                self.log.info(
                    "\n \
                               ==========================================\n \
                               = Running : %s\n \
                               =========================================="
                    % name
                )
                task()
                self._tasks.task_done()
                self.processing = [False, ""]
                log = logging.getLogger("sequence")

            self.processing = [False, ""]

    def stop(self):
        self.log.debug("Stopping task processor")
        self.exitFlag = True

    def beforeStop(self):
        """
        Action done when closing thread
        """
        pass
