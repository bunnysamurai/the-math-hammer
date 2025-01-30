#!/usr/bin/env python

import copy
from math_hammer import AStat, DStat, Model, Unit
from math_hammer import StandardModifiers

'''
Tool for creating configuration data, namely units and modifiers for factions.

Will be a jumping off point for the full GUI, where users can:
1. load their faction data
2. configure an "encounter"
3. run the attack sequence
4. print the results.

This tool has the following objectives:
Define weapons and armour (attack and defence characteristics)
Define models (which are a list of weapons and an armour)
Define units (which are lists of models)
Define modifiers (which are composed from a fixed list of basic modifiers)

How about this?  Each faction-specific python file, when run, serializes all the relevant data
It's then a matter of determining a unified interface for the GUI tool to use
This idea is okay in the short-term, but ultimately I want to enable others to use this stuff.  Which means a nice UI, I think.
I think long-long-loooooong term we have all of this via the Web.  Thoughts put into the UI here will go a long way towards defining that.

'''
# ==============================================================================================================
# ==============================================================================================================

# CustomModifiers is just a dict of modifiers
'''
    Defining modifiers, what is the user experience?
    Basically, it's just selecting multiple modifiers, combining them, and giving them a name
'''
# It's also the working dict, so we initialize it with the standard modifiers
CustomModifiers = copy.deepcopy(StandardModifiers)

def get_list_of_custom_mods():
    return CustomModifiers.keys()

def create_new_mod_from_names(*nameargs):
    result = None
    for k in nameargs:
        mod = CustomModifiers[k]
        if result is None:
            result = mod
        else:
            result *= mod
    return result


def update_custom_modifiers(new_mod, new_mod_name):
    CustomModifiers[new_mod_name] = new_mod


# CustomWeapons is just a list of AStats
'''
    Defining weapons, what is the user experience?

    They need to enter in a bunch of fields.  This then gets added to the CustomWeapons dict.
        A name
        Range, Strength, AP, Damage, etc
        Optionally, a number of Modifiers can be added, as well
'''
# CustomWeapons = {}

# def get_list_of_custom_weapons():
#     return CustomWeapons.keys()

# def create_new_weapon(range, attacks, skill, strength, ap, damage, descrip, modifier=None):
#     result = AStat(Range=range, A=attacks, BS_WS=skill, S=strength, AP=ap, D=damage, description=descrip)
#     if modifier is not None:
#         result *= modifier
#     return result

# def update_custom_weapons(new_wpn, new_wpn_name):
#     CustomWeapons[new_wpn_name] = new_wpn

# CustomArmour is just a list of DStats
'''
    Armour is very similar to Weapons
'''
# CustomArmour = {}

# def get_list_of_custom_armour():
#     return CustomArmour.keys()

# def create_new_armour(toughness, save, wounds, descrip, invuln=None, ignorewounds=None, modifier=None):
#     result = DStat(T=toughness, Sv=save, W=wounds, Inv=invuln, FNP=ignorewounds, description=descrip)
#     if modifier is not None:
#         result *= modifier
#     return result

# def update_custom_armour(new_arm, new_arm_name):
#     CustomArmour[new_arm_name] = new_arm

# CustomModels is a list of a combination of the above
# CustomModels = {}

# def get_list_of_custom_models():
#     return CustomModels.keys()

# def create_new_model(weapons, armour, name, pts=None, position=0, modifier=None):
#     result = Model(weapons=weapons, defence=armour, pts=pts, name=name, position=position)
#     if modifier is not None:
#         result *= modifier
#     return result

# def update_custom_model(new_mdl, new_mdl_name):
#     CustomModels[new_mdl_name] = new_mdl

class Base():
    def __init__(self, descrip):
        self.data = {}
        self.descrip = descrip

    def modify(self, item, modifier): 
        if modifier is not None:
            item *= modifier
        return item

    def update(self, item, name):
        self.data[name] = item
    
    def get_list(self):
        return self.data.keys()
    
    def create_new(self, item, name, modifier):
        self.update(self.modify(item, modifier), name)

class CustomModifiers(Base):
    def create_new(self):
        pass

class CustomWeapons(Base):
    def create_new(self, range, attacks, skill, strength, ap, damage, descrip, modifier=None):
        super().create_new(AStat(Range=range, A=attacks, BS_WS=skill, S=strength, AP=ap, D=damage, description=descrip), descrip, modifier)

class CustomArmours(Base):
    def create_new(self, toughness, save, wounds, descrip, invuln=None, ignorewounds=None, modifier=None):
        super().create_new(DStat(T=toughness, Sv=save, W=wounds, Inv=invuln, FNP=ignorewounds, description=descrip), descrip, modifier)



class CustomModels(Base):
    def create_new(self, weapons, armour, name, pts=None, position=0, modifier=None):
        super().create_new(Model(weapons=weapons, defence=armour, pts=pts, name=name, position=position), name, modifier)




# CustomUnits is a list of CustomModels
CustomUnits = {}

def run_tests():
    print(f"Old List: {get_list_of_custom_mods()}")

    keylist = get_list_of_custom_mods()
    new_mod = create_new_mod_from_names(*keylist)
    update_custom_modifiers(new_mod, "new mod")

    print(f"New List: {get_list_of_custom_mods()}")

# ==============================================================================================================
# ==============================================================================================================
if __name__ == "__main__":
    run_tests()
else:
    pass