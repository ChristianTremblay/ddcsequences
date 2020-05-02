#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from random import random
import time
import BAC0
from BAC0.core.devices.Points import Point

from .system import (
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


# def create(equipment):
#    system_input_format = equipment, model.INPUT_ELEMENT_FORMAT
#    items = system_input_format.items
#    system_input = system_input_format()
#    equip_input_values = list(equipment.input.values())
#    for i, each in enumerate(items):
#        system_input.each = equip_input_values[i]
#    equip = equipment.model(system_input,equipment.output)

# SCR
# input value must be the temperature before the SCR
# SCR = {
#    "input": {"value": None, "command": None},
#    "output": None,
#    "name": None,
#    "kw": 1,
#    "ls": 50,
#    "model": HEAT,
# }

SCR = HEAT(ValueCommandElement(), kw=1, ls=50)
CoolingValve = TRANSIENT(
    ValueCommandElement(), delta_max=10, min_output=5, tau=20, decrease=True
)
HeatingValve = TRANSIENT(
    ValueCommandElement(), delta_max=10, max_output=50, tau=20, decrease=False
)


class EquipmentGroup:
    """
    Group of equipements serving one goal.
    For example, pumps in parallel will result in one output being
    controlled by two devices.
    """

    ids = 0

    def __init__(self, name=None):
        if name:
            self.name = name
        else:
            self.name = "EquipmentGroup_{}".format(Equipment.ids)
        Equipment.ids += 1

    @property
    def output(self):
        # print("output")
        try:
            for each in self.equipments:
                # print("Executing {}".format(each.name))
                each.output
        except AttributeError:
            pass

        return [self.name, self.equipments]

    def execution(self):
        # To be used with BAC0 .match_value and get a Callable
        return self.output

    def __repr__(self):
        return "{}".format(self.name)

    def __getitem__(self, name):
        self.output
        for equipment in self.equipments:
            if equipment.name == name:
                return equipment
        raise AttributeError("Equipment not found")


class Equipment:
    ids = 0

    @staticmethod
    def get_value(value):
        if isinstance(value, Point):
            # print('BAC0 Point')
            _value = value.lastValue
            if _value == "active":
                # print('Active')
                return True
            elif _value == "inactive":
                # print('Inactive')
                return False
            # else:
            #    raise ValueError("Unknown value in context : {}".format(_value))
            else:
                # print('Value : {}'.format(_value))
                return _value

        else:
            return value

    def __init__(self, start_command=False, name=None):
        self.start_command = start_command
        self._status = False
        if name:
            self.name = name
        else:
            self.name = "Equipment_{}".format(Equipment.ids)
        Equipment.ids += 1

    @property
    def output(self):
        _start = Equipment.get_value(self.start_command)
        if _start == True and not self._status:
            # print('Starting {}'.format(self.name))
            self.start()
        if _start == False and self._status:
            # print('Stoping {}'.format(self.name))
            self.stop()
        self._on_output()
        try:
            for system in self.systems:
                # print("Executing {}".format(system.name))
                system.output
        except AttributeError:
            # print('Attribute Error')
            pass

        # return self._status

    @property
    def status(self):
        self.output
        return self._status
        # return self._status

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def execution(self):
        # To be used with BAC0 .match_value and get a Callable
        return self.output

    # def __getitem__(self,name):

    def __repr__(self):
        return getattr(self, "_equipment").__repr__()

    def __getitem__(self, name):
        for system in self.systems:
            try:
                return system[name]
            except:
                pass
        return self.__dict__[name]


class OnOffDevice(Equipment):
    def __init__(self, start_command=None, name=None):
        super().__init__(start_command=start_command, name=name)

    def start(self):
        # print("Start")
        self._status = True

    def stop(self):
        # print("Stop")
        self._status = False


class Pump(OnOffDevice):
    def __init__(
        self,
        start_command=False,
        modulation=100,
        succion_pressure=10,
        delta_p=5,
        max_flow=400,
        name=None,
    ):
        super().__init__(start_command=start_command, name=name)
        self.max_flow = max_flow
        self.succion_pressure = succion_pressure
        self.delta_p = delta_p
        self.modulation = modulation

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

    def _on_output(self):
        if not self._status:
            # print('Not running... modulation = 0')
            self._equipment.input["command"] = 0
        else:
            # print('Running... modulation = {}'.format(self.modulation))
            self._equipment.input["command"] = self.modulation

    @property
    def flow(self):
        self.output
        return (self._equipment.last_value / 100) * self.max_flow

    @property
    def pressure(self):
        self.output
        return self.succion_pressure + (
            (self._equipment.last_value / 100) * self.delta_p
        )


class ParallelPumps(EquipmentGroup):
    def __init__(
        self,
        pump1_start_command=False,
        pump1_modulation=100,
        pump2_start_command=False,
        pump2_modulation=100,
        succion_pressure=0,
        delta_p=5,
        max_flow=400,
        name=None,
        pump1_name="Pump_A",
        pump2_name="Pump_B",
    ):
        super().__init__(name=name)
        self.pump1_start_command = pump1_start_command
        self.pump2_start_command = pump2_start_command
        self.pump1_modulation = pump1_modulation
        self.pump2_modulation = pump2_modulation
        self.succion_pressure = succion_pressure
        self.delta_p = delta_p
        self.max_flow = max_flow

        self._p1 = Pump(
            start_command=Equipment.get_value(self.pump1_start_command),
            modulation=Equipment.get_value(self.pump1_modulation),
            succion_pressure=self.succion_pressure,
            delta_p=self.delta_p,
            max_flow=self.max_flow,
            name=pump1_name,
        )

        self._p2 = Pump(
            start_command=Equipment.get_value(self.pump2_start_command),
            modulation=Equipment.get_value(self.pump2_modulation),
            succion_pressure=self.succion_pressure,
            delta_p=self.delta_p,
            max_flow=self.max_flow,
            name=pump2_name,
        )

        self.equipments = [self._p1, self._p2]

    def _on_output(self):
        self._p1.start_command = Equipment.get_value(self.pump1_start_command)
        self._p1.modulation = Equipment.get_value(self.pump1_modulation)
        self._p2.start_command = Equipment.get_value(self.pump2_start_command)
        self._p2.modulation = Equipment.get_value(self.pump2_modulation)

    @property
    def flow(self):
        _ = self.output
        return self._p1.flow + self._p2.flow

    @property
    def pressure(self):
        _ = self.output
        return self._p1.pressure + self._p2.pressure


class Fan(Equipment):
    def __init__(self, start_command, name):
        super().__init__(start_command=start_command, name=name)


class Heater(Equipment):
    def __init__(self, kw=10, ls=50):
        self._equipment = HEAT(ValueCommandElement(), kw=1, ls=50)
        self.systems = [self._equipment]

    def set_flow(self, value):
        self._equipment.ls = value


class Chiller(Equipment):
    """
    BAsic approximation of a chiller
    """

    def __init__(self, neutral_temp=20, setpoint=6, start_command=None):
        super().__init__(start_command=start_command)

        self.neutral_temperature = neutral_temp
        self.setpoint = setpoint
        # self.enable = enable
        self.running = False
        delta_chill = self.neutral_temperature - self.setpoint
        # 100 because we will see temp reach setpoint, we are not testing load
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
        self._chwlt.input["value"] = self.neutral_temperature
        self._cwlt.input["value"] = self.neutral_temperature
        self._chwlt.input["command"] = 0
        self._cwlt.input["command"] = 0
        # init output
        self._chwlt.output
        self._cwlt.output
        self.systems = [self._cwlt, self._chwlt]

    def start(self):
        # print("Start")
        self.set_command(100)
        self.running = True

    def stop(self):
        # print("Stop")
        self.set_command(0)
        self.running = False

    @property
    def chwlt(self):
        return self._chwlt.last_value

    @property
    def cwlt(self):
        return self._cwlt.last_value

    def set_command(self, value):
        self._chwlt.input["command"] = value
        self._cwlt.input["command"] = value

    def __repr__(self):
        return "Chiller"


class Room(Equipment):
    def __init__(self):
        pass
        # idea...
        # would be a MIX
