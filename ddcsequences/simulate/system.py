#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from collections import namedtuple
import time
from datetime import datetime as dt
from random import uniform

from ddcmath.heating import heating_deltaT_c
from ddcmath.airflow import cfm2ls, ls2cfm

from BAC0.core.devices.Points import Point

_ELEMENTS = namedtuple("INPUT_ELEMENTS", ["min", "max"])


class InputElement(object):
    """
    Enforcing the format of system inputs
    Inputs can be number but can also be BAC0 points. In that case,
    we are interested in the lastValue to "not read on the network" as
    it will slow down everythin.
    """

    items = []

    @staticmethod
    def get_value(item):
        """
        This will cover the case of a BAC0.point
        """
        if isinstance(item, Point):
            return item.lastValue
        else:
            return item

    # def __setattr__(self, name, value):
    #    if name in self.items:
    #        self.__dict__[name] = value
    #    else:
    #        raise AttributeError("{} doesn't exist".format(name))

    def __getitem__(self, name):
        if name in self.items:
            return getattr(self, name)

    def __setitem__(self, name, value):
        if name in self.items:
            try:
                setattr(self, name, value)
            except AttributeError:
                # _prefix
                setattr(self, "_" + name, value)


class ValueCommandElement(InputElement):
    """
    A typical input containing a value and a command.
    Both could change at any time
    Can be used to model a SCR (inlet temprature + SCR Command),
    a VFD (discharge air pressure, VFD Command), etc.

    Iteration is possible to allow :

        value, command = element

    PS : If working with percent, use a number between 0-100 as it
    will be clearer than a number between 0 and 1

    """

    items = ["value", "command"]

    def __init__(self, value=None, command=None):
        self._value = value
        self._command = command

    @property
    def value(self):
        return InputElement.get_value(self._value)

    @property
    def command(self):
        return InputElement.get_value(self._command)

    def __iter__(self):
        for each in [self.value, self.command]:
            yield each
        # return [self.value, self.command]

    def __repr__(self):
        return "Value : {} | Command : {}".format(self.value, self.command)


class MixInputElement(InputElement):
    """
    Mix input element should be constructed by 2 elements to mix
    Each element must contain a value and a quantity.

    ex. Mixing water
    temperature = value
    volume = quantity

    ex. Mixin air (return mixed with outside air)
    temperature = value
    quantity = airflow proportion (via damper position for example)

    """

    items = ["value", "quantity"]

    def __init__(self, value=None, quantity=None):
        self._value = value
        self._quantity = quantity

    @property
    def value(self):
        return InputElement.get_value(self._value)

    @property
    def quantity(self):
        return InputElement.get_value(self._quantity)

    def __iter__(self):
        for each in [self.value, self.quantity]:
            yield each

    def __repr__(self):
        return "Value : {} | Quantity : {}".format(self.value, self.quantity)


class FlexibleInput(object):
    """
    Input of a system can be multiple things. I need something
    to covers different cases. 

    This class allows the system input to be a simple number,
    a list, another system or a function
    """

    def __init__(self, flex_input):
        self._input = flex_input

    @property
    def value(self):
        if callable(self._input):
            return self._input()
        elif isinstance(self._input, System):
            return self._input.output
        # elif isinstance(self._input, ValueCommandElement):
        #    return [element for element in self._input]
        # elif isinstance(self._input, MixInputElement):
        #    return [element for element in self._input]
        else:
            return self._input

    def __repr__(self):
        return "{} | Type : {}".format(self.value, type(self._input))

    def __iter__(self):
        if isinstance(self._input, ValueCommandElement) or isinstance(
            self._input, MixInputElement
        ):
            for each in self._input:
                yield each
        else:
            raise ValueError("Not iterable")


class System(object):
    """
    A system is a black box. You give it an input, it will throw out an output.
    This class must be subclassed by more specific systems containint a method
    called "process". This will define the behaviour of the system.

    Input of a system can be another system. This will allow cascading systems
    to create something more complex.

    Timing is provided so eventually, we'll cover transient reaction of systems.

    """

    ids = 0

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        randomness=False,
        random_error=0.5,
    ):
        self.input = self.define_input(system_input)
        self.output_reference = system_output
        self.t_0 = None
        self.last_execution = None
        self.last_value = None
        self.dt = 0
        if not name:
            name = "System_{}".format(System.ids)
        self.name = name
        System.ids += 1
        self.randomness = randomness
        self.random_error = random_error

    def _pre_process(self):
        if not self.t_0:
            self.t_0 = dt.now()
        if self.last_execution:
            self.dt = self.last_execution - self.t_0
        out = self.process()
        self.last_execution = dt.now()
        if self.randomness:
            out += uniform(-self.random_error, random_error)
        self.last_value = out
        return out

    @property
    def output(self):
        return self._pre_process()
        # return self.process()

    def process(self):
        raise NotImplementedError("Must define a funtion")

    def define_input(self, system_input):
        if isinstance(system_input, list):
            assert (
                len(system_input) >= self.INPUT_ELEMENTS.min
                and len(system_input) <= self.INPUT_ELEMENTS.max
            )

            _n = []
            for each in system_input:
                if self.INPUT_ELEMENT_FORMAT:
                    assert isinstance(each, self.INPUT_ELEMENT_FORMAT)
                _n.append(FlexibleInput(each))
            new_input = _n

        else:
            if self.INPUT_ELEMENT_FORMAT:
                assert isinstance(system_input, self.INPUT_ELEMENT_FORMAT)
            new_input = FlexibleInput(system_input)
        return new_input

    def print_config(self):
        # params = ['kw','btu','cfm','ls']
        s = "{}\nSpecific Config\n{}\n".format("=" * 20, "=" * 20)
        for each in self.CONFIG_PARAMS:
            s += "    {} : {}\n".format(each, getattr(self, each))
        return s

    def __repr__(self):
        return "System name : {}\nFunction : {}\nInput : {}\nInitial Time : {}\nLast Execution : {}\nLast value : {}\n{}".format(
            self.name,
            str(self.__class__).split(".")[-1][:-2],
            self.input,
            self.t_0,
            self.last_execution,
            self.last_value,
            self.print_config(),
        )

    def __getitem__(self, name):
        if name in self.INPUT_ELEMENT_FORMAT.items:
            return self.input.value[name]
        else:
            return getattr(self, name)

    def __setitem__(self, name, value):
        if name in self.INPUT_ELEMENT_FORMAT.items:
            self.input.value[name] = value
        else:
            self.name = value


