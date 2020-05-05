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
from yaml import load, dump, FullLoader

from functools import wraps

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


SCR = HEAT(ValueCommandElement(), kw=1, ls=50)
CoolingValve = TRANSIENT(
    ValueCommandElement(), delta_max=10, min_output=5, tau=20, decrease=True
)
HeatingValve = TRANSIENT(
    ValueCommandElement(), delta_max=10, max_output=50, tau=20, decrease=False
)


def tmp_wrap(func):
    @wraps(func)
    def tmp(*args, **kwargs):
        print(func.__name__)
        arg = int(func.__name__)
        return func(*args, **kwargs)

    return tmp


class EquipmentGroup:
    """
    Group of equipements serving one goal.
    For example, pumps in parallel will result in one output being
    controlled by two devices.
    """

    ids = 0
    defined = {}

    def __init__(self, name=None, members=None, description=None):
        if name:
            self.name = name
            self.id = name
        else:
            self.id = "EquipmentGroup_{}".format(EquipmentGroup.ids)
            self.name = self.id
        EquipmentGroup.ids += 1
        self.members = members
        self.description = description
        EquipmentGroup.defined[self.id] = self

    def refresh(self):
        # print("output")
        try:
            for equipment in self.equipments:
                # print("Executing {}".format(each.name))
                equipment.refresh()
        except AttributeError:
            pass

        # return [self.name, self.equipments]

    def __repr__(self):
        return "{}".format(self.name)

    def __getitem__(self, name):
        # self.refresh() # risk of double refresh
        for equipment in self.equipments:
            if equipment.name == name:
                return equipment
        raise AttributeError("Equipment not found")


class Equipment:
    """
    Base class for an equipment which is in fact 
    composed of one or more systems. Equipments models
    real life devices like pumps, fans or chillers.
    """

    ids = 0
    defined = {}

    @staticmethod
    def get_value(value):
        if isinstance(value, Point):
            _value = value.lastValue
            if _value == "active":
                return True
            elif _value == "inactive":
                return False
            else:
                return _value
        else:
            return value

    def __init__(self, name=None, description=None):
        if name:
            self.name = name
            self.id = name
        else:
            self.id = "Equipment_{}".format(Equipment.ids)
            self.name = self.id
        self.description = description
        Equipment.ids += 1
        Equipment.defined[self.id] = self

    def _call(self, method):
        try:
            # print('Trying {}'.format(method))
            method()
        except (NotImplementedError, AttributeError) as error:
            # print('Failed : {}'.format(error))
            pass

    def refresh(self):
        self._call(self._on_refresh)
        try:
            for system in self.systems:
                system.output
        except AttributeError:
            pass

    def _on_refresh(self):
        self._call(self.update_equipment)

    def __repr__(self):
        return "{} | {}\n{}".format(self.name, self.__class__, self.__dict__)

    def __getitem__(self, name):
        for system in self.systems:
            try:
                return system[name]
            except:
                pass
        return self.__dict__[name]

    def __setattr__(self, name, value):
        self.__dict__[name] = value
        try:
            for system in self.systems:
                system.output
                # print("Updating {}".format(system.name))
        except AttributeError:
            pass
        self._call(self._on_refresh)
        self._call(self._on_setattr)

    def _on_setattr(self):
        """
        Callback that can be use to execute tasks when an input is changed.
        """
        raise NotImplementedError

    def update_equipment(self):
        """
        Supplemental callback to be use in case updates
        are needed when, for example, an input is changed.
        """
        raise NotImplementedError


class OnOffDevice(Equipment):
    """
    An equipment that we can start and stop.
    A status is available to know the state of this equipment.
    To start or stop, call the functions direclty of write to 
    start_command

    :start_command: (boolean) 
    :status: (boolean)
    """

    def __init__(self, start_command=None, name=None, description=None):
        super().__init__(name=name, description=description)
        self.start_command = start_command
        self._status = False

    def start(self):
        if not self.start_command:
            self.start_command = True
        self._call(self._on_start)
        self._status = True

    def stop(self):
        if self.start_command:
            self.start_command = False
        self._call(self._on_stop)
        self._status = False

    def _on_start(self):
        raise NotImplementedError

    def _on_stop(self):
        raise NotImplementedError

    def status(self):
        self.refresh()
        return self._status

    def _on_refresh(self):
        _start = Equipment.get_value(self.start_command)
        if _start == True and not self._status:
            self.start()
        if _start == False and self._status:
            self.stop()
        self._call(self.update_equipment)


