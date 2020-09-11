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


class MixedAirDampers(Equipment):
    def __init__(
        self,
        name=None,
        description=None,
        damper_command=0,
        outdoor_air_temp=0,
        return_air_temp=21,
        outdoor_air_co2=400,
        return_air_co2=500,
        tau=10,
    ):
        super().__init__(name=name, description=description)
        self.damper_command = damper_command
        self.outdoor_air_temp = outdoor_air_temp
        self.return_air_temp = return_air_temp
        self.outdoor_air_co2 = outdoor_air_co2
        self.return_air_co2 = return_air_co2

        self._outdoor_air_temp = MixInputElement(
            Equipment.get_value(self.outdoor_air_temp),
            Equipment.get_value(self.damper_command),
        )
        self._return_air_temp = MixInputElement(
            Equipment.get_value(self.return_air_temp),
            Equipment.get_value(self.return_air_modulation),
        )

        self._outdoor_air_co2 = MixInputElement(
            Equipment.get_value(self.outdoor_air_co2),
            Equipment.get_value(self.damper_command),
        )
        self._return_air_co2 = MixInputElement(
            Equipment.get_value(self.return_air_co2),
            Equipment.get_value(self.return_air_modulation),
        )

        self.tau = tau

        self._temperature = TRANSIENT(
            MIX([self._outdoor_air_temp, self._return_air_temp]), tau=self.tau
        )
        self._co2 = TRANSIENT(
            MIX([self._outdoor_air_co2, self._return_air_co2]), tau=self.tau
        )
        self.systems = [self._temperature, self._co2]

    @property
    def return_air_modulation(self):
        return 100 - Equipment.get_value(self.damper_command)

    def update_equipment(self):
        self._temperature.input._input["element1"]["value"] = Equipment.get_value(
            self.outdoor_air_temp
        )
        self._temperature.input._input["element1"]["quantity"] = Equipment.get_value(
            self.damper_command
        )
        self._temperature.input._input["element2"]["value"] = Equipment.get_value(
            self.return_air_temp
        )
        self._temperature.input._input["element2"]["quantity"] = Equipment.get_value(
            self.return_air_modulation
        )
        self._co2.input._input["element1"]["value"] = Equipment.get_value(
            self.outdoor_air_co2
        )
        self._co2.input._input["element1"]["quantity"] = Equipment.get_value(
            self.damper_command
        )
        self._co2.input._input["element2"]["value"] = Equipment.get_value(
            self.return_air_co2
        )
        self._co2.input._input["element2"]["quantity"] = Equipment.get_value(
            self.return_air_modulation
        )

    def mixed_air_temp(self):
        self.refresh()
        return self._temperature.output

    def mixed_air_co2(self):
        self.refresh()
        return self._co2.output
