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

from bacpypes.local.object import (
    AnalogOutputCmdObject,
    AnalogValueCmdObject,
    BinaryOutputCmdObject,
    BinaryValueCmdObject,
)
from bacpypes.object import AnalogInputObject, BinaryInputObject, register_object_type
from bacpypes.basetypes import EngineeringUnits
from bacpypes.primitivedata import CharacterString

from collections import namedtuple
import time

from bacpypes.primitivedata import CharacterString
from bacpypes.basetypes import EngineeringUnits


# from ddcsequences.simulate.equipment import Pump
from ddcsequences.simulate.equipment import generate, Equipment

# params_file = os.path.join(os.getcwd(), "ddcsequences/test/equipments_params.yaml")
test_equipments = {
    "MYTANK": {
        "class": "Tank",
        "description": "Bassin 1",
        "statics": {"level": 0, "number_of_switches": 7},
        "add_property": {
            "level0": 0,
            "level1": 1,
            "level2": 2,
            "level3": 3,
            "level4": 4,
            "level5": 5,
            "level6": 6,
        },
        "inputs": None,
        "outputs": {"level0": "LEVEL0-IN"},
    },
    "MYPUMP": {
        "class": "Pump",
        "description": "A test pump",
        "statics": None,
        "inputs": None,
        "outputs": None,
    },
}


@pytest.fixture(scope="session")
def network_and_devices():
    # Register class to activate behaviours
    register_object_type(AnalogOutputCmdObject, vendor_id=842)
    register_object_type(AnalogValueCmdObject, vendor_id=842)
    register_object_type(BinaryOutputCmdObject, vendor_id=842)
    register_object_type(BinaryValueCmdObject, vendor_id=842)

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

        pump_command = create_BO(oid=1, name="P1-C", pv=0)
        pump_command.description = "Pump P-1 Command"
        bos.append(pump_command)

        pump_status = create_BI(oid=1, name="P1-S", pv=0)
        pump_status.description = "Pump P-1 Status"
        bis.append(pump_status)

        level0_switch = create_BI(oid=2, name="LEVEL0-IN", pv=0)
        level0_switch.description = "Tank Level 0 Bi"
        bis.append(level0_switch)

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
    # _add_points(device_app)
    ip = device_app.localIPAddr.addrTuple[0]
    boid = device_app.Boid

    # Create BACnet object and add them to device
    level0_input = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 1),
        objectName="LEVEL0-IN",
        presentValue="inactive",
        description=CharacterString("Proximity level switch"),
    )
    pump_command = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 2),
        objectName="P1-C",
        presentValue="inactive",
        description=CharacterString("Pump command"),
    )
    pump_status = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 3),
        objectName="P1-S",
        presentValue="inactive",
        description=CharacterString("Pump status"),
    )

    device_app.this_application.add_object(level0_input)
    device_app.this_application.add_object(pump_command)
    device_app.this_application.add_object(pump_status)

    # Connect to test device using main network
    test_device = BAC0.device("{}:47809".format(ip), boid, bacnet, poll=10)

    # Now create test equipments
    generate(controller=test_device, config=test_equipments)

    params = namedtuple(
        "devices", ["bacnet", "device_app", "test_device", "equipments"]
    )
    params.bacnet = bacnet
    params.device_app = device_app
    params.test_device = test_device
    params.equipments = Equipment.defined
    yield params

    # Close when done
    params.test_device.disconnect()

    params.bacnet.disconnect()
    # If too quick, we may encounter socket issues...
    time.sleep(1)


