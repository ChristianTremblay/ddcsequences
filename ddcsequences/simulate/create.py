#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from .equipment import ParallelPumps, Pump, Chiller, Fan

from BAC0.core.devices import Device
import pprint


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


def parallel_pumps(controller=None, config=None):
    if not config:
        return help("parallel_pumps")
    controller = controller
    # if not isinstance(controller, Device):
    #    raise ValueError("Provide a BAC0 controller.")

    p1_p2 = ParallelPumps(
        pump1_start_command=controller[config["p1_start"]],
        pump2_start_command=controller[config["p2_start"]],
        pump1_modulation=controller[config["p1_modulation"]],
        pump2_modulation=controller[config["p2_modulation"]],
        succion_pressure=controller[config["succion_pressure"]],
        delta_p=config["delta_p"],
        max_flow=config["max_flow"],
        pump1_name=config["pump1_name"],
        pump2_name=config["pump2_name"],
    )
    print(
        "Defining match values for both pumps status on {} and {}.".format(
            config["p1_status"], config["p2_status"]
        )
    )
    controller[config["p1_status"]].match_value(p1_p2[config["pump1_name"]].status)
    controller[config["p2_status"]].match_value(p1_p2[config["pump2_name"]].status)
    if config["set_succion_pressure"]:
        print(
            "Setting basic succion pressure {} to {}.".format(
                config["succion_pressure"], config["set_succion_pressure"]
            )
        )
        controller[config["succion_pressure"]] = float(config["set_succion_pressure"])
    if config["discharge_pressure"]:
        print(
            "Defining match values for discharge pressure on {}.".format(
                config["discharge_pressure"]
            )
        )
        controller[config["discharge_pressure"]].match_value(p1_p2.pressure)
    if config["flow_sensor"]:
        print(
            "Defining match values for flow sensor on {}.".format(config["flow_sensor"])
        )
        controller[config["flow_sensor"]].match_value(p1_p2.flow)
    return p1_p2