class ADD(System):
    """
    Simple system that adds the values contained in the input
    Input must be a list of things to add
    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=float("inf"))
    INPUT_ELEMENT_FORMAT = None
    CONFIG_PARAMS = None

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        randomness=False,
        random_error=0,
    ):
        super().__init__(
            system_input,
            system_output,
            name=name,
            randomness=randomness,
            random_error=random_error,
        )

    def process(self):
        output = 0
        for element in self.input:
            output += element.value
        return output


class SUB(System):
    """
    Simple system that subtract 2 values given
    Input must be a list of 2 things to subtract (first element - second element)
    """

    INPUT_ELEMENTS = _ELEMENTS(min=2, max=2)
    INPUT_ELEMENT_FORMAT = None
    CONFIG_PARAMS = None

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        randomness=False,
        random_error=0,
    ):
        super().__init__(
            system_input,
            system_output,
            name=name,
            randomness=randomness,
            random_error=random_error,
        )

    def process(self):
        a, b = self.input
        return a.value - b.value


class HEAT(System):
    """
    Simple system simulating the action of heating the input
    Based on flow, power and command, we "heat" the input to
    get the output
    """

    INPUT_ELEMENTS = _ELEMENTS(min=2, max=2)
    INPUT_ELEMENT_FORMAT = ValueCommandElement
    CONFIG_PARAMS = ["power_kw", "power_btu", "flow_cfm", "flow_ls"]

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        kw=None,
        btu=None,
        cfm=None,
        ls=None,
        randomness=False,
        random_error=0,
    ):
        super().__init__(
            system_input,
            system_output,
            name=name,
            randomness=randomness,
            random_error=random_error,
        )
        if kw:
            self.power_kw = kw
            self.power_btu = self.power_kw * 3412
        elif btu:
            self.power_btu = btu
            self.powe_kw = self.power_btu / 3412

        if cfm:
            self.flow_cfm = cfm
            self.flow_ls = cfm2ls(self.flow_cfm)
        elif ls:
            self.flow_ls = ls
            self.flow_cfm = ls2cfm(self.flow_ls)

    def process(self):
        temp, command = self.input
        return heating_deltaT_c(kw=self.power_kw * command, ls=self.flow_ls) + temp


class MIX(System):
    """
    This system takes in input made from MixInputElement and will
    calculate the resulting output of mixing the 2 inputs.
    """

    INPUT_ELEMENTS = _ELEMENTS(min=2, max=2)
    INPUT_ELEMENT_FORMAT = MixInputElement
    CONFIG_PARAMS = None

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        randomness=False,
        random_error=0,
    ):
        super().__init__(
            system_input,
            system_output,
            name=name,
            randomness=randomness,
            random_error=random_error,
        )

    def process(self):
        item1, item2 = self.input
        T1, V1 = item1.value
        T2, V2 = item2.value

        T = ((V1 * T1) + (V2 * T2)) / (V1 + V2)

        return T


class LINEAR(System):
    """
    Simple linear system that will compute an output based on a 
    maximum delta depending on a command.
    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=1)
    INPUT_ELEMENT_FORMAT = ValueCommandElement
    CONFIG_PARAMS = ["delta_max"]

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        delta_max=0,
        randomness=False,
        random_error=0,
    ):
        super().__init__(
            system_input,
            system_output,
            name=name,
            randomness=randomness,
            random_error=random_error,
        )
        self.delta_max = delta_max

    def process(self):

        sensor, command = self.input
        delta = (command / 100) * self.delta_max

        return sensor + delta


class COOL(System):
    """
    Simple system that will cool an input
    min_output serves in some cases like cooling valves where output 
    temperature could not go lower than chilled water temperature.
    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=1)
    INPUT_ELEMENT_FORMAT = ValueCommandElement
    CONFIG_PARAMS = ["delta_max", "min_output"]

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        delta_max=0,
        min_output=None,
        randomness=False,
        random_error=0,
    ):
        super().__init__(
            system_input,
            system_output,
            name=name,
            randomness=randomness,
            random_error=random_error,
        )
        self.delta_max = delta_max
        self.min_output = min_output

    def process(self):
        sensor, command = self.input
        delta = (command / 100) * self.delta_max
        output = sensor - delta
        if self.min_output:
            return max(output, self.min_output)
        else:
            return output