#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
from ...sequence import Sequence
from .utils import ZNT_State, Econo_and_Mech, DAT_State, Reheat, Dampers, AHU_Cooling, SupplyFan, GEF, Relief_Fan, MASD_State, Sensors_Feedback

class AHU(Sequence, ZNT_State, Econo_and_Mech, DAT_State, Reheat, Dampers, AHU_Cooling, SupplyFan, GEF, Relief_Fan, MASD_State, Sensors_Feedback):
    """
    Basic tests done on a AHU
    """
    def __init__(self, controller):
        super(AHU, self).__init__(controller)
        self.controller['DA-T'] = 20
        self.controller['BLDG-P'] = 0
        self.controller['ZN-T'] = 22        
        self.controller['RA-H'] = 30
        self.controller['OA-T'] = 20

        self.controller['RA-T'].match_value(self.fake_rat)
        self.controller['DA-T'].match_value(self.dat_feedback)
        
        # Expansion disconnected
        self.controller['HTG1-C'].out_of_service()
        self.controller['HTG2-C'].out_of_service()
        
        # Reset evrything
        self.controller['SYS-RESET'] = 'Reset'
        self.controller['TUNING-RESET'] = True
        self.controller['SYS-RESET'] = 'Off'
        self.controller['TUNING-RESET'] = False
        # Fan status
        self.controller['SF-S'].match(self.controller['SF-C'])
        self.controller['RLF-S'].match(self.controller['RLF-C'])
        self.controller['GEF-S'].match(self.controller['GEF-C'])
        

        self.define_task(self.test_AHU)
        print('Use start() to begin process')
    
        
    def test_AHU(self):
        self.note("Let's begin")
        self.fan_should_start()
        self.gef_is_on()
        
        # HEATING
        self.to_heating()
        self.reheat_should_start()
        self.dampers_should_open_to_minimum()
        
        # SATISFIED
        self.to_satisfied()
        self.reheat_should_stop()
        
        # COOLING - ECONO
        self.to_econo()
        self.to_cooling()
        self.dampers_should_modulate()
        
        # COOLING - MECH
        self.to_mech()
        self.dampers_should_open_to_minimum()
        self.ahu_cooling_should_start()
        
        # SATISFIED
        self.to_satisfied()
        self.ahu_cooling_should_stop()
        
        # Building pressure 
        bldg_sp = self.controller['BLDGP-SP'].value
        self.controller['BLDG-P'].write(bldg_sp + 10)
        self.rlf_fan_should_modulate()
        self.controller['BLDG-P'].write(bldg_sp - 10)
        self.rlf_fan_should_stop()
        
        
