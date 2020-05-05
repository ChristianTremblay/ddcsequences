#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from .equipment import EquipmentGroup, Pump, Chiller, Fan

from BAC0.core.devices import Device
import pprint

_classes = {"Pump": Pump, "ParallelPumps": ParallelPumps}


def create_pump():
    pass


config = {
    "parallel_pumps": {
        "name_of_pair": None,
        "controller": None,
        "pump1_name": "Pump_A",
        "pump2_name": "Pump_B",
        "p1_start": None,
        "p1_modulation": None,
        "p1_status": None,
        "p2_start": None,
        "p2_modulation": None,
        "p2_status": None,
        "succion_pressure": None,
        "set_succion_pressure": None,
        "discharge_pressure": None,
        "flow_sensor": None,
        "delta_p": None,  # in psi
        "max_flow": None,
    }
}


def help(name):
    pp = pprint.PrettyPrinter(indent=4)
    print("Create a dict with all parameters and send it to create method")
    pp.pprint(config[name])
    print("You can use this syntax to get the template : ")
    print("new_config = create.config['{}']".format(name))


def create(controller, config=None):
    controller = controller
    config = config[key]
    name = config["name"]
    _equip = _classes[config["class"]](name=name)
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
    except AttributeError:
        pass
    try:
        for k, v in config["inputs"].items():
            if v:
                var = controller[v]
                setattr(_equip, k, var)
    except AttributeError:
        pass
    try:
        for k, v in config["outputs"].items():
            if v:
                controller[v].match_value(getattr(_equip, k))
    except AttributeError:
        pass
    return _equip
