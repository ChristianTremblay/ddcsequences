#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.

from collections import namedtuple, deque
import time
from datetime import datetime as dt
from random import uniform
import numpy as np
import math

from ddcmath.heating import heating_deltaT_c
from ddcmath.airflow import cfm2ls, ls2cfm

from BAC0.core.devices.Points import Point

_ELEMENTS = namedtuple("INPUT_ELEMENTS", ["min", "max"])


class Dampening(object):
    """
    In the context of simulation, I want to break the linearity
    This will apply a exponential decay factor based on time so
    maximum power will be available after 3*tau (typically 3*10sec = 30sec)

    Une image vaut mille mots

    ^                            ^
    |      ___                   |
    |     |   |           =>     |       .-.
    | ____|   |______            | ___.-`   `-.___
    |__________________          |__________________
    
    
    Decay is calculated as a log function applied from the starting time 
    of the system (or its change of value).
    Meaning that even if the block isn't executed in the mean time, the day we'll read
    the output, we'll get the value where it should be.
    
    """

    def __init__(self, tau=10):
        self.factor = 1
        self.tau = tau
        self.tmax = 10 * self.tau
        self.t = None
        self.y = None
        self.t0 = None
        self.running = False
        self.rising = False
        self.dropping = False

    def calculate(self, t0, rise=True):
        self.t0 = t0
        self.t = np.linspace(0, self.tmax, 1000)
        if rise:
            self.y = self.factor - (self.factor * np.exp(-self.t / self.tau))
        else:
            self.y = -self.factor * np.exp(-self.t / self.tau)

    @property
    def value(self):
        result = -1
        _now = dt.now()
        self._dt = (_now - self.t0).seconds
        for i, each in enumerate(self.t):
            if self._dt <= each:
                result = self.y[i]
                break
        if result > 0.99 or result == -1:
            result = 1
            self.running = False
            self.rising = False
            self.dropping = False
        return result

    def rise(self, t0=None):
        if not t0:
            t0 = dt.now()
        self.running = True
        self.rising = True
        self.dropping = False
        self.calculate(t0=t0)
        return self.value

    def drop(self, t0=None):
        if not t0:
            t0 = dt.now()
        self.running = True
        self.dropping = True
        self.rising = False
        self.calculate(t0=t0)
        return self.value

    def __repr__(self):
        s = "\n{}\nDampening\n{}\n".format("=" * 20, "=" * 20)
        for each in self.__dict__:
            s += "    {} : {}\n".format(each, getattr(self, each))
        return s


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
        This will cover the case of a BAC0.point or Systems that
        could also become the "input" of another system
        """
        if isinstance(item, Point):
            return item.lastValue
        elif isinstance(item, System):
            return item.output
        else:
            return item

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


class ValueElement(InputElement):
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

    items = ["value"]

    def __init__(self, value=None):
        self._value = value

    @property
    def value(self):
        return InputElement.get_value(self._value)

    def __repr__(self):
        return "Value : {}".format(self.value)


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

    def __getitem__(self, name):
        if name in self._input.items:
            return self._input[name]

    def __setitem__(self, name, value):
        if name in self._input.items:
            self._input[name] = value


class System(object):
    """
    A system is a black box. You give it an input, it will throw out an output.
    This class must be subclassed by more specific systems containing a method
    called "process". This will define the behaviour of the system.

    Input of a system can be another system. This will allow cascading systems
    to create something more complex.

    Timing is provided to cover transient reaction of systems.

    """

    ids = 0

    def __init__(self, system_input, system_output=None, name=None, random_error=0):
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
        self.random_error = random_error

    def _pre_process(self):
        if not self.t_0:
            self.t_0 = dt.now()
        if self.last_execution:
            self.dt = self.last_execution - self.t_0
        out = self.process()
        self.last_execution = dt.now()
        if self.random_error != 0:
            out += uniform(-self.random_error, self.random_error)
        self.last_value = out
        return out

    @property
    def output(self):
        return self._pre_process()
        # return self.process()

    def execution(self):
        # To be used with BAC0 .match_value and get a Callable
        return self.output

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
                assert isinstance(each, self.INPUT_ELEMENT_FORMAT)
                _n.append(FlexibleInput(each))
            new_input = _n

        else:
            if self.INPUT_ELEMENT_FORMAT:
                assert isinstance(system_input, self.INPUT_ELEMENT_FORMAT)
            new_input = FlexibleInput(system_input)
        return new_input

    def print_config(self):
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
        if isinstance(self.INPUT_ELEMENT_FORMAT, tuple):
            for each in self.INPUT_ELEMENT_FORMAT:
                if name in each.items:
                    return self.input.value[name]
        else:
            if name in self.INPUT_ELEMENT_FORMAT.items:
                return self.input.value[name]
        return getattr(self, name)

    def __setitem__(self, name, value):
        if isinstance(self.INPUT_ELEMENT_FORMAT, tuple):
            for each in self.INPUT_ELEMENT_FORMAT:
                if name in each.items:
                    self.input.value[name] = value
        else:
            if name in self.INPUT_ELEMENT_FORMAT.items:
                self.input.value[name] = value
            else:
                self.name = value


class PASSTHRU(System):
    """
    Simple system that takes the values contained in the input
    and give it back in its output
    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=1)
    INPUT_ELEMENT_FORMAT = (System, list, float, int)
    CONFIG_PARAMS = ["element1"]

    def __init__(self, system_input, system_output=None, name=None, random_error=0):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.element1 = self.input

    def process(self):
        return self.element1


