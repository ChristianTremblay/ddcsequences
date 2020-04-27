# -*- coding: utf-8 -*-
"""
Created on Sun Aug 14 22:41:56 2016

@author: CTremblay
"""


class JCI_Enum(object):

    StartStop_States = {
        "Off": 1,
        "SF Starts First": 2,
        "RF Starts First": 3,
        "Ramp SF": 4,
        "Stabilize System": 5,
        "Ramp Min OA": 6,
        "On": 7,
        "Close Dampers": 8,
        "RF Stops First": 9,
        "SF Stops First": 10,
        "Fans Off": 11,
        "Fan Fault": 12,
    }
    Occ_Schedule = {"Occupied": 1, "UnOccupied": 2, "Standby": 3, "Not Set": 4}

    Dehum_States = {"No Dehumid": 1, "Normal Dehumid": 2, "Humidity Unreliable": 3}

    Ahu_States = {
        "Satisfied": 1,
        "Econ": 2,
        "Econ+Mech": 3,
        "HX Cool+Mech": 4,
        "HX Heat": 5,
        "HX Heat+Preheat": 6,
        "HX Heat+Preheat+Reheat": 7,
        "Cooling Idle": 8,
        "Heating Idle": 9,
        "Temperature Unreliable": 10,
    }