"""

import BAC0

from BAC0.core.utils.notes import note_and_log

from bacpypes.local.object import (
    AnalogOutputCmdObject,
    AnalogValueCmdObject,
    BinaryOutputCmdObject,
    BinaryValueCmdObject,
)
from bacpypes.object import AnalogInputObject, BinaryInputObject, register_object_type
from bacpypes.basetypes import EngineeringUnits
from bacpypes.primitivedata import CharacterString

import time


def start_device(ip, deviceId):
    try:
        new_device = BAC0.lite(
            ip=ip, deviceId=deviceId, localObjName="BAC0_DaVinci_Fireplace"
        )
    except Exception:
        new_device = BAC0.lite(deviceId=deviceId, localObjName="BAC0_DaVinci_Fireplace")
    time.sleep(1)

    # Register class to activate behaviours
    register_object_type(AnalogOutputCmdObject, vendor_id=842)
    register_object_type(AnalogValueCmdObject, vendor_id=842)
    register_object_type(BinaryOutputCmdObject, vendor_id=842)
    register_object_type(BinaryValueCmdObject, vendor_id=842)

    online = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 1),
        objectName="Fireplace Online",
        presentValue="inactive",
        description=CharacterString("Communication status on the serial interface"),
    )
    ledpulse_bv = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 2),
        objectName="LEDPULSE",
        presentValue="inactive",
        description=CharacterString(
            "Set Led to pulse between current color and color set by LEDCOLOR after turning on LEDPULSE on"
        ),
    )
    flameenable_bv = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 3),
        objectName="FLAME-EN",
        presentValue="inactive",
        description=CharacterString(
            "If set to false, will prevent FLAME to be turned ON"
        ),
    )
    flamealarm_bv = BinaryValueCmdObject(
        objectIdentifier=("binaryValue", 4),
        objectName="FLAME-ALARM",
        presentValue="inactive",
        minimumOnTime=300,
        description=CharacterString(
            "Will be On if there is a discrepancy between command and status of flame"
        ),
    )

    led_bo = BinaryOutputCmdObject(
        objectIdentifier=("binaryOutput", 1),
        objectName="LED",
        presentValue="inactive",
        description=CharacterString("Turns the LED on or off"),
    )
    flame_bo = BinaryOutputCmdObject(
        objectIdentifier=("binaryOutput", 2),
        objectName="FLAME",
        presentValue="inactive",
        description=CharacterString("Turns flame relay on or off"),
    )
    heatfan_bo = BinaryOutputCmdObject(
        objectIdentifier=("binaryOutput", 3),
        objectName="HEATFAN",
        presentValue="inactive",
        description=CharacterString(
            "Turns the heat exchanger blower on or off, if present"
        ),
    )
    lamp_bo = BinaryOutputCmdObject(
        objectIdentifier=("binaryOutput", 4),
        objectName="LAMP",
        presentValue="inactive",
        description=CharacterString("Lamp on or off (non LED)"),
    )
    auxburner_bo = BinaryOutputCmdObject(
        objectIdentifier=("binaryOutput", 5),
        objectName="AUXBURNER",
        presentValue="inactive",
        description=CharacterString("Auxiliary burner or valve, if present"),
    )

    ledfadetime_av = AnalogValueCmdObject(
        objectIdentifier=("analogValue", 1),
        objectName="LEDFADETIME",
        presentValue=0,
        units=EngineeringUnits("milliseconds"),
        description=CharacterString("Sets fade time between led colors (0-32767)"),
    )
    leddwelltime_av = AnalogValueCmdObject(
        objectIdentifier=("analogValue", 2),
        objectName="LEDDWELLTIME",
        presentValue=0,
        units=EngineeringUnits("milliseconds"),
        description=CharacterString(
            "Sets how long a color will remain before it transistions to the newer color"
        ),
    )
    ledcolorR_av = AnalogValueCmdObject(
        objectIdentifier=("analogValue", 3),
        objectName="LEDCOLOR_R",
        relinquishDefault=100,
        presentValue=100,
        description=CharacterString("RED value of LEDCOLOR (0-255)"),
    )
    ledcolorG_av = AnalogValueCmdObject(
        objectIdentifier=("analogValue", 4),
        objectName="LEDCOLOR_G",
        relinquishDefault=100,
        presentValue=100,
        description=CharacterString("GREEN value of LEDCOLOR (0-255)"),
    )

    ledcolorB_av = AnalogValueCmdObject(
        objectIdentifier=("analogValue", 5),
        objectName="LEDCOLOR_B",
        relinquishDefault=100,
        presentValue=100,
        description=CharacterString("BLUE value of LEDCOLOR (0-255)"),
    )
    ledcolorW_av = AnalogValueCmdObject(
        objectIdentifier=("analogValue", 6),
        objectName="LEDCOLOR_W",
        relinquishDefault=100,
        presentValue=100,
        description=CharacterString("WHITE value of LEDCOLOR (0-255)"),
    )
    humidity_ai = AnalogInputObject(
        objectIdentifier=("analogInput", 1),
        objectName="HUMIDITY",
        presentValue=0,
        units=EngineeringUnits("percentRelativeHumidity"),
        description=CharacterString("Reading of humidity sensor"),
    )
    temperature_ai = AnalogInputObject(
        objectIdentifier=("analogInput", 2),
        objectName="TEMPERATURE",
        presentValue=0,
        units=EngineeringUnits("degreesCelsius"),
        description=CharacterString("Reading of temperature sensor"),
    )
    dewpoint_ai = AnalogInputObject(
        objectIdentifier=("analogInput", 3),
        objectName="DEWPOINT",
        presentValue=0,
        units=EngineeringUnits("degreesCelsius"),
        description=CharacterString(
            "Calculated dewpoint based on temperature and humidity readings"
        ),
    )

    heatfanspeed_ao = AnalogOutputCmdObject(
        objectIdentifier=("analogOutput", 1),
        objectName="HEATFANSPEED",
        presentValue=0,
        description=CharacterString("Sets speed of heat exchanger"),
    )
    flamelevel_ao = AnalogOutputCmdObject(
        objectIdentifier=("analogOutput", 2),
        objectName="FLAMELEVEL",
        presentValue=0,
        description=CharacterString("Level of flame, if present (1-10)"),
    )
    lamplevel_ao = AnalogOutputCmdObject(
        objectIdentifier=("analogOutput", 3),
        objectName="LAMPLEVEL",
        presentValue=6,
        description=CharacterString("Level of lamp (1-10)"),
    )

    # BV
    new_device.this_application.add_object(online)
    new_device.this_application.add_object(ledpulse_bv)
    new_device.this_application.add_object(flameenable_bv)
    new_device.this_application.add_object(flamealarm_bv)

    # BO
    new_device.this_application.add_object(led_bo)
    new_device.this_application.add_object(flame_bo)
    new_device.this_application.add_object(heatfan_bo)
    new_device.this_application.add_object(lamp_bo)
    new_device.this_application.add_object(auxburner_bo)

    # AI
    new_device.this_application.add_object(humidity_ai)
    new_device.this_application.add_object(temperature_ai)
    new_device.this_application.add_object(dewpoint_ai)

    # AO
    new_device.this_application.add_object(heatfanspeed_ao)
    new_device.this_application.add_object(flamelevel_ao)
    new_device.this_application.add_object(lamplevel_ao)

    # AV
    new_device.this_application.add_object(ledfadetime_av)
    new_device.this_application.add_object(leddwelltime_av)
    new_device.this_application.add_object(ledcolorR_av)
    new_device.this_application.add_object(ledcolorG_av)
    new_device.this_application.add_object(ledcolorB_av)
    new_device.this_application.add_object(ledcolorW_av)

    return new_device

"""
