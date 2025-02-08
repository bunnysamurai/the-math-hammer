#!/usr/bin/env python

import copy
import matplotlib.pyplot as plt

from math_hammer import AStat, DStat, Model, Unit, Dice
from math_hammer import StandardModifiers
from math_hammer import perform_full_analysis, update_position

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

class CustomFactionBase():
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

    def get_item(self, key):
        return self.data[key]
    
    def create_new(self, item, name, modifier):
        self.update(self.modify(item, modifier), name)

class CustomFactionModifiers(CustomFactionBase):
    def __init__(self, descrip):
        super().__init__(descrip)
        self.data = copy.deepcopy(StandardModifiers)

    def create_new(self, nameargs, name):
        '''
            Here we assume nameargs only contains valid keys in the data dict.  This may be a big assumption. 
        '''
        result = None
        for k in nameargs:
            mod = copy.deepcopy(self.get_item(k))
            if result is None:
                result = mod
            else:
                result *= mod
        self.update(result, name)

class CustomFactionWeapons(CustomFactionBase):
    def create_new(self, range, attacks, skill, strength, ap, damage, descrip, modifier=None):
        super().create_new(AStat(Range=range, A=attacks, BS_WS=skill, S=strength, AP=ap, D=damage, description=descrip), descrip, modifier)

class CustomFactionArmours(CustomFactionBase):
    def create_new(self, toughness, save, wounds, descrip, invuln=None, ignorewounds=None, modifier=None):
        super().create_new(DStat(T=toughness, Sv=save, W=wounds, Inv=invuln, FNP=ignorewounds, description=descrip), descrip, modifier)

class CustomFactionModels(CustomFactionBase):
    def create_new(self, weapons, armour, name, pts=None, position=0, modifier=None):
        super().create_new(Model(weapons=weapons, defence=armour, pts=pts, name=name, position=position), name, modifier)

class CustomFactionUnits(CustomFactionBase):
    def create_new(self, model_list, name, modifier=None):
        super().create_new(Unit(model_list=model_list, name=name), name=name, modifier=modifier)

