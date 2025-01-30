#!/usr/bin/env python


from math_hammer import AStat, DStat, Model, Unit, Dice
from math_hammer import StandardModifiers

TemplarVow = StandardModifiers["LethalHits"]
CrusadersWrath = StandardModifiers["AP_PlusOne"] * StandardModifiers["StrengthPlusOne"]
ChampStack = StandardModifiers["SustainedHits_1"] * StandardModifiers["CriticalHit_5up"] # Champ has Sigismund's Seal and spend 1 CP to give them vow "Accept Any Challenge"


# ==================================================================================== #
#               Charwucters
# ==================================================================================== #
the_emperors_champion_sweep = Model(
    weapons=AStat(Range=12,A=10+1, BS_WS=2, S=6, AP=-2, D=1, description="Black Sword (Sweep) with Sigismund's Seal"),
    defence=DStat(T=4, Sv=2, W=5, Inv=4, description="Black Plate"),
    pts=75, name="The Emperor's Champion (Sweeping)"
)
the_emperors_champion_strike = Model(
    weapons=AStat(Range=12,A=6+1, BS_WS=2, S=8, AP=-3, D=3, description="Black Sword (Strike) with Sigismund's Seal"),
    defence=DStat(T=4, Sv=2, W=5, Inv=4, description="Black Plate"),
    pts=75, name="The Emperor's Champion (Striking)"
)

chaplain_gregor_ironmaw = Model(
    weapons=AStat(Range=12,A=5, BS_WS=2, S=6, AP=-1, D=2, description="Crozius Arcanum with Perdition's Edge") * StandardModifiers["StrengthPlusOne"] * StandardModifiers["AP_PlusOne"] * StandardModifiers["AttacksPlusOne"],
    defence=DStat(T=4, Sv=3, W=4, Inv=4),
    pts=60+15, name="Chaplain Gregor Ironmaw, Orc Slayer"
)

# ==================================================================================== #
#               Redemptor Fists
# ==================================================================================== #

punching_redemptor_dread = Model(
    weapons=AStat(Range=12,A=5, BS_WS=3, S=12, AP=-2, D=3, description="Redemptor Fist"),
    defence=DStat(T=10, Sv=2, W=12),
    pts=210, name="Redemptor Dreadnought"
) * TemplarVow
punching_redemptor_dread_wrath = punching_redemptor_dread * CrusadersWrath 

brutalis_talon_sweep = Model(
    weapons=AStat(Range=12,A=10, BS_WS=3, S=7, AP=-2, D=1, description="Talons (Sweep)") * StandardModifiers["TwinLinked"],
    defence=DStat(T=10, Sv=2, W=12),
    pts=160, name="Brutalis Dreadnought"
) * TemplarVow
brutalis_talon_strike = Model(
    weapons=AStat(Range=12,A=6, BS_WS=3, S=12, AP=-2, D=3, description="Talons (Strike)") * StandardModifiers["TwinLinked"],
    defence=DStat(T=10, Sv=2, W=12),
    pts=160, name="Brutalis Dreadnought"
) * TemplarVow
brutalis_talon_sweep_wrath = brutalis_talon_sweep * CrusadersWrath
brutalis_talon_strike_wrath = brutalis_talon_strike * CrusadersWrath

assets = {'emperors_champ_sweep': the_emperors_champion_sweep,
          'emperors_champ': the_emperors_champion_strike,
          'gregor_ironmaw': chaplain_gregor_ironmaw,
          'melee_redemptor_dread': punching_redemptor_dread,
          }

# ==================================================================================== #
#               Sword Brethern
# ==================================================================================== #

sw_power_weapon = AStat(Range=12,A=4, BS_WS=3, S=5, AP=-2, D=1, description="Power Weapon")
sw_chainsword = AStat(Range=12,A=5, BS_WS=3, S=4, AP=-1, D=1, description="Chainsword")
sw_thammer = AStat(Range=12,A=3, BS_WS=4, S=8, AP=-2, D=2, description="Thunder Hammer") * StandardModifiers["DevestatingWounds"]
sw_lclaws = AStat(Range=12,A=5, BS_WS=3, S=5, AP=-2, D=1, description="Lightning Claws") * StandardModifiers["TwinLinked"]
sw_mastercraft_psword = AStat(Range=12,A=4, BS_WS=2, S=5, AP=-2, D=2, description="Master-crafted Power Weapon")

sw_defence = DStat(T=4, Sv=3, W=3)

sword_brethern = Unit(
    model_list = [
        Model(weapons=sw_power_weapon, defence=sw_defence, pts=150/5, name="Primaris Sword Brother"),
        Model(weapons=sw_power_weapon, defence=sw_defence, pts=150/5, name="Primaris Sword Brother"),
        Model(weapons=sw_thammer, defence=sw_defence, pts=150/5, name="Primaris Sword Brother"),
        Model(weapons=sw_lclaws, defence=sw_defence, pts=150/5, name="Primaris Sword Brother"),
        Model(weapons=sw_mastercraft_psword, defence=sw_defence, pts=150/5, name="Sword Brother Castellan"),
    ], 
    name="Sword Bretheren") * TemplarVow * StandardModifiers["DamagePlusOne"]