class SELECT(System):
    """
    System to be used to make selection between inputs.
    The selected input becomes the output
    """

    INPUT_ELEMENTS = _ELEMENTS(min=2, max=2)
    INPUT_ELEMENT_FORMAT = (System, list, float, int)
    CONFIG_PARAMS = ["element1", "element2", "selection"]

    def __init__(
        self, system_input, system_output=None, name=None, random_error=0, select=False
    ):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.element1, self.element2 = self.input
        self.selection = select

    def process(self):
        if self.selection:
            return self.element2
        else:
            return self.element1


class ADD(System):
    """
    Simple system that adds the values contained in the input
    Input must be a list of things to add
    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=float("inf"))
    INPUT_ELEMENT_FORMAT = (System, list, float, int)
    CONFIG_PARAMS = ["elements"]

    def __init__(self, system_input, system_output=None, name=None, random_error=0):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.elements = self.input

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
    INPUT_ELEMENT_FORMAT = (System, list, float, int)
    CONFIG_PARAMS = ["element1", "element2"]

    def __init__(self, system_input, system_output=None, name=None, random_error=0):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.element1, self.element2 = self.input

    def process(self):
        return self.element1.value - self.element2.value


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
        random_error=0,
    ):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
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
    CONFIG_PARAMS = ["element1", "element2"]

    def __init__(self, system_input, system_output=None, name=None, random_error=0):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.element1, self.element2 = self.input

    def process(self):
        # item1, item2 = self.input
        T1, V1 = self.element1.value
        T2, V2 = self.element2.value

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
        random_error=0,
        decrease=False,
    ):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.delta_max = delta_max
        self.decrease = decrease

    def _effect(self):
        if self.decrease:
            return -1
        else:
            return 1

    def process(self):

        sensor, command = self.input
        delta = (command / 100) * self.delta_max

        return sensor + (self._effect() * delta)


class SPAN(System):
    """
    Simple linear system that will compute an output based on a 
    maximum delta depending on a command.
    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=1)
    INPUT_ELEMENT_FORMAT = (System, ValueElement, int, float)
    CONFIG_PARAMS = ["xrange_A", "xrange_B", "yrange_A", "yrange_B"]

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        xrange_A=0,
        xrange_B=100,
        yrange_A=0,
        yrange_B=100,
        use_command=False,
        random_error=0,
    ):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.xrange_A = xrange_A
        self.xrange_B = xrange_B
        self.yrange_A = yrange_A
        self.yrange_B = yrange_B

    def process(self):
        if isinstance(self.input, ValueElement):
            new_input = self.input.value["value"]
        else:
            new_input = self.input.value

        if new_input <= self.xrange_A:
            y = self.yrange_A
        elif new_input >= self.xrange_B:
            y = self.yrange_B

        else:
            # prop = (new_input / (self.input_max - self.input_min))
            m = (self.yrange_B - self.yrange_A) / (self.xrange_B - self.xrange_A)
            b = self.yrange_A - m * (self.xrange_A)
            # y = mx + b
            y = m * new_input + b
        return y


