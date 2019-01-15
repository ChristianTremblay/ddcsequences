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
import numpy as np

log = logging.getLogger("sequence")


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
        name = "%s (%s)" % (prop.name, prop.description)
    except AttributeError:
        name = "(name not found)"
    return name


def wait_for_state(point, state, *, callback=None, timeout=180):
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
            add_note(
                point.properties.device,
                "%s is now in state %s" % (var_name(point), state),
            )
            break
        elif time.time() > tout:
            # raise TimeoutError('Wrong state after waiting a long time.')
            add_error(
                point.properties.device,
                "Timeout : %s in wrong state (%s != %s) after %s sec"
                % (var_name(point), format_variable_value(point), state, timeout),
            )
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()


def wait_for_state_not(point, state, *, callback=None, timeout=180):
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
            add_note(
                point.properties.device,
                "%s left state %s for %s" % (var_name(point), state, point.value),
            )
            break
        elif time.time() > tout:
            add_error(
                point.properties.device,
                "Timeout : %s didn't change state (%s == %s) after %s sec"
                % (var_name(point), format_variable_value(point), state, timeout),
            )
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()


def wait_for_value_gt(point, value, *, callback=None, timeout=90, maximum=None):
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

    def test_max(point, maximum):
        if maximum:
            if point.value == maximum:
                return True
        else:
            return False

    tout = time.time() + timeout
    while True:
        if point.value > value or test_max(point, maximum):
            add_note(
                point.properties.device,
                "%s is greater than %.2f (value = %s or has reached maximum value)"
                % (var_name(point), value, format_variable_value(point)),
            )
            break
        elif time.time() > tout:
            # raise TimeoutError('Variable not yet greater than value after timeout')
            add_error(
                point.properties.device,
                "Timeout : %s (value = %s) not greater than %.2f after %s sec"
                % (var_name(point), format_variable_value(point), value, timeout),
            )
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()


def wait_for_value_lt(point, value, *, callback=None, timeout=90, minimum=None):
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

    def test_min(point, minimum):
        if minimum:
            if point.value == minimum:
                return True
        else:
            return False

    tout = time.time() + timeout
    while True:
        if point.value < value or test_min(point, minimum):
            add_note(
                point.properties.device,
                "%s is less than %.2f (value = %s or has reached minimum value)"
                % (var_name(point), value, point),
            )
            break
        elif time.time() > tout:
            # raise TimeoutError('Variable not yet less than value after timeout')
            add_error(
                point.properties.device,
                "Timeout : %s (value = %s) not less than %.2f after %s sec"
                % (var_name(point), format_variable_value(point), value, timeout),
            )
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()


def check_that(point, value, *, callback=None, timeout=90):
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
            add_note(point.properties.device, "%s is %s" % (var_name(point), value))
            break
        elif time.time() > tout:
            add_error(
                point.properties.device,
                "Problem : %s is not %s, it is %s after %s sec"
                % (var_name(point), value, format_variable_value(point), timeout),
            )
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()