sword_brethern_wrath = sword_brethern * CrusadersWrath

# led by The Emperor's Champion
sword_brethern_ld_by_champ = sword_brethern + the_emperors_champion_strike
sword_brethern_ld_by_champ_wrath = sword_brethern_ld_by_champ * CrusadersWrath
sword_brethern_ld_by_champ_stack = sword_brethern_ld_by_champ * ChampStack
sword_brethern_ld_by_champ_wrath_stack = sword_brethern_ld_by_champ_wrath * ChampStack

# led by Gregor Ironmaw, Orc Slayer
sword_brethern_ld_by_gregor = (sword_brethern + chaplain_gregor_ironmaw) * StandardModifiers["PlusOneToWound"]
sword_brethern_ld_by_gregor_wrath = sword_brethern_ld_by_gregor * CrusadersWrath

# ==================================================================================== #
#               Primaris Crusader Squad
# ==================================================================================== #

pric_chainsword = AStat(Range=12,A=5, BS_WS=3, S=4, AP=-1, D=1, description="Chainsword")
pric_powerfist = AStat(Range=12,A=3, BS_WS=3, S=8, AP=-2, D=2, description="Power Fist")
pric_powerweapon = AStat(Range=12,A=3, BS_WS=3, S=5, AP=-2, D=1, description="Power Weapon")
pric_def_neophyte = DStat(T=4, Sv=4, W=2)
pric_def_initiate = DStat(T=4, Sv=3, W=2)

pri_crusaders = Unit([
    Model(weapons=pric_powerweapon, defence=pric_def_initiate, pts=140/10, name="Primaris Sword Brother"),
    Model(weapons=pric_chainsword, defence=pric_def_neophyte, pts=140/10, name="Primais Neophyte"),
    Model(weapons=pric_chainsword, defence=pric_def_neophyte, pts=140/10, name="Primais Neophyte"),
    Model(weapons=pric_chainsword, defence=pric_def_neophyte, pts=140/10, name="Primais Neophyte"),
    Model(weapons=pric_chainsword, defence=pric_def_neophyte, pts=140/10, name="Primais Neophyte"),
    Model(weapons=pric_chainsword, defence=pric_def_initiate, pts=140/10, name="Primaris Initiate"),
    Model(weapons=pric_chainsword, defence=pric_def_initiate, pts=140/10, name="Primaris Initiate"),
    Model(weapons=pric_chainsword, defence=pric_def_initiate, pts=140/10, name="Primaris Initiate"),
    Model(weapons=pric_powerfist, defence=pric_def_initiate, pts=140/10, name="Primaris Initiate"),
    Model(weapons=pric_powerfist, defence=pric_def_initiate, pts=140/10, name="Primaris Initiate"),
]) * TemplarVow

# led by Gregor Ironmaw, Orc Slayer
pri_crusaders_ld_by_gregor = (pri_crusaders + chaplain_gregor_ironmaw) * StandardModifiers["PlusOneToWound"]
pri_crusaders_ld_by_gregor_wrath = pri_crusaders_ld_by_gregor * CrusadersWrath

# led by The Emperor's Champion
pri_crusaders_ld_by_champ = (pri_crusaders + the_emperors_champion_strike)
pri_crusaders_ld_by_champ_wrath = pri_crusaders_ld_by_champ * CrusadersWrath
pri_crusaders_ld_by_champ_stack = pri_crusaders_ld_by_champ * ChampStack
pri_crusaders_ld_by_champ_wrath_stack = pri_crusaders_ld_by_champ_wrath * ChampStack

# ==================================================================================== #
#               Assault Intercessors
# ==================================================================================== #

ai_chainsword = AStat(Range=12,A=4, BS_WS=3, S=4, AP=-1, D=1, description="Astartes Chainsword")
ai_defence = sw_defence 

assault_intercessors = Unit([
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor"),
    Model(weapons=ai_chainsword, defence=ai_defence, pts=75/5, name="Assault Intercessor Sergeant"),
]) * TemplarVow * StandardModifiers["RerollWoundsOne"]

# led by Gregor Ironmaw, Orc Slayer
assault_intercessors_ld_by_gregor = (assault_intercessors + chaplain_gregor_ironmaw) * StandardModifiers["PlusOneToWound"]
assault_intercessors_ld_by_gregor_wrath = assault_intercessors_ld_by_gregor * CrusadersWrath

# led by The Emperor's Champion
assault_intercessors_ld_by_champ = (assault_intercessors + the_emperors_champion_strike)
assault_intercessors_ld_by_champ_wrath = assault_intercessors_ld_by_champ * CrusadersWrath

# ==================================================================================== #
#               Terminator Assault Squad
# ==================================================================================== #
TerminatorArmour = DStat(T=5, Sv=2, W=3, Inv=4, description="Blessed Terminator Armour")
TerminatorArmour_wShield = DStat(T=5, Sv=2, W=4, Inv=4, description="Blessed Terminator Armour with Storm Shield")

