from ddcsequences.simulate.equipment import OnOffDevice, Pump

import time


# def test_onoffdevice():
#    dev = OnOffDevice()
#    assert dev.status == False

#    dev.start_command = True
#    assert dev.status == True

#    dev.start_command = False
#    assert dev.status == False

#    dev.start()
#    assert dev.status == True

#    dev.stop()
#    assert dev.status == False


# def test_pump():
#    pump = Pump(name="my_pump")
#    assert pump.name == "my_pump"
#    assert pump.status == False

#    pump.start()
#    assert pump.status == True
#    time.sleep(1)
#    assert pump.pressure > 0
#    assert pump.flow > 0
#    assert pump.amperage > 0
#    t0_press = pump.pressure
#    t0_flow = pump.flow
#    pump.modulation = 0
#    time.sleep(3)
#    assert pump.pressure < t0_press
#    assert pump.flow < t0_flow
#    pump.start_command = False
#    pump.refresh()
#    assert pump.status == False
#    assert pump.flow < pump.max_flow
#    assert pump.pressure < pump.succion_pressure + pump.delta_p
#    assert pump.amperage < pump.max_amperage
