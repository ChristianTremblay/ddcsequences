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
import time
import BAC0.core.devices.Device as BAC0_device

class Sequence(object):
    def __init__(self, controller):
        if controller is BAC0_device:
            self.controller = controller
        else:
            raise TypeError('Controller must be a BAC0 device')
        
    def note(self, text):
        self.controller.notes = text
        print(text)
    
        
    def wait_for_state(self, variable, state, callback = None, timeout=90):
        tout = time.time() + timeout
        while True:
            if variable == state:
                self.note = '%s is now %s' % (variable, state)
                break
            elif time.time() > tout:
                raise TimeoutError('Wrong state after waiting a long time.')
            time.sleep(2)
        # State is now correct, execute callback
        if callback is not None:
            callback()
    
       
    def wait_for_state_not(self, variable, state, callback = None, timeout=90):
        tout = time.time() + timeout
        while True:
            if variable != state:
                self.note = '%s is no more %s' % (variable, state)
                break
            elif time.time() > tout:
                raise TimeoutError('Same state after waiting a long time.')
            time.sleep(2)
        # State is now correct, execute callback
        if callback is not None:
            callback()        
            
    def wait_for_value_gt(self, variable, value, callback = None, timeout=90):
        tout = time.time() + timeout
        while True:
            if variable > value:
                self.note = '%s is greater than %s' % (variable, value)
                break
            elif time.time() > tout:
                raise TimeoutError('Variable not yet greater than value after timeout')
            time.sleep(2)
        # State is now correct, execute callback
        if callback is not None:
            callback()        

    def wait_for_value_lt(self, variable, value, callback = None, timeout=90):
        tout = time.time() + timeout
        while True:
            if variable < value:
                self.note = '%s is less than %s' % (variable, value)
                break
            elif time.time() > tout:
                raise TimeoutError('Variable not yet less than value after timeout')
            time.sleep(2)
        # State is now correct, execute callback
        if callback is not None:
            callback()