def run_tests():
    # let's make an Emperor's Champion 
    Black_Templars_Modifiers = CustomFactionModifiers("Black Templar Modifiers")
    Black_Templars_Weapons = CustomFactionWeapons("Black Templar Weapons")
    Black_Templars_Armours = CustomFactionArmours("Black Templar Armours")
    Black_Templars_Models = CustomFactionModels("Black Templar Models")
    Black_Templars_Units = CustomFactionUnits("Black Templar Units")


    Black_Templars_Modifiers.create_new(["SustainedHits_1"], name="Templar Vow")
    Black_Templars_Armours.create_new(toughness=4, save=2, wounds=5, descrip="Black Plate", invuln=4)
    Black_Templars_Weapons.create_new(range=0, attacks=10, skill=2, strength=6, ap=-2, damage=1, descrip="Black Sword (sweep)")
    Black_Templars_Weapons.create_new(range=0, attacks=6, skill=2, strength=8, ap=-3, damage=3, descrip="Black Sword (strike)")
    Black_Templars_Models.create_new(
        weapons=[ Black_Templars_Weapons.get_item("Black Sword (sweep)") ], 
        armour=Black_Templars_Armours.get_item("Black Plate"),
        name="mdl The Emperor's Champion (sweep)",
        pts=75)
    Black_Templars_Units.create_new(
        model_list=[Black_Templars_Models.get_item("mdl The Emperor's Champion (sweep)")], 
        name="The Emperor's Champion (sweep)",
        modifier=Black_Templars_Modifiers.get_item("Templar Vow"))


    # and a unit of Guardsmen
    IG_Modifiers = CustomFactionModifiers("IG Modifiers")
    IG_Weapons = CustomFactionWeapons("IG Weapons")
    IG_Armours = CustomFactionArmours("IG Armours")
    IG_Models = CustomFactionModels("IG Models")
    IG_Units = CustomFactionUnits("IG Units")


    IG_Armours.create_new(toughness=3, save=5, wounds=1, descrip="Flak Armour")
    IG_Armours.create_new(toughness=3, save=5, wounds=2, descrip="Flak Armour (HWT)")

    IG_Weapons.create_new(range=24, attacks=2, skill=4, strength=3, ap=0, damage=1, descrip="Lasgun")
    IG_Weapons.create_new(range=24, attacks=2, skill=4, strength=8, ap=-3, damage=2, descrip="Plasma Gun (Super)")
    IG_Weapons.create_new(range=12, attacks=1, skill=4, strength=8, ap=-3, damage=2, descrip="Plasma Pistol (Super)")
    IG_Weapons.create_new(range=48, attacks=1, skill=4, strength=12, ap=-3, damage=Dice(bias=1), descrip="Lascannon")
    IG_Weapons.create_new(range=0, attacks=1, skill=4, strength=3, ap=0, damage=1, descrip="Close Combat Weapon")
    IG_Weapons.create_new(range=0, attacks=3, skill=4, strength=3, ap=0, damage=1, descrip="Chainsword")
    IG_Weapons.create_new(range=0, attacks=2, skill=4, strength=4, ap=-2, damage=1, descrip="Power Weapon")

    IG_Models.create_new(
        weapons=[ IG_Weapons.get_item("Lasgun"),
                  IG_Weapons.get_item("Close Combat Weapon") ], 
        armour=IG_Armours.get_item("Flak Armour"),
        name="Guardsman w/Lasgun",
        pts=6)
    IG_Models.create_new(
        weapons=[ IG_Weapons.get_item("Plasma Gun (Super)"),
                  IG_Weapons.get_item("Close Combat Weapon") ], 
        armour=IG_Armours.get_item("Flak Armour"),
        name="Guardsman w/Plasma Gun (Super)",
        pts=6)
    IG_Models.create_new(
        weapons=[ IG_Weapons.get_item("Lascannon"),
                  IG_Weapons.get_item("Close Combat Weapon") ], 
        armour=IG_Armours.get_item("Flak Armour (HWT)"),
        name="Heavy Weapons Team w/Lascannon",
        pts=6)
    IG_Models.create_new(
        weapons=[ IG_Weapons.get_item("Plasma Pistol (Super)"),
                  IG_Weapons.get_item("Power Weapon")  ], 
        armour=IG_Armours.get_item("Flak Armour"),
        name="Guardsman Sgt w/Plasma Pistol (Super) Power Weapon",
        pts=6)

    IG_Units.create_new(
        model_list =[ IG_Models.get_item("Guardsman w/Lasgun"), 
                      IG_Models.get_item("Guardsman w/Lasgun"), 
                      IG_Models.get_item("Guardsman w/Lasgun"), 
                      IG_Models.get_item("Guardsman w/Lasgun"), 
                      IG_Models.get_item("Guardsman w/Lasgun"), 
                      IG_Models.get_item("Guardsman w/Plasma Gun (Super)"), 
                      IG_Models.get_item("Guardsman w/Plasma Gun (Super)"), 
                      IG_Models.get_item("Guardsman Sgt w/Plasma Pistol (Super) Power Weapon"), 
                      IG_Models.get_item("Heavy Weapons Team w/Lascannon")],
        name="Infantry Squad Lukas Special",
        modifier=IG_Modifiers.get_item("LethalHits"))

    # and... fight!

    defender = Black_Templars_Units.get_item("The Emperor's Champion (sweep)")
    attacker = IG_Units.get_item("Infantry Squad Lukas Special")

    attacker = update_position(attacker, 0)
    defender = update_position(defender, 0)

    VERY_LIKELY_P_VALUE = 5/6.0
    result = perform_full_analysis(attacker=attacker, defender=defender, count=1000, pvalue=VERY_LIKELY_P_VALUE, description="Emperor's Champion sweeping an Infantry Squad")

    print("==========================\n")
    print(f"{attacker}\n\nVERSUS\n\n{defender}\n")
    print(f"{result}")

# ==============================================================================================================
# ==============================================================================================================
if __name__ == "__main__":
    run_tests()
else:
    pass