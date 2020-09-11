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


class DX_Cooling_Stage(Equipment):
    def __init__(
        self,
        name=None,
        description=None,
        modulation=100,
        entering_temp=0,
        delta_T=7,
        min_temperature=0,
        max_temperature=float("inf"),
        tau=10,
    ):
        super().__init__(name=name, description=description)
        self.modulation = modulation
        self.entering_temp = entering_temp

        # Eventually, calculate delta_T vs flow
        self.delta_T = delta_T

        self.min_temperature = min_temperature
        self.max_temperature = max_temperature

        self.tau = tau
        self._temperature = TRANSIENT(
            ValueCommandElement(0, 0),
            delta_max=self.delta_T,
            min_output=self.min_temperature,
            tau=self.tau,
            decrease=True,
        )
        self.systems = [self._temperature]

        self._temperature.input["command"] = Equipment.get_value(
            self.modulation, convert_boolean=True
        )
        self._temperature.input["value"] = Equipment.get_value(self.entering_temp)

    def update_equipment(self):
        if Equipment.get_value(self.modulation, convert_boolean=True) > 0:
            self._temperature.input["command"] = Equipment.get_value(
                self.modulation, convert_boolean=True
            )
            self._temperature.input["value"] = Equipment.get_value(self.entering_temp)
        else:
            self._temperature.input["command"] = 0
            self._temperature.input["value"] = Equipment.get_value(self.entering_temp)

    def leaving_temp(self):
        self.refresh()
        return self._temperature.output
