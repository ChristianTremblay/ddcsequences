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


class EquipmentGroup:
    """
    Group of equipements serving one goal.
    For example, pumps in parallel will result in one group output being
    controlled by two devices.

    I mean by that : Pump A or Pump B will generate a flow in output.

    This class serves as a base for group and behaviour will need to 
    be defined in each groups accordingly.
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
        try:
            for equipment in self.equipments:
                equipment.refresh()
        except AttributeError:
            pass

    def __repr__(self):
        return "{}".format(self.name)

    def __getitem__(self, name):
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
    def get_value(value, convert_boolean=False):
        if isinstance(value, Point):
            _value = value.lastValue
            if _value == "active" or value == "1: active":
                if convert_boolean:
                    return 100
                else:
                    return True
            elif _value == "inactive" or _value == "0: inactive":
                if convert_boolean:
                    return 0
                else:
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
            method()
        except (NotImplementedError, AttributeError) as error:
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
        # self.refresh()
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