class Pump(OnOffDevice):
    """
    A pump is an OnOffDevice to which we add a TRANSIENT system
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
        succion_pressure=10,
        delta_p=5,
        max_flow=400,
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


class Fan(Equipment):
    def __init__(self, start_command, name):
        super().__init__(start_command=start_command, name=name)


class Heater(Equipment):
    def __init__(self, kw=10, ls=50):
        self._equipment = HEAT(ValueCommandElement(), kw=1, ls=50)
        self.systems = [self._equipment]

    def set_flow(self, value):
        self._equipment.ls = value


class Chiller(OnOffDevice):
    """
    BAsic approximation of a chiller
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

    #    def set_command(self, value):
    #        self._chwlt.input["command"] = value
    #        self._cwlt.input["command"] = value

    def __repr__(self):
        return "Chiller"


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


class TankWithProximityLevels(Equipment):
    @staticmethod
    def getprop(self, name, i):
        def xget(self):
            # print("Get {}".format(name))
            # print(self.output_list[i])
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
        # def update_equipment(self):
        _number_of_switches = self.number_of_switches
        _level_per_switch = 100 / _number_of_switches
        a = range(0, 101, int(_level_per_switch))
        base = [True] * _number_of_switches
        find = Equipment.get_value(self.level)
        idx = min(range(len(a)), key=lambda i: abs(a[i] - find))
        # print(a[idx], idx)
        mask = [
            True if i < idx else False
            for i, x in enumerate(range(0, _number_of_switches))
        ]
        return base and mask

    def _add_method(self, name, arg):
        self.__setattr__("_" + name, None)
        setattr(
            self.__class__,
            name,
            property(TankWithProximityLevels.getprop(self, name, arg)),
        )


class Room(Equipment):
    def __init__(self):
        pass
        # idea...
        # would be a MIX


# ///////////////////////////////////////////////////////////////


def open_config_file(filename):
    """
    Turns the yaml file into a dict
    Some validation could occur here
    """
    with open(filename, "r") as file:
        equipment_params = load(file, Loader=FullLoader)
    return equipment_params


def create_equip(controller, config=None, name=None):
    """
    This function helps in the creation of equipments.
    It relies on a config dict to generate equipments
    and make all the links with the BAC0 device.
    """
    _classes = {
        "Pump": Pump,
        "ParallelPumps": ParallelPumps,
        "Chiller": Chiller,
        "Valve": Valve,
        "TankWithProximityLevels": TankWithProximityLevels,
    }
    controller = controller
    # config = config[key]
    # name = config["name"]
    try:
        _equip = _classes[config["class"]](name=name)
    except KeyError:
        raise ConfigFileError(
            "Can't create an equipment of type {}.".format(config["class"])
        )
    try:
        for k, v in config["statics"].items():
            if k == "members":
                _members = []
                for each in v:
                    _members.append(Equipment.defined[each])
                setattr(_equip, "members", _members)
                continue
            if v:
                setattr(_equip, k, v)
    except (AttributeError, KeyError):
        pass
    try:
        for k, v in config["inputs"].items():
            if v:
                var = controller[v]
                setattr(_equip, k, var)
    except (AttributeError, KeyError):
        pass
    try:
        for name_of_method, params in config["add_methods"].items():
            if params:
                _args = []
                for base_method, value in params.items():
                    _mthd = getattr(_equip, base_method)

                    target, arg = value
                    # setattr(_equip,name_of_method,lambda x: _equip.output_list[arg])
                    # new_method = lambda: _mthd(int(arg))
                    _equip._add_method(name_of_method, arg)
                    # print("New method : {} | {}".format(name_of_method, arg))
                    controller[target].match_value(getattr(_equip, name_of_method))
    except (AttributeError, KeyError):
        pass
    try:
        for k, v in config["outputs"].items():
            if v:
                controller[v].match_value(getattr(_equip, k))
    except (AttributeError, KeyError):
        pass

    return _equip


def generate(controller, filename):
    params = open_config_file(filename)
    # new_equip = []
    for k, v in params.items():
        print("Creating {} | {}".format(k, v["description"]))
        try:
            _ = create_equip(controller=controller, config=v, name=k)
        except ConfigFileError as error:
            print("{}".format(error))
            continue


class ConfigFileError(Exception):
    pass
