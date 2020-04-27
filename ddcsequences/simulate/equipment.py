#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from random import random
import time
import BAC0

from .system import (
    System,
    ADD,
    SUB,
    HEAT,
    ValueCommandElement,
    MixInputElement,
    MIX,
    LINEAR,
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
