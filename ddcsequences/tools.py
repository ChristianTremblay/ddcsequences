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

def var_name(variable):
    try:
        # Will work if variable is a BAC0 point
        prop = variable.properties
        name = '%s (%s)' % (prop.name, prop.description)
    except TypeError:
        name = "(name not found)"
    return name
   
def wait_for_state(variable, state, *, callback = None, timeout=180):
    tout = time.time() + timeout
    while True:
        if variable == state:
            log.info('%s is now in state %s' % (var_name(variable), state))
            break
        elif time.time() > tout:
            #raise TimeoutError('Wrong state after waiting a long time.')
            log.error('Timeout : %s in wrong state (%s != %s) after %s sec' % (var_name(variable), format_variable_value(variable), state, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()

   
def wait_for_state_not(variable, state, *, callback = None, timeout=180):
    tout = time.time() + timeout
    while True:
        if variable != state:
            log.info('%s left state %s for %s' % (var_name(variable), state, variable.value))
            break
        elif time.time() > tout:
            log.error("Timeout : %s didn't change state (%s == %s) after %s sec" % (var_name(variable), format_variable_value(variable), state, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        
        
def wait_for_value_gt(variable, value, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable > value:
            log.info('%s is greater than %s (value = %2f0)' % (var_name(variable), value, variable))
            break
        elif time.time() > tout:
            #raise TimeoutError('Variable not yet greater than value after timeout')
            log.error('Timeout : %s (value = %.2f) not greater than %.2f after %s sec' % (var_name(variable), value, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        

def wait_for_value_lt(variable, value, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable < value:
            return ('%s is less than %s (value = %2f0)' % (var_name(variable), value, variable))
            break
        elif time.time() > tout:
            #raise TimeoutError('Variable not yet less than value after timeout')
            log.error('Timeout : %s (value = %.2f) not less than %.2f after %s sec' % (var_name(variable), value, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()
        
def check_that(variable, value, *, callback = None, timeout=90):
    tout = time.time() + timeout
    while True:
        if variable == value:
            log.info('%s is %s' % (var_name(variable), value))
            break
        elif time.time() > tout:
            log.error('Problem : %s is not %s, it is %s after %s sec' % (var_name(variable), value, format_variable_value(variable), timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()

def format_variable_value(variable):
    try:
        var_prop = variable.properties
        var_type = var_prop.type
        if 'multiState' in var_type:
            return variable.enumValue
        elif 'binary' in var_type:
            return variable.boolValue
        elif 'analog' in var_type:            
            return '%.2f %s' % (variable.value, var_prop.units_state)    
    except TypeError:
        return variable    
