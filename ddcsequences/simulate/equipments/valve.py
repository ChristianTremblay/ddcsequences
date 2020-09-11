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


class Valve(Equipment):
    _modes = ["heating", "cooling"]

    def __init__(
        self,
        name=None,
        description=None,
        modulation=100,
        entering_temp=0,
        max_flow=400,
        mode="heating",
        delta_T=10,
        min_temperature=float("-inf"),
        max_temperature=float("inf"),
        tau=10,
    ):
        super().__init__(name=name, description=description)
        self.modulation = modulation
        self.entering_temp = entering_temp
        self.max_flow = max_flow
        self.mode = mode

        # Eventually, calculate delta_T vs flow
        self.delta_T = delta_T

        self.min_temperature = min_temperature
        self.max_temperature = max_temperature

        self.tau = tau
        _decrease = False
        if mode.lower() in Valve._modes:
            self.mode = mode.lower()
            _decrease = True if self.mode == "cooling" else False
        else:
            raise ValueError("Provide valve mode as 'heating' or 'cooling'")
        self._temperature = TRANSIENT(
            ValueCommandElement(0, 0),
            delta_max=self.delta_T,
            min_output=self.min_temperature,
            tau=self.tau,
            decrease=_decrease,
        )
        self._leaving_flow = TRANSIENT(
            ValueCommandElement(0, 0),
            delta_max=self.max_flow,
            min_output=0,
            max_output=self.max_flow,
            tau=self.tau / 2,
            decrease=_decrease,
        )
        self.systems = [self._temperature, self._leaving_flow]

        self._temperature.input["command"] = Equipment.get_value(self.modulation)
        self._leaving_flow.input["command"] = Equipment.get_value(self.modulation)
        self._temperature.input["value"] = Equipment.get_value(self.entering_temp)
        self._leaving_flow.input["value"] = 0

    def update_equipment(self):
        self._leaving_flow.input["command"] = Equipment.get_value(self.modulation)
        if Equipment.get_value(self.modulation) > 0:
            self._temperature.input["command"] = Equipment.get_value(self.modulation)
            self._temperature.input["value"] = Equipment.get_value(self.entering_temp)
        else:
            self._temperature.input["command"] = 0
            self._temperature.input["value"] = Equipment.get_value(self.entering_temp)

    def leaving_temp(self):
        self.refresh()
        return self._temperature.output

    def leaving_flow(self):
        self.refresh()
        return self._leaving_flow.output
