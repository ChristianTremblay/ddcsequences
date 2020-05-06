from ddcsequences.simulate.equipment import Equipment, generate, OnOffDevice, Pump
from ddcsequences.tools import wait_for_state

import time


def test_onoffdevice(network_and_devices):
    dev = OnOffDevice()
    assert dev.status() == False
    dev.start_command = True
    assert dev.status() == True

    dev.start_command = False
    assert dev.status() == False

    dev.start()
    assert dev.status() == True

    dev.stop()
    assert dev.status() == False


def test_pump(network_and_devices):
    pump = network_and_devices.equipments["MYPUMP"]
    assert pump.name == "MYPUMP"
    assert pump.description == "A test pump"
    assert pump.status() == False

    pump.start()
    assert pump.status() == True
    time.sleep(1)
    assert pump.pressure() > 0
    assert pump.flow() > 0
    assert pump.amperage() > 0
    t0_press = pump.pressure()
    t0_flow = pump.flow()
    pump.modulation = 0
    time.sleep(3)
    assert pump.pressure() < t0_press
    assert pump.flow() < t0_flow
    pump.start_command = False
    pump.refresh()
    assert pump.status() == False
    assert pump.flow() < pump.max_flow
    assert pump.pressure() < pump.succion_pressure + pump.delta_p
    assert pump.amperage() < pump.max_amperage


def test_tank(network_and_devices):
    mytank = network_and_devices.equipments["MYTANK"]
    test_device = network_and_devices.test_device
    assert mytank.name == "MYTANK"
    assert mytank.description == "Bassin 1"
    assert mytank.level0() == False
    wait_for_state(test_device["LEVEL0-IN"], False, timeout=6, log_only=False)
    assert mytank.level1() == False
    assert mytank.level2() == False
    assert mytank.level3() == False
    assert mytank.level4() == False
    assert mytank.level5() == False
    assert mytank.level6() == False
    mytank.level = 50
    assert mytank.level0() == True
    wait_for_state(test_device["LEVEL0-IN"], True, timeout=6, log_only=False)
    assert mytank.level1() == True
    assert mytank.level2() == True
    assert mytank.level3() == True
    assert mytank.level4() == False
    assert mytank.level5() == False
    assert mytank.level6() == False
    mytank.level = 100
    assert mytank.level0() == True
    wait_for_state(test_device["LEVEL0-IN"], True, timeout=6, log_only=False)
    assert mytank.level1() == True
    assert mytank.level2() == True
    assert mytank.level3() == True
    assert mytank.level4() == True
    assert mytank.level5() == True
    assert mytank.level6() == True
    mytank.level = 0
    wait_for_state(test_device["LEVEL0-IN"], False, timeout=6, log_only=False)