class TRANSIENT(System):
    """
    System that will increase or decrease an input
    min_output serves in some cases like cooling valves where output 
    temperature could not go lower than chilled water temperature.

    This system use the dampening function 

    """

    INPUT_ELEMENTS = _ELEMENTS(min=1, max=1)
    INPUT_ELEMENT_FORMAT = (System, ValueCommandElement, ValueElement)
    CONFIG_PARAMS = [
        "delta_max",
        "min_output",
        "max_output",
        "last_command",
        "last_input",
        "last_offset",
        "tau",
        "decrease",
    ]

    def __init__(
        self,
        system_input,
        system_output=None,
        name=None,
        delta_max=0,
        min_output=None,
        max_output=None,
        tau=10,
        decrease=False,
        random_error=0,
    ):
        super().__init__(
            system_input, system_output, name=name, random_error=random_error
        )
        self.delta_max = delta_max
        self.min_output = min_output
        self.max_output = max_output
        self.last_command = 0
        self.last_input = 0
        self.last_offset = 0
        self.tau = tau
        self._changes = []
        self.decrease = decrease

    def _effect(self):
        # Select between increasing effect and decreasing effect
        if self.decrease:
            return -1
        else:
            return 1

    def calculcate_dT(self):
        _transient_over_list = []
        dT = 0
        transient_over = True
        for delta_T, dampening in self._changes:
            if isinstance(dampening, Dampening):
                damp_value = dampening.value
            else:
                damp_value = 1
            dT += delta_T * damp_value
            if damp_value < 1:
                transient_over = False
        return (dT, transient_over)

    def process_value_command_element(self):
        sensor, command = self.input
        if callable(command):
            command = command()

        def _clean():
            _delta_T = (command / 100) * self.delta_max
            self._changes = [(_delta_T, 1)]
            new_dT, can_clean = self.calculcate_dT()
            dT = new_dT
            return dT

        if not math.isclose(command, self.last_command, rel_tol=0.1):
            delta_command = command - self.last_command
            _dampening = Dampening(self.tau)
            _delta_T = (delta_command / 100) * self.delta_max
            if delta_command < 0:
                _dampening.drop()
            else:
                _dampening.rise()
            self._changes.append([_delta_T, _dampening])

            dT, can_clean = self.calculcate_dT()
            self.last_command = command
            self.t_0 = _dampening.t0

        else:
            # Nothing change, clean and continue
            old_dT, can_clean = self.calculcate_dT()
            if can_clean:
                dT = _clean()
            else:
                dT = old_dT
        self.last_offset = dT
        output = sensor + (self._effect() * dT)
        return output

    def process_value_element(self, force_input=None):
        if force_input:
            new_input = force_input
        else:
            # Called twice ? Why does block here...when input is a MIX
            try:
                new_input = self.input.value["value"]
            except TypeError:
                new_input = force_input
        if isinstance(new_input, System):
            new_input = new_input.output

        def _clean():
            new_dT, can_clean = self.calculcate_dT()
            dT = new_dT
            return dT

        if not math.isclose(new_input, self.last_input, rel_tol=0.1):
            delta_input = new_input - self.last_input
            _dampening = Dampening(self.tau)
            _delta_T = delta_input
            if delta_input < 0:
                _dampening.drop()
            else:
                _dampening.rise()
            self._changes.append([delta_input, _dampening])

            dT, can_clean = self.calculcate_dT()
            self.last_input = new_input
            self.t_0 = _dampening.t0

        else:
            # Nothing change, clean and continue
            old_dT, can_clean = self.calculcate_dT()
            if can_clean:
                dT = new_input
                self._changes = [(new_input, 1)]
            else:
                dT = old_dT

        self.last_offset = dT
        output = self._effect() * dT
        return output

    def process(self):
        output = None

        if isinstance(self.input.value, ValueCommandElement):
            output = self.process_value_command_element()
        elif isinstance(self.input.value, ValueElement):
            output = self.process_value_element()
        else:
            # if isinstance(self.input, System):
            try:
                output = self.process_value_element(force_input=self.input.value)
            except TypeError as error:
                print(self.input.value, error)
            # output = float("-inf")

        if self.max_output:
            output = min(output, self.max_output)

        if self.min_output:
            output = max(output, self.min_output)
        # if output == self.max_output or output == self.min_output:
        #    _ = _clean()

        return output
