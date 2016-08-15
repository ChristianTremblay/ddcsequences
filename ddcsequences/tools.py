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

def wait_for_state(variable, state, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable == state:
            variable.properties.device.notes = '%s is now %s' % (variable, state)
            break
        elif time.time() > tout:
            raise TimeoutError('Wrong state after waiting a long time.')
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()

def wait_for_state_change(variable, state, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable != state:
            variable.properties.device.notes = '%s is no more %s' % (variable, state)
            break
        elif time.time() > tout:
            raise TimeoutError('Same state after waiting a long time.')
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        
        
