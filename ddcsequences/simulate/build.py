from yaml import load, dump, FullLoader

from .equipment import Equipment, EquipmentGroup

from .equipments import (
    Chiller,
    MixedAirDampers,
    DX_Cooling_Stage,
    Pump,
    ParallelPumps,
    Tank,
    Valve,
    Fan,
)


def create_equip(controller, config=None, name=None):
    """
    This function helps in the creation of equipments.
    It relies on a config dict to generate equipments
    and make all the links with the BAC0 device.

    The yaml file format is : 
    
    name:
        class: Classname
        description: str
        statics:
            variable1: value
            variable2: value 
        inputs:
            variable1: Name_of_BAC0_point
        outputs:
            variable1: Name_of_BAC0_point
        add_property:
            level0:
                proximity: [LT-2G, 0]

    Inputs and outputs sections will generate a match_value between the
    variable of the equipment and the BAC0 point.


    """
    _classes = {
        "Pump": Pump,
        "ParallelPumps": ParallelPumps,
        "Chiller": Chiller,
        "Valve": Valve,
        "Tank": Tank,
        "MixedAirDamper": MixedAirDampers,
        "Fan": Fan,
    }
    controller = controller
    try:
        _equip = _classes[config["class"]](name=name, description=config["description"])
    except KeyError:
        raise ConfigFileError(
            "Can't create an equipment of type {}.".format(config["class"])
        )
    try:
        for k, v in config["statics"].items():
            if k == "members":
                _members = [Equipment.defined[each] for each in v]
                setattr(_equip, "members", _members)
                continue
            if v:
                setattr(_equip, k, v)
    except (AttributeError, KeyError):
        pass
    try:
        for k, v in config["inputs"].items():
            if v and controller:
                var = controller[v]
                setattr(_equip, k, var)
    except (AttributeError, KeyError):
        pass
    try:
        for property_name, params in config["add_property"].items():
            _equip._add_property(property_name, params)
    except (AttributeError, KeyError):
        pass
    try:
        for k, v in config["outputs"].items():
            if v and controller:
                controller[v].match_value(getattr(_equip, k))
    except (AttributeError, KeyError):
        pass

    return _equip


def open_config_file(filename):
    """
    Turns the yaml file into a dict
    Some validation could occur here
    """
    with open(filename, "r") as file:
        equipment_params = load(file, Loader=FullLoader)
    return equipment_params


def generate(controller, config):
    params = config if isinstance(config, dict) else open_config_file(config)
    # new_equip = []
    for k, v in params.items():
        print("Creating {} | {}".format(k, v["description"]))
        try:
            _ = create_equip(controller=controller, config=v, name=k)
        except ConfigFileError as error:
            print("{}".format(error))
            continue
    return {"equipments": Equipment.defined, "groups": EquipmentGroup.defined}


class ConfigFileError(Exception):
    pass
