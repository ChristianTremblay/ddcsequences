#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Functions and objects related to PID testing
"""
import logging

from .tools import detect_rise_in_output, detect_drop_in_output, var_name

log = logging.getLogger("sequence.pid")


class PID_Loop:
    """
    PID Loop parameters
    """

    def __init__(
        self,
        pv=None,
        setpoint=None,
        output=None,
        offset=None,
        direct_acting=None,
        name="PID Loop",
    ):
        self.pv = pv
        self.setpoint = setpoint
        self.output = output
        self.offset = offset
        self.direct_acting = direct_acting
        self.name = name

    def validate(self, *, callback=None, timeout=180):
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
        log.info(
            "\n \
                                   *******************************\n \
                                   | Testing PID %s               \n \
                                   *******************************"
            % self.name
        )
        try:
            initial_pv_value = self.pv.value
            initial_out_value = self.output.value
        except AttributeError:
            raise AttributeError(
                "You must provide PV and Output as a BAC0 point variable"
            )
        log.info("Waiting one minute to gather data")

        if self.direct_acting:
            # Output should rise if PV is greater than setpoint (cooling)
            log.info(
                "Setting process value (%s) higher than setpoint (%s)"
                % (var_name(self.pv), self.setpoint.value)
            )
            self.pv._set(self.setpoint + self.offset)
            result = detect_rise_in_output(self.output, timeout=300, maximum=100)
            if result:
                log.info(
                    "PID (%s) is working correctly, there has been a rise in the value"
                    % self.name
                )
                res += 1
            else:
                log.error("PID (%s) is not working" % self.name)
            log.info(
                "Setting process value (%s) lower than setpoint (%s)"
                % (var_name(self.pv), self.setpoint.value)
            )
            self.pv._set(self.setpoint - self.offset)
            result = detect_drop_in_output(self.output, timeout=300, minimum=0)
            if result:
                log.info(
                    "PID (%s) is working correctly, there has been a drop in the value"
                    % self.name
                )
                res += 1
            else:
                log.error("PID (%s) is not working" % self.name)

        else:
            # Output should rise if PV is less than setpoint (heating)
            log.info(
                "Setting process value (%s) lower than setpoint (%s)"
                % (var_name(self.pv), self.setpoint.value)
            )
            self.pv._set(self.setpoint - self.offset)
            result = detect_rise_in_output(self.output, timeout=300, maximum=100)
            if result:
                log.info(
                    "PID (%s) is working correctly, there has been a rise in the value"
                    % self.name
                )
            else:
                log.error("PID (%s) is not working" % self.name)
            log.info(
                "Setting process value (%s) higher than setpoint (%s)"
                % (var_name(self.pv), self.setpoint.value)
            )
            self.pv._set(self.setpoint + self.offset)
            result = detect_drop_in_output(self.output, timeout=300, minimum=0)
            if result:
                log.info(
                    "PID (%s) is working correctly, there has been a drop in the value"
                    % self.name
                )
            else:
                log.error("PID (%s) is not working" % self.name)
        self.pv._set(initial_pv_value)
        if res == 2:
            log.info("PID tests worked correctly")
        elif res == 1:
            log.error("At least one test failed")
        else:
            log.error("PID tests faileds")
        # State is now correct, execute callback
        if callback is not None:
            callback()


class Flow_PID_Loop(PID_Loop):
    """
    PID Loop parameters
    """

    def __init__(
        self,
        pv=None,
        setpoint=None,
        output=None,
        offset=None,
        direct_acting=None,
        name="PID Loop",
    ):
        self.pv = pv
        self.setpoint = setpoint
        self.output = output
        self.offset = offset
        self.direct_acting = direct_acting
        self.name = name