assault_termie_with_hammer_shield = Model(
    weapons=AStat(Range=12,A=3, BS_WS=4, S=8, AP=-2, D=2, description="Thunder Hammmer") * StandardModifiers["DevestatingWounds"],
    defence=TerminatorArmour_wShield,
    pts=185/5,
    name="Assault Terminator")
assault_termie_with_lclaws = Model(
    weapons=AStat(Range=12,A=5, BS_WS=3, S=5, AP=-2, D=1) * StandardModifiers["TwinLinked"],
    defence=TerminatorArmour,
    pts=185/5,
    name="Assault Terminator")

assault_termies_0_5 = Unit([
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
]) * TemplarVow
assault_termies_0_5_wrath = assault_termies_0_5 * CrusadersWrath

assault_termies_5_0 = Unit([
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
]) * TemplarVow
assault_termies_5_0_wrath = assault_termies_5_0 * CrusadersWrath

assault_termies_3_2 = Unit([
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
]) * TemplarVow
assault_termies_3_2_wrath = assault_termies_3_2 * CrusadersWrath

assault_termies_2_3 = Unit([
    assault_termie_with_hammer_shield,
    assault_termie_with_hammer_shield,
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
    assault_termie_with_lclaws,
]) * TemplarVow
assault_termies_2_3_wrath = assault_termies_2_3 * CrusadersWrath


# ==================================================================================== #
# ==================================================================================== #
#       Ranged Boyz
# ==================================================================================== #
# ==================================================================================== #
BiologisFireDicipline = StandardModifiers["LethalHits"] * StandardModifiers["SustainedHits_1"] * StandardModifiers["CriticalHit_5up"]
TotalObliteration = StandardModifiers["RerollHits"]  * StandardModifiers["RerollWounds"] * StandardModifiers["Reroll_D6_Damage"]
melta_rifle = AStat(Range=12,A=1, BS_WS=3, S=9, AP=-4, D=Dice())
multi_melta = AStat(Range=12,A=2, BS_WS=4, S=9, AP=-4, D=Dice())
melta_rifle_melta_range = AStat(Range=12,A=1, BS_WS=3, S=9, AP=-4, D=Dice(bias=2))
multi_melta_melta_range = AStat(Range=12,A=2, BS_WS=4, S=9, AP=-4, D=Dice(bias=2))
eradicator_gravis = DStat(T=6, Sv=3, W=3, description="Eradicator Gravis")

eradicators = Unit([
    Model(weapons=melta_rifle, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=melta_rifle, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=multi_melta, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
])
eradicators_at_vehicle = eradicators * TotalObliteration
full_squad_eradicators = Unit([
    Model(weapons=melta_rifle, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=melta_rifle, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=melta_rifle, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=melta_rifle, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=multi_melta, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
    Model(weapons=multi_melta, defence=eradicator_gravis, pts=95/3, name="Eradicator"),
])
full_squad_eradicators_at_vehicle = full_squad_eradicators * TotalObliteration
# Eradicators + Apothecary Biologis with Fire Discipline = A lot of hurt
full_eradicators_firedis_stack = full_squad_eradicators * BiologisFireDicipline
full_eradicators_firedis_stack_at_vehicle = full_squad_eradicators_at_vehicle * BiologisFireDicipline

blastadd = 0
ven_brother_grammituis = Model(
    weapons=[
        AStat(Range=12,A=Dice(), BS_WS=3, S=5, AP=-1, D=1, description="Heavy Flamer") * StandardModifiers["Torrent"],
        AStat(Range=12,A=12, BS_WS=3, S=6, AP=0, D=1, description="Heavy Onslaught Gatling Cannon") * StandardModifiers["DevestatingWounds"],
        AStat(Range=12,A=Dice(bias=blastadd), BS_WS=3, S=4, AP=0, D=1, description="Twin Fragstorm Grenade Launcher") * StandardModifiers["TwinLinked"],
    ],
    defence=DStat(T=10, Sv=2, W=12),
    pts=210, name="Venerable Brother Grammituis"
)

redemptor_dread = Model(
    weapons=[
        AStat(Range=12,A=Dice(), BS_WS=3, S=5, AP=-1, D=1, description="Heavy Flamer") * StandardModifiers["Torrent"],
        AStat(Range=12,A=Dice(bias=blastadd), BS_WS=3, S=4, AP=0, D=1, description="Twin Fragstorm Grenade Launcher") * StandardModifiers["TwinLinked"],
        AStat(Range=12,A=Dice(bias=1+blastadd), BS_WS=3, S=9, AP=-4, D=3, description="Macro Plasma Incinerator"),
        AStat(Range=12,A=Dice(sides=3), BS_WS=3, S=8, AP=-1, D=2, description="Icarus Rocket Pod"),
    ],
    defence=DStat(T=10, Sv=2, W=12),
    pts=210, name="Redemptor Dreadnought"
)