def check_isclose(point, value, *, rtol=1e-02, atol=1e-02, callback=None, timeout=90):
    """
    This function will read a point and check if its value is closed to the value
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
        if np.isclose(point.value, value, rtol=rtol, atol=atol):
            add_note(
                point.properties.device, "%s is close to %s" % (var_name(point), value)
            )
            break
        elif time.time() > tout:
            add_error(
                point.properties.device,
                "Problem : %s is not close to %s, it is %s after %s sec"
                % (var_name(point), value, format_variable_value(point), timeout),
            )
            break
        time.sleep(2)
    # State is now correct, execute callback
    if callback is not None:
        callback()


def detect_rise_in_output(output, timeout=300, minimum=None, maximum=None):
    """
    This function will monitor an output and check if there is a growing
    trend. If the output gets higher with time.
    
    Three tests will be made and if at least test #3 is greater than test #1 
    we will consider that the output is rising (success).
    
    :param output: BAC0.point
    :param minimum: float lowest possible value
    :param maximum: float highest possible value
    :param timeout: float timeout duration in seconds
    """
    timeout_each_test = (timeout - 3) / 3
    initial_out_value = output.value
    wait_for_value_gt(
        output, initial_out_value, timeout=timeout_each_test, maximum=maximum
    )
    time.sleep(20)
    second_out_value = output.value
    wait_for_value_gt(
        output, second_out_value, timeout=timeout_each_test, maximum=maximum
    )
    time.sleep(20)
    third_out_value = output.value
    wait_for_value_gt(
        output, third_out_value, timeout=timeout_each_test, maximum=maximum
    )
    if (
        third_out_value > second_out_value and second_out_value > initial_out_value
    ) or (third_out_value > initial_out_value):
        return True
    else:
        return False


def detect_drop_in_output(output, timeout=300, minimum=None, maximum=None):
    """
    This function will monitor an output and check if there is a droping
    trend. If the output gets lower with time.
    
    Three tests will be made and if at least test #3 is less than test #1 
    we will consider that the output is droping (success).
    
    :param output: BAC0.point
    :param minimum: float lowest possible value
    :param maximum: float highest possible value
    :param timeout: float timeout duration in seconds
    """
    timeout_each_test = (timeout - 3) / 3
    initial_out_value = output.value
    wait_for_value_lt(
        output, initial_out_value, timeout=timeout_each_test, minimum=minimum
    )
    time.sleep(20)
    second_out_value = output.value
    wait_for_value_lt(
        output, second_out_value, timeout=timeout_each_test, minimum=minimum
    )
    time.sleep(20)
    third_out_value = output.value
    wait_for_value_lt(
        output, third_out_value, timeout=timeout_each_test, minimum=minimum
    )
    if (
        third_out_value < second_out_value and second_out_value < initial_out_value
    ) or (third_out_value < initial_out_value):
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
        if "multiState" in var_type:
            return point.enumValue
        elif "binary" in var_type:
            return point.boolValue
        elif "analog" in var_type:
            return "%.2f %s" % (point.value, var_prop.units_state)
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
        add_note(
            point.properties.device,
            "%s has been adjusted to %s"
            % (var_name(point), format_variable_value(point)),
        )
    except:
        add_error(
            point.properties.device,
            "%s has not been adjusted to %s and is still %s"
            % (var_name(point), value, format_variable_value(point)),
        )


def which_pump(pump_1, pump_2):
    if pump_1:
        active_pump = 1
    elif pump_2:
        active_pump = 2
    else:
        active_pump = 0
    return active_pump


def check_pump_rotation(rotation_point, pump_1, pump_2, *, name=""):
    """
    Pump rotation test
    
    :param rotation_point: BAC0.point
    :param pump_1: BAC0.point
    :param pump_2: BAC0.point
    :param name: str (ex. CW, PHW, etc...)
    
    """
    pump_before = which_pump(pump_1, pump_2)
    add_note(rotation_point.properties.device, "Forcing pump rotation")
    adjust(rotation_point, True)
    adjust(rotation_point, False)
    pump_after = which_pump(pump_1, pump_2)
    add_note(
        rotation_point.properties.device,
        "Before rotation : %s Pump %s" % (name, pump_before),
    )
    add_note(
        rotation_point.properties.device,
        "After rotation : %s Pump %s" % (name, pump_after),
    )
    if pump_after != pump_before:
        add_note(rotation_point.properties.device, "Rotation succeeded")
    else:
        add_error(rotation_point.properties.device, "Rotation failed")


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
        df = pd.DataFrame({"value": point.history})
        df["enum"] = df["value"].apply(fn)
        return df["enum"]

    except AttributeError:
        raise AttributeError("Must provide a BAC0.point history")


class diff_press:
    """
    Custom class that mimic a BAC0.point to modify 2 pressure inputs so the diff pressure is what we want.
    """

    def __init__(self, succion_press=None, disch_press=None, device_result=None):
        self.rp = succion_press
        self.dp = disch_press
        self.result = device_result

    def _set(self, value):
        adjust(self.dp, self.rp.value + value)
        add_note(
            self.rp.properties.device,
            "Differential pressure is now %.2f psi" % self.value,
        )

    @property
    def value(self):
        return self.result.value

    @property
    def properties(self):
        return self.succion_press.properties


def add_note(controller, note):
    log.info(note)
    controller.notes = note


def add_error(controller, note):
    log.error(note)
    controller.notes = note
