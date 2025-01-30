#!/usr/bin/env python

from math_hammer import AStat, DStat, Model, Unit, Dice
from math_hammer import StandardModifiers

SustainedHits_1 = StandardModifiers["SustainedHits_1"]
DevestatingWounds = StandardModifiers["DevestatingWounds"]
TwinLinked = StandardModifiers["TwinLinked"]
LethalHits = StandardModifiers["LethalHits"]

# ==================================================================================== #
#       Elf assests
# ==================================================================================== #
dire_avenger_model = Model(
    weapons=AStat(Range=18,A=3, BS_WS=3, S=4, AP=-1, D=1, description="Dire Avenger") * LethalHits,
    defence=DStat(T=3, Sv=4, W=3, Inv=4),
    pts=190/5, name="Dire Avenger"
)

dire_avenger_squad = Unit([
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    dire_avenger_model,
    ])

wraithguard_model_cannon = Model(
    weapons=AStat(Range=12,A=1, BS_WS=4, S=14, AP=-4, D=Dice(), description="Wraithcannon") * DevestatingWounds,
    defence=DStat(T=7, Sv=2, W=3),
    pts=190/5, name="Wraithguard with Cannon"
)
wraithguard_model_dscythe = Model(
    weapons=AStat(Range=12,A=Dice(), BS_WS=4, S=10, AP=-4, D=1, description="D-scythe") * DevestatingWounds,
    defence=DStat(T=7, Sv=2, W=3),
    pts=190/5, name="Wraithguard with Scythe"
)
wraithguard_cannon = Unit([wraithguard_model_cannon for _ in range(0,10)])
wraithguard_scythe = Unit([wraithguard_model_dscythe for _ in range(0,10)])

waveserpent = Model(
    weapons=[
        AStat(Range=12,A=1, BS_WS=3, S=12, AP=-3, D=Dice(bias=2), description="Twin Bright Lance") * TwinLinked,
        AStat(Range=12,A=3, BS_WS=3, S=6, AP=-1, D=2, description="Shuriken Cannon") * SustainedHits_1,
    ],
    defence=DStat(T=9, Sv=3, W=13, Inv=5),
    pts=120, name="Wave Serpent"
)