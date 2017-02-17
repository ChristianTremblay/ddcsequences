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
import pandas as pd

log = logging.getLogger('sequence')

def var_name(point):
    """
    Given a BAC0 point, return a formatted string in the form 
    name (description)
    
    :param point: BAC0.point
    :returns: formatted string
    """
    try:
        # Will work if variable is a BAC0 point
        prop = point.properties
        name = '%s (%s)' % (prop.name, prop.description)
    except AttributeError:
        name = "(name not found)"
    return name
   
def wait_for_state(point, state, *, callback = None, timeout=180):
    """
    This function will read a point and wait for its state to match the 
    state parameter value. Common use case is to wait until a point reach 
    a specified state. Ex. In a controller, ZNT-STATE (Zone temperature state)
    can have multiple states like Heating, Cooling, Satisfied, ...
    To be able to validate that heating works correctly, we must first wait for
    the controller to be in heating mode.
    
    A timeout will trig an error if the function is waiting for too long.
    
    Output will be log as an info when success or an error in case of a timeout
    
    :param point: BAC0.point
    :param state: String
    :param callback: function (optional)
    :param timeout: float
    
    """
    tout = time.time() + timeout
    while True:
        if point == state:
            log.info('%s is now in state %s' % (var_name(point), state))
            break
        elif time.time() > tout:
            #raise TimeoutError('Wrong state after waiting a long time.')
            log.error('Timeout : %s in wrong state (%s != %s) after %s sec' % (var_name(point), format_variable_value(point), state, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()

   
def wait_for_state_not(point, state, *, callback = None, timeout=180):
    """
    This function will read a point and wait for its state to diverge from the 
    state parameter value. Common use case is to wait until a point quits 
    a specified state. 
    
    A timeout will trig an error if the function is waiting for too long.
    
    Output will be log as an info when success or an error in case of a timeout
    
    :param point: BAC0.point
    :param state: String
    :param callback: function (optional)
    :param timeout: float
    
    """
    tout = time.time() + timeout
    while True:
        if point != state:
            log.info('%s left state %s for %s' % (var_name(point), state, point.value))
            break
        elif time.time() > tout:
            log.error("Timeout : %s didn't change state (%s == %s) after %s sec" % (var_name(point), format_variable_value(point), state, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        
        
def wait_for_value_gt(point, value, *, callback = None, timeout=90):
    """
    This function will read a point and wait for its value to be greater than 
    the value parameter. 
    
    A timeout will trig an error if the function is waiting for too long.
    
    Output will be log as an info when success or an error in case of a timeout
    
    :param point: BAC0.point
    :param value: float
    :param callback: function (optional)
    :param timeout: float
    
    """
    tout = time.time() + timeout
    while True:
        if point.value > value:
            log.info('%s is greater than %.2f (value = %s)' % (var_name(point), value, format_variable_value(point)))
            break
        elif time.time() > tout:
            #raise TimeoutError('Variable not yet greater than value after timeout')
            log.error('Timeout : %s (value = %s) not greater than %.2f after %s sec' % (var_name(point), format_variable_value(point), value, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()        

def wait_for_value_lt(point, value, *, callback = None, timeout=90):
    """
    This function will read a point and wait for its value to be less than 
    the value parameter. 
    
    A timeout will trig an error if the function is waiting for too long.
    
    Output will be log as an info when success or an error in case of a timeout
    
    :param point: BAC0.point
    :param value: float
    :param callback: function (optional)
    :param timeout: float
    
    """
    tout = time.time() + timeout
    while True:
        if point.value < value:
            return ('%s is less than %.2f (value = %s)' % (var_name(point), value, point))
            break
        elif time.time() > tout:
            #raise TimeoutError('Variable not yet less than value after timeout')
            log.error('Timeout : %s (value = %s) not less than %.2f after %s sec' % (var_name(point), format_variable_value(point), value, timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()
        
def check_that(point, value, *, callback = None, timeout=90):
    """
    This function will read a point and check if its value fits the value
    parameter.
    
    A timeout will trig an error if the function is waiting for too long.
    
    Output will be log as an info when success or an error in case of a timeout
    
    :param point: BAC0.point
    :param value: float or string
    :param callback: function (optional)
    :param timeout: float
    
    """
    tout = time.time() + timeout
    while True:
        if point == value:
            log.info('%s is %s' % (var_name(point), value))
            break
        elif time.time() > tout:
            log.error('Problem : %s is not %s, it is %s after %s sec' % (var_name(point), value, format_variable_value(point), timeout))
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()

def check_pid(pv, setpoint, output, *, offset = 3, direct_acting = True, name = 'unknown', callback = None, timeout=180):
    """
    This function will validate if a PID loop is acting correctly.
    
    How
    ==========
    Direct Acting
    ---------------
    If the PID is said to be direct acting (direct_acting = True, default), it 
    is a PID with an output that will rise if the process value (PV) rise 
    compared to the setpoint. It's a "cooling PID".
    
    The function will adjust the process value (simulation of the input) to be
    greater than the setpoint (adding the offset parameter to the setpoint).
    
    Function will then wait for a rise in the output. See function : 
        detect_rise_in_output
        
    Once it's done, the function will revert the action by adjusting the process
    value to be less than the setpoint (substracting the offset parameter to 
    the setpoint).
    
    Function will then wait for a drop in the output. See function : 
        detect_drop_in_output

    Reverse Acting
    ---------------    
    If the PID is said to be reverse acting (direct_acting = False), it is a 
    PID with an output that will rise if the process value (PV) drops compared 
    to the setpoint. It's a "heating PID".

    The function will adjust the process value (simulation of the input) to be
    less than the setpoint (substracting the offset parameter to the setpoint).
    
    Function will then wait for a rise in the output. See function : 
        detect_rise_in_output

    Once it's done, the function will revert the action by adjusting the process
    value to be greater than the setpoint (adding the offset parameter to 
    the setpoint).
    
    Function will then wait for a drop in the output. See function : 
        detect_drop_in_output    
    
    Timeout
    -------
    A timeout will trig an error if the function is waiting for too long.
    
    Log
    ---
    Output will be log as an info when success or an error in case of a timeout
    
    :param pv: BAC0.point (The process value)
    :param setpoint: BAC0.point (The setpoint)
    :param output: BAC0.point (The output driven by the PID Loop)
    :param offset: float (offset of the pv compared to the setpoint to force an action)
    :param direct_acting: boolean (Action of the PID)
    :param name: str (Name of the PID for logging)
    :param callback: function (optional)
    :param timeout: float
    
    """
    res = 0
    log.info('*******************************\n \
              | Testing PID %s               \n \
              *******************************' % name)
    try:
        initial_pv_value = pv.value
        initial_out_value = out.value
    except AttributeError:
        raise AttributeError('You must provide PV and Output as a BAC0 point variable')
    log.info('Waiting one minute to gather data')

    if direct_acting:
        # Output should rise if PV is greater than setpoint (cooling)
        log.info('Setting process value (%s) higher than setpoint (%s)' % (var_name(pv), setpoint.value) )
        pv._set(setpoint + 3)
        result = detect_rise_in_output(output, timeout=30)
        if result : 
            log.info('PID (%s) is working correctly, there has been a rise in the value' % name)
            res += 1
        else:
            log.error('PID (%s) is not working' % name)
        log.info('Setting process value (%s) lower than setpoint (%s)' % (var_name(pv), setpoint.value) )
        pv._set(setpoint - 3)
        result = detect_drop_in_output(output, timeout=30)
        if result : 
            log.info('PID (%s) is working correctly, there has been a drop in the value' % name) 
            res += 1
        else:
            log.error('PID (%s) is not working' % name)

    else:
        # Output should rise if PV is less than setpoint (heating)
        log.info('Setting process value (%s) lower than setpoint (%s)' % (var_name(pv), setpoint.value) )
        pv._set(setpoint - 3)
        result = detect_rise_in_output(output, timeout=30)
        if result : 
            log.info('PID (%s) is working correctly, there has been a rise in the value' % name)
        else:
            log.error('PID (%s) is not working' % name)
        log.info('Setting process value (%s) higher than setpoint (%s)' % (var_name(pv), setpoint.value) )
        pv._set(setpoint + 3)
        result = detect_drop_in_output(output, timeout=30)
        if result : 
            log.info('PID (%s) is working correctly, there has been a drop in the value' % name)            
        else:
            log.error('PID (%s) is not working' % name)                    
    pv._set(initial_pv_value)
    if res == 2:
        log.info('PID tests worked correctly')
    elif res == 1:
        log.error('At least one test failed')
    else:
        log.error('PID tests faileds')
    # State is now correct, execute callback
    if callback is not None:
        callback()                        

def detect_rise_in_output(output, timeout = 30):
    """
    This function will monitor an output and check if there is a growing
    trend. If the output gets higher with time.
    
    Three tests will be made and if at least test #3 is greater than test #1 
    we will consider that the output is rising (success).
    
    :param output: BAC0.point
    :param timeout: float timeout duration in seconds
    """
    timeout_each_test = (timeout - 3) / 3
    initial_out_value = output.value
    wait_for_value_gt(output, initial_out_value, timeout=timeout_each_test)
    time.sleep(1)
    second_out_value = output.value
    wait_for_value_gt(output, second_out_value, timeout=timeout_each_test)
    time.sleep(1)
    third_out_value = output.value
    wait_for_value_gt(output, initial_out_value, timeout=timeout_each_test)
    if (third_out_value > second_out_value and second_out_value > initial_out_value) \
       or (third_out_value > initial_out_value):
        return True
    else:
        return False

def detect_drop_in_output(output, timeout = 30):
    """
    This function will monitor an output and check if there is a droping
    trend. If the output gets lower with time.
    
    Three tests will be made and if at least test #3 is less than test #1 
    we will consider that the output is droping (success).
    
    :param output: BAC0.point
    :param timeout: float timeout duration in seconds
    """
    timeout_each_test = (timeout - 3) / 3
    initial_out_value = output.value
    wait_for_value_lt(output, initial_out_value, timeout=timeout_each_test)
    time.sleep(1)
    second_out_value = output.value
    wait_for_value_lt(output, second_out_value, timeout=timeout_each_test)
    time.sleep(1)
    third_out_value = output.value
    wait_for_value_lt(output, initial_out_value, timeout=timeout_each_test)
    if (third_out_value < second_out_value and second_out_value < initial_out_value) \
       or (third_out_value < initial_out_value):
        return True
    else:
        return False

def format_variable_value(point):
    """
    Helper to format the text of a BAC0.point for logging
    """
    try:
        var_prop = point.properties
        var_type = var_prop.type
        if 'multiState' in var_type:
            return point.enumValue
        elif 'binary' in var_type:
            return point.boolValue
        elif 'analog' in var_type:            
            return '%.2f %s' % (point.value, var_prop.units_state)    
    except AttributeError:
        return point
    
def adjust(point, value):
    """
    This function will write to a BAC0.point and log the action to the file.
    It is a way to assure that every action is written to the log for later
    validation of the sequence.
    
    :param point: BAC0.point
    :param value: float or str
    """
    try:
        point._set(value)
        log.info('%s has been adjusted to %s' % (var_name(point), format_variable_value(point)))
    except:
        log.error('%s has not been adjusted to %s and is still %s' % (var_name(point), value, format_variable_value(point)))

def which_pump(pump_1, pump_2):
    if pump_1:
        active_pump = 1
    elif pump_2:
        active_pump = 2
    else:
        active_pump = 0
    return active_pump

def check_pump_rotation(rotation_point, pump_1, pump_2, *, name=''):
    """
    Pump rotation test
    
    :param rotation_point: BAC0.point
    :param pump_1: BAC0.point
    :param pump_2: BAC0.point
    :param name: str (ex. CW, PHW, etc...)
    
    """
    pump_before = which_pump(pump_1, pump_2)
    log.info('Forcing pump rotation')
    adjust(rotation_point, True)
    adjust(rotation_point, False)
    pump_after = which_pump(pump_1, pump_2)
    log.info('Before rotation : %s Pump %s' % (name, pump_before))
    log.info('After rotation : %s Pump %s' % (name, pump_after))
    if pump_after != pump_before:
        log.info('Rotation succeeded')
    else:
        log.error('Rotation failed')
    
def enum_history(point):
    """
    BAC0 history for enum are by default integer values. It is often more 
    helpful to see the "text" related to the different states.
    
    This function allow to create a 2nd column to the dataframe containing
    the history with the text representation of the states.
    
    :param point: BAC0.point
    :returns: pandas.DataFrame with a 'enum' column.
    """
    def fn(value):
        return states[value]
    try:
        states = point.properties.units_state
        df = pd.DataFrame({'value':point.history})
        df['enum'] = df['value'].apply(fn)
        return df['enum']

    except AttributeError:
        raise AttributeError('Must provide a BAC0.point history')
            
    
class diff_press():
    """
    Custom class that mimic a BAC0.point to modify 2 pressure inputs so the diff pressure is what we want.
    """
    def __init__(self, succion_press = None, disch_press = None, device_result = None):
        self.rp = succion_press
        self.dp = disch_press
        self.result = device_result
    def _set(self, value):
        adjust(self.dp, self.rp.value + value)
        log.info('Differential pressure is now %.2f psi' % self.result)
        
    @property
    def value(self):
        return self.result.value