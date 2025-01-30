#!/usr/bin/env python

import dill as pickle
import matplotlib.pyplot as plt
import argparse
import copy

from math_hammer import perform_full_analysis, update_position

import black_templars
import aeldari
import imperial_guard

DEFAULT_COUNT = 1000

if __name__ == "__main__":
    # ==================================================================================== #
    # ==================================================================================== #
    #       Melee Boyz
    # ==================================================================================== #
    # ==================================================================================== #
    melee_boyz = {
        'chaplain_gregor_ironmaw': black_templars.chaplain_gregor_ironmaw * black_templars.TemplarVow,
        'the_emperors_champion_strike': black_templars.the_emperors_champion_strike * black_templars.TemplarVow,
        'the_emperors_champion_sweep': black_templars.the_emperors_champion_sweep * black_templars.TemplarVow,

        'punching_redemptor_dread': copy.deepcopy(black_templars.punching_redemptor_dread),
        'punching_redemptor_dread_wrath': copy.deepcopy(black_templars.punching_redemptor_dread_wrath),
        'brutalis_talon_sweep': copy.deepcopy(black_templars.brutalis_talon_sweep),
        'brutalis_talon_sweep_wrath': copy.deepcopy(black_templars.brutalis_talon_sweep_wrath),
        'brutalis_talon_strike': copy.deepcopy(black_templars.brutalis_talon_strike),
        'brutalis_talon_strike_wrath': copy.deepcopy(black_templars.brutalis_talon_strike_wrath),

        'sword_brethern': copy.deepcopy(black_templars.sword_brethern),
        'sword_brethern_wrath': copy.deepcopy(black_templars.sword_brethern_wrath),
        'sword_brethern_ld_by_gregor (0CP)': copy.deepcopy(black_templars.sword_brethern_ld_by_gregor),
        'sword_brethern_ld_by_gregor_wrath (1CP)': copy.deepcopy(black_templars.sword_brethern_ld_by_gregor_wrath),
        'sword_brethern_ld_by_champ (0CP)': copy.deepcopy(black_templars.sword_brethern_ld_by_champ),
        'sword_brethern_ld_by_champ_wrath (1CP)': copy.deepcopy(black_templars.sword_brethern_ld_by_champ_wrath),
        'sword_brethern_ld_by_champ_stack (1CP)': copy.deepcopy(black_templars.sword_brethern_ld_by_champ_stack),
        'sword_brethern_ld_by_champ_wrath_stack (2CP)': copy.deepcopy(black_templars.sword_brethern_ld_by_champ_wrath_stack),

        'pri_crusaders': copy.deepcopy(black_templars.pri_crusaders),
        'pri_crusaders_ld_by_gregor': copy.deepcopy(black_templars.pri_crusaders_ld_by_gregor),
        'pri_crusaders_ld_by_gregor_wrath': copy.deepcopy(black_templars.pri_crusaders_ld_by_gregor_wrath),
        'pri_crusaders_ld_by_champ': copy.deepcopy(black_templars.pri_crusaders_ld_by_champ),
        'pri_crusaders_ld_by_champ_wrath': copy.deepcopy(black_templars.pri_crusaders_ld_by_champ_wrath),
        'pri_crusaders_ld_by_champ_stack': copy.deepcopy(black_templars.pri_crusaders_ld_by_champ_stack),
        'pri_crusaders_ld_by_champ_wrath_stack': copy.deepcopy(black_templars.pri_crusaders_ld_by_champ_wrath_stack),

        'assault_intercessors': copy.deepcopy(black_templars.assault_intercessors),
        'assault_intercessors_ld_by_gregor': copy.deepcopy(black_templars.assault_intercessors_ld_by_gregor),
        'assault_intercessors_ld_by_gregor_wrath': copy.deepcopy(black_templars.assault_intercessors_ld_by_gregor_wrath),
        'assault_intercessors_ld_by_champ': copy.deepcopy(black_templars.assault_intercessors_ld_by_champ),
        'assault_intercessors_ld_by_champ_wrath': copy.deepcopy(black_templars.assault_intercessors_ld_by_champ_wrath),

        'assault_termies_0_5': copy.deepcopy(black_templars.assault_termies_0_5),
        'assault_termies_0_5_wrath': copy.deepcopy(black_templars.assault_termies_0_5_wrath),
        'assault_termies_5_0': copy.deepcopy(black_templars.assault_termies_5_0),
        'assault_termies_5_0_wrath': copy.deepcopy(black_templars.assault_termies_5_0_wrath),
        'assault_termies_3_2': copy.deepcopy(black_templars.assault_termies_3_2),
        'assault_termies_3_2_wrath': copy.deepcopy(black_templars.assault_termies_3_2_wrath),
        'assault_termies_2_3': copy.deepcopy(black_templars.assault_termies_2_3),
        'assault_termies_2_3_wrath': copy.deepcopy(black_templars.assault_termies_2_3_wrath),
    }

    # ==================================================================================== #
    # ==================================================================================== #
    #       Ranged Boyz
    # ==================================================================================== #
    # ==================================================================================== #
    ranged_boyz = {
        'eradicators': copy.deepcopy(black_templars.eradicators),
        'eradicators_at_vehicle': copy.deepcopy(black_templars.eradicators_at_vehicle),
        'full_squad_eradicators': copy.deepcopy(black_templars.full_squad_eradicators),
        'full_squad_eradicators_at_vehicle': copy.deepcopy(black_templars.full_squad_eradicators_at_vehicle),
        'redemptor_dread': copy.deepcopy(black_templars.redemptor_dread),
        'ven_brother_grammituis': copy.deepcopy(black_templars.ven_brother_grammituis),
        'full_eradicators_firedis_stack': copy.deepcopy(black_templars.full_eradicators_firedis_stack),
        'full_eradicators_firedis_stack_at_vehicle': copy.deepcopy(black_templars.full_eradicators_firedis_stack_at_vehicle),
        'leman_russ': copy.deepcopy(imperial_guard.leman_russ_tank),
        'wraithguard_cannon': copy.deepcopy(aeldari.wraithguard_cannon),
        'wraithguard_scythe': copy.deepcopy(aeldari.wraithguard_scythe),
        'chimera': copy.deepcopy(imperial_guard.chimera),
        'guardsmen': copy.deepcopy(imperial_guard.guardsmen),
    }

    # ==================================================================================== #
    #       Statistical Reports
    # ==================================================================================== #

    DEFENDER_OPTIONS = {
        'chimera': copy.deepcopy(imperial_guard.chimera),
        'leman_russ': copy.deepcopy(imperial_guard.leman_russ_tank),
        'wraithguard_cannon': copy.deepcopy(aeldari.wraithguard_cannon),
        'wraithguard_scythe': copy.deepcopy(aeldari.wraithguard_scythe),
        'waveserpent': copy.deepcopy(aeldari.waveserpent),
        'guardsmen': copy.deepcopy(imperial_guard.guardsmen),
        'eradicators': copy.deepcopy(black_templars.eradicators),
        'redemptor_dread': copy.deepcopy(black_templars.redemptor_dread),
        'ven_brother_grammituis': copy.deepcopy(black_templars.ven_brother_grammituis),
        'space_marine': copy.deepcopy(black_templars.assault_intercessors),
    }
    ATTACKER_OPTIONS = {
        'ranged': ranged_boyz,
        'melee': melee_boyz,
        'eldar': {"dire_avenger": copy.deepcopy(aeldari.dire_avenger_squad)},
    }
    
    par = argparse.ArgumentParser(description='Warhammer 40k 10th Ed. Math Hammer')
    par.add_argument('ATTACKER', type=str, choices=ATTACKER_OPTIONS.keys(), help='Attacker group to run in simulation.')
    par.add_argument('DEFENDER', type=str, choices=DEFENDER_OPTIONS.keys(), help='Defender to run in simulation.')
    par.add_argument('--count', type=str, help=f'Number of sequences to run.  Default is {DEFAULT_COUNT}.', default=DEFAULT_COUNT)
    par.add_argument('--verylikely', type=float, help='Threshold, on range [0,1], that is considered "Very Likely". Default is 5/6.', default=5/6.0)

    args = par.parse_args()

    the_list = ATTACKER_OPTIONS[args.ATTACKER]
    the_target = DEFENDER_OPTIONS[args.DEFENDER]

    h = plt.figure(1)

    print("Working...")


    models_removed = {}
    damage_done = {}
    for k in the_list:
        attacker = the_list[k]
        attacker = update_position(attacker, 0)
        the_target = update_position(the_target, 2)
        result = perform_full_analysis(attacker=attacker, defender=the_target, count=args.count, pvalue=args.verylikely, description=k)
        models_removed[k] = result.very_likely_models_removed
        damage_done[k] = result.very_likely_damage_output
        plt.plot(result.damage_cdf)


    def print_report(modl_dict, header):
        print(header)
        for k in modl_dict:
            print(f"{int(modl_dict[k]): 3d} : {k}")

    print_report(models_removed, f"{int(args.verylikely*100)}% chance M models removed:")
    print_report(damage_done, f"{int(args.verylikely*100)}% chance N damage done:")

    plt.legend(the_list.keys())
    plt.title(f"versus {the_target}")
    plt.show()