#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
from ...simulate.equipment import Equipment, EquipmentGroup, OnOffDevice
from ...simulate.system import (
    System,
    ADD,
    SUB,
    HEAT,
    ValueElement,
    ValueCommandElement,
    MixInputElement,
    MIX,
    LINEAR,
    TRANSIENT,
    PASSTHRU,
    SELECT,
)


class Tank(Equipment):
    @staticmethod
    def getprop(self, name, i):
        """
        This method is used to dynamically create properties based on number of switches.
        As the function returned is dynamic and will change based on equipment, 
        this must be done at the equipment level, not the base class level.

        Works with _add_property(), see below.
        """
        def xget(self):
            self.refresh()
            try:
                return lambda: self.proximity()[i]
            except IndexError:
                return False

        return xget

    def __init__(self, number_of_switches=5, level=0, name=None, description=None):
        super().__init__(name=name, description=description)

        self.number_of_switches = number_of_switches
        self.level = level
        self.output_list = [False] * number_of_switches

    def proximity(self):
        _number_of_switches = self.number_of_switches
        _level_per_switch = 100 / _number_of_switches
        a = range(0, 101, int(_level_per_switch))
        base = [True] * _number_of_switches
        find = Equipment.get_value(self.level)
        idx = min(range(len(a)), key=lambda i: abs(a[i] - find))
        mask = [
            True if i < idx else False
            for i, x in enumerate(range(0, _number_of_switches))
        ]
        return base and mask

    def _add_property(self, name, arg):
        """
        Called by generate for parameters declared with a add_property key in the yaml file.
        """
        self.__setattr__("_" + name, None)
        setattr(self.__class__, name, property(Tank.getprop(self, name, arg)))
