#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
class Occupancy(object):
    def to_occupied(self):
        self.note('Switching to occupied')
        self.controller['OCC-SCHEDULE'] = 'Occupied'
        self.wait_for_state(self.controller['EFF-OCC'], 'Occupied')

    def to_unoccupied(self):
        self.note('Switching to unoccupied')
        self.controller['OCC-SCHEDULE'] = 'UnOccupied'
        self.wait_for_state(self.controller['EFF-OCC'], 'UnOccupied')

class SupplyFan(object):
    def fan_should_start(self):
        self.wait_for_state(self.controller['STARTSTOP-STATE'], 'On', callback=self.fan_is_on)
    def fan_is_on(self):
        self.wait_for_state(self.controller['SF-C'], 'active')
    def fan_is_off(self):
        self.wait_for_state(self.controller['SF-C'], 'inactive')
        
class GEF(object):
    def gef_is_on(self):
        self.wait_for_state(self.controller['GEF-C'], 'active')
    

class Econo_and_Mech(object):
    def to_econo(self, delta = 5, callback):
        self.note('Switching to econo')
        sp = self.controller['ECONSWO-SP'].value
        self.controller['OA-T'].write(sp - delta)
        self.wait_for_state(self.controller['ECON-AVAILABLE'], 'active')

    def to_mech(self, delta = 5, callback):
        self.note('switching to mechanical cooling')
        sp = self.controller['ECONSWO-SP'].value
        self.controller['OA-T'].write(sp + delta)
        self.wait_for_state(self.controller['ECON-AVAILABLE'], 'inactive')


class ZNT_State(object):
    def to_heating(self, sensor='ZN-T', setpoint='EFFHTG-SP', delta = 5):
        self.note = 'Creating heating demand'
        self.controller[sensor].write(self.controller[setpoint].value - delta)
        self.wait_for_state(self.controller['ZNT-STATE'], 'Heating', callback=self.dat_is_heating)
    
    def to_cooling(self, sensor='ZN-T', setpoint='EFFCLG-SP', delta = 5):
        self.note = 'Creating cooling demand'
        self.controller[sensor].write(self.controller[setpoint].value + delta)
        self.wait_for_state(self.controller['ZNT-STATE'], 'Cooling', callback=self.dat_is_cooling)
    
    def to_satisfied(self, sensor='ZN-T', htg_sp='EFFHTG-SP', clg_sp='EFFCLG-SP'):
        self.note('switching to satisfied')        
        sp = ((self.controller[clg_sp].value - self.controller[htg_sp].value) / 2) + self.controller[htg_sp].value
        self.controller[sensor].write(sp)
        self.wait_for_state(self.controller['ZNT-STATE'], 'Satisfied', callback=self.dat_is_off)
        
class DAT_State(object):
    def dat_is_off(self):
        assert self.controller['DATSP-STATE'] == 'Off'
        self.note = 'DATSP-STATE is Off : Ok'
    def dat_is_heating(self):
        assert self.controller['DATSP-STATE'] == 'Heating DA-T Reset'
        self.note = 'DATSP-STATE is Heating : Ok'
    def dat_is_cooling(self):
        assert self.controller['DATSP-STATE'] == 'Cooling DA-T Reset'
        self.note = 'DATSP-STATE is Cooling : Ok'
        
class Reheat(object):
    def reheat_should_stop(self):
        self.wait_for_state(self.controller['RH-OUTSTATE'], 'Off', callback=self.reheat_is_off)
    def reheat_is_off(self):
        if 'RH-O' in self.controller:
            assert self.controller['RH-O'] == 0
        else:
            assert self.controller['HTG1-C'] == 'inactive'
        self.note = 'Reheat is Off'
    def reheat_should_start(self):
        old_value = self.controller['DA-T'].value
        self.controller['DA-T'].write(10)
        self.note = 'Forcing DA-T to a small value so heating will modulate'        
        self.wait_for_state(self.controller['RH-OUTSTATE'], 'T Control', callback=self.reheat_in_control)
        self.controller['DA-T'].write(old_value)
        self.note = 'Reverting to old DA-T value'

    def reheat_in_control(self):
        """
        Treat RH-O AND HTG stage to cover Vernier
        """
        if 'RH-O' in self.controller:
            self.wait_for_state_not(self.controller['RH-O'], 0)
            self.note = 'Reheat is modulating'

        if 'HTG1-C' in self.controller:
            self.wait_for_state(self.controller['HTG1-C'], 'active')
        if 'HTG2-C' in self.controller:
            self.wait_for_state(self.controller['HTG2-C'], 'active')
        if 'HTG3-C' in self.controller:
            self.wait_for_state(self.controller['HTG3-C'], 'active')
        if 'HTG4-C' in self.controller:
            self.wait_for_state(self.controller['HTG4-C'], 'active')
        self.note = 'All heating stages are working'
        
