#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
from ...sequence import Sequence
from .utils import ZNT_State, Econo_and_Mech, DAT_State, Reheat, Dampers, AHU_Cooling, SupplyFan, GEF, Relief_Fan


class AHU(Sequence, ZNT_State, Econo_and_Mech, DAT_State, Reheat, Dampers, AHU_Cooling, SupplyFan, GEF, Relief_Fan):
    """
    Basic tests done on a AHU
    """
    def __init__(self, controller):
        super(AHU, self).__init__(controller)
        self.controller['DA-T'] = 20
        self.controller['BLDG-P'] = 0
        self.controller['GEF-S'] = False
        self.controller['RA-H'] = 30
        self.controller['RA-T'] = 21
        self.controller['RLF-S'] = False
        self.controller['SF-S'].match(self.controller['SF-C'])
        self.controller['ZN-T'] = 22
        
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
        
        
