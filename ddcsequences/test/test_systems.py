from ddcsequences.simulate.system import (
    System,
    ADD,
    SUB,
    HEAT,
    ValueCommandElement,
    MixInputElement,
    MIX,
    LINEAR,
)


def test_add():
    a = ADD([2, 3])
    assert a.output == 5


def test_sub():
    b = SUB([10, 6])
    assert b.output == 4


def test_mix():
    m1 = MixInputElement(-20, 10)
    m2 = MixInputElement(21, 90)
    m = MIX([m1, m2])
    assert m.output == 16.9


def test_linear():
    i = ValueCommandElement(0, 100)
    VFD = LINEAR(i, delta_max=20)
    assert VFD.output == 20
    VFD["command"] = 50
    assert VFD.output == 10
