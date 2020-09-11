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


class Chiller(OnOffDevice):
    """
    Basic approximation of a chiller
    """

    def __init__(
        self,
        name=None,
        description=None,
        neutral_temp=20,
        setpoint=6,
        start_command=False,
        modulation=100,
    ):
        super().__init__(
            start_command=start_command, name=name, description=description
        )

        self.neutral_temperature = neutral_temp
        self.setpoint = setpoint
        self.modulation = modulation
        delta_chill = Equipment.get_value(
            self.neutral_temperature
        ) - Equipment.get_value(self.setpoint)
        self._chwlt = TRANSIENT(
            ValueCommandElement(),
            delta_max=delta_chill,
            min_output=5,
            tau=60,
            decrease=True,
            random_error=0.1,
            name="Chilled Water Leaving Temp",
        )
        self._cwlt = TRANSIENT(
            ValueCommandElement(),
            delta_max=20,
            max_output=40,
            tau=30,
            decrease=False,
            random_error=0.1,
            name="Condensed Water Leaving Temp",
        )
        self._chwlt.input["command"] = Equipment.get_value(self.modulation)
        self._cwlt.input["command"] = Equipment.get_value(self.modulation)
        self._chwlt.input["value"] = Equipment.get_value(self.neutral_temperature)
        self._cwlt.input["value"] = Equipment.get_value(self.neutral_temperature)
        self.systems = [self._cwlt, self._chwlt]

    def update_equipment(self):
        if self._status:
            self._chwlt.input["value"] = Equipment.get_value(self.neutral_temperature)
            self._cwlt.input["value"] = Equipment.get_value(self.neutral_temperature)
            self._chwlt.delta_max = Equipment.get_value(
                self.neutral_temperature
            ) - Equipment.get_value(self.setpoint)
            self._chwlt.input["command"] = Equipment.get_value(self.modulation)
            self._cwlt.input["command"] = Equipment.get_value(self.modulation)

    def _on_stop(self):
        self._chwlt.input["value"] = Equipment.get_value(self.neutral_temperature)
        self._cwlt.input["value"] = Equipment.get_value(self.neutral_temperature)
        self._chwlt.input["command"] = 0
        self._cwlt.input["command"] = 0

    def chwlt(self):
        self.refresh()
        return self._chwlt.last_value

    def cwlt(self):
        self.refresh()
        return self._cwlt.last_value

    def get_normalized(self):
        return self._chwlt.last_value / (
            self._chwlt.input["value"] - self._chwlt.last_value
        )

    def chwet(self):
        self.refresh()
        return self._chwlt.last_value - (self._chwlt.delta_max * self.get_normalized())

    def cwet(self):
        self.refresh()
        return self._cwlt.last_value - (self._cwlt.delta_max * self.get_normalized())

    def __repr__(self):
        return "Chiller"
