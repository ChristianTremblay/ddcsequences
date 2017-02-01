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
import logging

log = logging.getLogger('sequence')
   
def wait_for_state(variable, state, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable == state:
            log.info('%s is now %s' % (variable, state))
            break
        elif time.time() > tout:
            #raise TimeoutError('Wrong state after waiting a long time.')
            log.error('Timeout : Wrong state (%s) after waiting a long time (%s sec).' % (state, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()

   
def wait_for_state_not(variable, state, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable != state:
            log.info('%s is no more %s' % (variable, state))
            break
        elif time.time() > tout:
            log.error('Timeout : Wrong state (%s) after waiting a long time (%s sec).' % (state, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        
        
def wait_for_value_gt(variable, value, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable > value:
            log.info('%s is greater than %s' % (variable, value))
            break
        elif time.time() > tout:
            #raise TimeoutError('Variable not yet greater than value after timeout')
            log.error('Variable (%s) not yet greater than value (%s) after timeout (%s sec)' % (variable, value, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        

def wait_for_value_lt(variable, value, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable < value:
            return ('%s is less than %s' % (variable, value))
            break
        elif time.time() > tout:
            #raise TimeoutError('Variable not yet less than value after timeout')
            log.error('Variable (%s) not yet less than value (%s) after timeout (%s sec)' % (variable, value, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()
        
def check_that(variable, value):
    if variable == value:
        log.info('%s is %s' % (variable.property.name, value))
    else:
        log.error('Problem : %s is not %s' % (variable.property.name, value))