class Dampers(object):
    def dampers_should_close(self):
        self.wait_for_state(self.controller['MAD-OUTSTATE'], 'Close', callback=self.dampers_closed)
    def dampers_closed(self):
        try:
            self.wait_for_state(self.controller['MAD-O'], 0)
        except KeyError:
            self.wait_for_state(self.controller['OAD-O'], 0)
        self.note = 'Dampers are closed'
    def dampers_should_modulate(self):
        old_value = self.controller['DA-T'].value
        self.controller['DA-T'].write(30)
        self.note = 'Forcing DA-T to a large value so dampers will modulate'
        self.wait_for_state(self.controller['MAD-OUTSTATE'], 'T Control', callback=self.dampers_are_modulating)
        self.controller['DA-T'].write(old_value)
        self.note = 'Reverting to old DA-T value'
        
    def dampers_are_modulating(self):
        if 'MAD-O' in self.controller:
            self.wait_for_value_gt(self.controller['MAD-O'], self.controller['OAD-MINPOS'])
        if 'OAD-O' in self.controller:
            self.wait_for_value_gt(self.controller['OAD-O'], self.controller['OAD-MINPOS'])
        if 'RAD-O' in self.controller:
            self.wait_for_value_lt(self.controller['RAD-O'], 100)

        self.note = 'Dampers are modulating' 
        
    def dampers_should_open_to_minimum(self):
        self.wait_for_state(self.controller['MAD-OUTSTATE'], 'Off', callback=self.dampers_are_at_min_pos)
        
    def dampers_are_at_min_pos(self):
        if 'MAD-O' in self.controller:
            self.wait_for_state_not(self.controller['MAD-O'].value, self.controller['OAD-MINPOS'].value)
        if 'OAD-O' in self.controller:
            self.wait_for_state_not(self.controller['OAD-O'].value, self.controller['OAD-MINPOS'].value)
        if 'RAD-O' in self.controller:
            self.wait_for_state_not(self.controller['OAD-O'].value, 100)

        self.note = 'Dampers are at minimum position'    
        
class AHU_Cooling(object):
    def ahu_cooling_should_stop(self):
        self.wait_for_state(self.controller['CLG-OUTSTATE'], 'Off', callback=self.ahu_cooling_is_off)
    def ahu_cooling_is_off(self):
        self.wait_for_state(self.controller['CLG-OUTSTATE'], 'Off')
        self.note = 'AHU Cooling is Off'
    def ahu_cooling_should_start(self):        
        old_value = self.controller['ZN-T'].value
        self.controller['ZN-T'].write(30)        
        self.note = 'Forcing ZN-T to a large value so cooling stages will modulate'
        self.wait_for_state(self.controller['CLG-OUTSTATE'], 'T Control', callback=self.ahu_cooling_in_control)
        self.controller['ZN-T'].write(old_value)
        self.note = 'Reverting to old ZN-T value'
        
    def ahu_cooling_in_control(self):
        if 'CLG1-C' in self.controller:
            self.wait_for_state_not(self.controller['CLG1-C'].value, 'inactive')
        if 'CLG2-C' in self.controller:
            self.wait_for_state_not(self.controller['CLG2-C'].value, 'inactive')
        if 'CLG3-C' in self.controller:
            self.wait_for_state_not(self.controller['CLG3-C'].value, 'inactive')
        if 'CLG4-C' in self.controller:
            self.wait_for_state_not(self.controller['CLG4-C'].value, 'inactive')

        self.note = 'All AHU Cooling stages working'
    def ahu_cooling_dehumidif(self):
        self.wait_for_state(self.controller['CLG-OUTSTATE'], 'H Control', callback=self.ahu_cooling_is_off)


class Relief_Fan(object):
    def rlf_fan_should_stop(self):
        self.wait_for_state(self.controller['RLF-OUTSTATE'], 'Off', callback=self.rlf_fan_is_off)

    def rlf_fan_is_off(self):
        self.wait_for_state(self.controller['RLF-C'], 'inactive')
        self.wait_for_state(self.controller['RLF-O'], 0)
        
    def rlf_fan_should_modulate(self):
        self.wait_for_state(self.controller['RLF-O'], 'BS-P Control', callback=self.rlf_fan_is_modulating)
    
    def rlf_fan_is_modulating(self):
        self.wait_for_state(self.controller['RLF-C'], 'active')
        self.wait_for_value_gt(self.controller['RLF-O'], 0)