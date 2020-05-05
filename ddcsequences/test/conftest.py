#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacnet communication with another device
"""

import pytest
import BAC0
from yaml import load, dump, FullLoader
import os

from BAC0.core.devices.create_objects import (
    create_AV,
    create_MV,
    create_BV,
    create_AI,
    create_BI,
    create_AO,
    create_BO,
    create_CharStrValue,
)

from collections import namedtuple
import time

from bacpypes.primitivedata import CharacterString
from bacpypes.basetypes import EngineeringUnits


# from ddcsequences.simulate.equipment import Pump
from ddcsequences.simulate.equipment import generate

params_file = os.path.join(os.getcwd(), "ddcsequences/test/equipments_params.yaml")


@pytest.fixture(scope="session")
def network_and_devices():
    bacnet = BAC0.lite()

    def _add_points(device):
        # Add a lot of points for tests (segmentation required)

        mvs = []
        avs = []
        bvs = []
        ais = []
        bis = []
        aos = []
        bos = []
        charstr = []

        pump_command = create_BO(oid=1, name="P1-C", pv=1)
        pump_command.description = "Pump P-1 Command"
        bos.append(pump_command)

        pump_status = create_BI(oid=1, name="P1-S", pv=1)
        pump_status.description = "Pump P-1 Status"
        bis.append(pump_status)

        # for i in range(qty):
        #    mvs.append(create_MV(oid=i, name="mv{}".format(i), pv=1, pv_writable=True))
        #    new_av = create_AV(oid=i, name="av{}".format(i), pv=99.9, pv_writable=True)
        #    new_av.units = EngineeringUnits.enumerations["degreesCelsius"]
        #    new_av.description = "Fake Description {}".format(i)
        #    avs.append(new_av)
        #    bvs.append(create_BV(oid=i, name="bv{}".format(i), pv=1, pv_writable=True))
        #    ais.append(create_AI(oid=i, name="ai{}".format(i), pv=99.9))
        #    aos.append(create_AO(oid=i, name="ao{}".format(i), pv=99.9))
        #    bis.append(create_BI(oid=i, name="bi{}".format(i), pv=1))
        #    bos.append(create_BO(oid=i, name="bo{}".format(i), pv=1))
        #    charstr.append(
        #        create_CharStrValue(
        #            oid=i,
        #            name="string{}".format(i),
        #            pv=CharacterString("test"),
        #            pv_writable=True,
        #        )
        #    )

        for mv in mvs:
            device.this_application.add_object(mv)
        for av in avs:
            device.this_application.add_object(av)
        for bv in bvs:
            device.this_application.add_object(bv)
        for ai in ais:
            device.this_application.add_object(ai)
        for ao in aos:
            device.this_application.add_object(ao)
        for bi in bis:
            device.this_application.add_object(bi)
        for bo in bos:
            device.this_application.add_object(bo)
        for cs in charstr:
            device.this_application.add_object(cs)

    # Create the app that will store variables and mimic a controller.
    device_app = BAC0.lite(port=47809)
    _add_points(device_app)
    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    # Connect to test device using main network
    test_device = BAC0.device("{}:47809".format(ip), boid, bacnet, poll=10)

    # Now create a pump
    mypump = generate(filename=params_file, controller=test_device)

    params = namedtuple("devices", ["bacnet", "device_app", "test_device", "mypump"])
    params.bacnet = bacnet
    params.device_app = device_app
    params.test_device = test_device
    params.mypump = mypump

    yield params

    # Close when done
    params.test_device.disconnect()

    params.bacnet.disconnect()
    # If too quick, we may encounter socket issues...
    time.sleep(1)


def generate_equipment(filename, create_method, controller, key):
    with open(filename, "r") as file:
        equipment_params = load(file, Loader=FullLoader)
    return create_method(controller=controller, config=equipment_params[key])
