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


class Fan(OnOffDevice):
    """
    A Fan is an OnOffDevice to which we add a TRANSIENT system
    This system will model the way flow and pressure are impacted 
    by the start, stop and possible modulation of the pump.

    Note : inputs may also be BAC0.core.devices.Point

    :start_command: (boolean) will start and stop the pump
    :modulation: (float) default to 100, if modified, will have an impact on TRANSIENT
    :succion_pressure: (float) typical pressure of loop, should drop when pump is running by simulation can't do that right now
    :delta_p : (float) increase in pressure when pump is running at max flow
    :max_flox: (flow) flow when pump is running at 100% modulation, when TRANSIENT effect is over
    """

    def __init__(
        self,
        start_command=False,
        modulation=100,
        succion_pressure=0,
        delta_p=150,
        max_flow=2000,
        amperage=1,
        name=None,
        description=None,
    ):
        super().__init__(
            start_command=start_command, name=name, description=description
        )
        self.max_flow = max_flow
        self.succion_pressure = succion_pressure
        self.delta_p = delta_p
        self.modulation = modulation
        self.max_amperage = amperage

        self._equipment = TRANSIENT(
            ValueCommandElement(0, 0),
            delta_max=100,
            max_output=100,
            tau=2,
            decrease=False,
            random_error=0.1,
            name="{}".format(self.name),
        )

        self.systems = [self._equipment]

    def update_equipment(self):
        # print('Status : {}'.format(self._status))
        if self._status:
            # print('Running, updating modulation to {}'.format(self.modulation))
            self._equipment.input["command"] = Equipment.get_value(self.modulation)
        self._equipment.output

    def flow(self):
        self.refresh()
        return (self._equipment.last_value / 100) * self.max_flow

    def pressure(self):
        self.refresh()
        return self.succion_pressure + (
            (self._equipment.last_value / 100) * self.delta_p
        )

    def amperage(self):
        self.refresh()
        return (self._equipment.last_value / 100) * self.max_amperage

    def _on_start(self):
        self._equipment.input["command"] = Equipment.get_value(self.modulation)

    def _on_stop(self):
        self._equipment.input["command"] = 0


class ParallelPumps(EquipmentGroup):
    def __init__(self, members=None, name=None, description=None):
        super().__init__(name=name, description=description, members=members)

    def flow(self):
        self.refresh()
        _flow = 0
        for each in self.members:
            _flow += each.flow()
        return _flow

    def pressure(self):
        self.refresh()
        _pressure = 0
        for each in self.members:
            _pressure += each.pressure()
        return _pressure
