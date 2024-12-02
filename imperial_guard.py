#!/usr/bin/env python

from math_hammer import AStat, DStat, Model, Unit, Dice
from math_hammer import Torrent, SustainedHits_1, PlusOneToHit

# ==================================================================================== #
#       Imperial Guard assests
# ==================================================================================== #
leman_russ_tank = Model(
    weapons=[
        AStat(A=Dice(bias=3), BS_WS=4, S=10, AP=-1, D=3, description="Battle Cannon"),
        AStat(A=Dice(sides=3), BS_WS=4, S=8, AP=-3, D=2, description="Plasma Cannon (supercharged)"),
        AStat(A=Dice(sides=3), BS_WS=4, S=8, AP=-3, D=2, description="Plasma Cannon (supercharged)"),
        AStat(A=3, BS_WS=4, S=5, AP=-1, D=2, description="Heavy Bolter"),
        AStat(A=1, BS_WS=4, S=14, AP=-3, D=Dice(), description="Hunter-killer Missle"),
    ], 
    defence=DStat(T=11, Sv=2, W=13), 
    pts=170, name="Leman Russ Battle Tank"
)
chimera = Model(
    weapons=[
        AStat(A=Dice(), BS_WS=4, S=5, AP=-1, D=1, description="Chimera Heavy Flamer") * Torrent,
        AStat(A=3, BS_WS=4, S=5, AP=-1, D=2, description="Heavy Bolter") * SustainedHits_1,
        AStat(A=3+3, BS_WS=4, S=4, AP=0, D=1, description="Heavy Stubber (rapid firing)"),
        AStat(A=6+6, BS_WS=4, S=3, AP=0, D=1, description="Lasgun Array (rapid firing)"),
        AStat(A=1, BS_WS=4, S=14, AP=-3, D=Dice(), description="Hunter-killer Missle"),
    ],
    defence=DStat(T=9, Sv=3, W=11),
    pts=70, name="Chimera"
)

lasgun = AStat(A=2, BS_WS=4, S=3, AP=0, D=1, description="lasgun, King of Weapons (rapid firing)" )
laspistol = AStat(A=1, BS_WS=4, S=3, AP=0, D=1, description="laspistol" )
autocannon = AStat(A=2, BS_WS=4, S=3, AP=0, D=1, description="Autocannon" )
plasmagun = AStat(A=2, BS_WS=4, S=8, AP=-3, D=2, description="Plasma Gun (rapid firing, supercharged)" )
guardsmen_model = Model(weapons=lasgun, defence=DStat(T=3, Sv=5, W=1), pts=60/10, name="Guardsman")
guardsmen_plasma_model = Model(weapons=plasmagun, defence=DStat(T=3, Sv=5, W=1), pts=60/10, name="Guardsman")
guardsmen_sgt_model = Model(weapons=laspistol, defence=DStat(T=3, Sv=5, W=1), pts=60/10, name="Guardsman")
guardsmen_hvy_autcannon_model = Model(weapons=autocannon, defence=DStat(T=3, Sv=5, W=2), pts=2*60/10, name="Heavy Weapons Team")
guardsmen = Unit([
    guardsmen_sgt_model,
    guardsmen_hvy_autcannon_model, 
    guardsmen_plasma_model,
    guardsmen_plasma_model,
    guardsmen_model,
    guardsmen_model,
    guardsmen_model,
    guardsmen_model,
    guardsmen_model,
]) * PlusOneToHit


assets = {'leman_russ': leman_russ_tank,
          'chimera': chimera,
          'infantry_squad': guardsmen
          }