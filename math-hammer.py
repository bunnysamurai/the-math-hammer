#!/usr/bin/env python

import random
import numpy as np
import numbers
import copy
import matplotlib.pyplot as plt
import argparse

DEFAULT_COUNT = 1000
# =========================================================================== #
## more complicated stuff, or faction specific, or USR specific
def modifier_critical_case(sequence, thing_to_do):
    def functor(state):
        if state.roll[sequence].value >= state.char['critical'+sequence]:
            state = thing_to_do(state)
        return state
    return functor

def modifier_sustained_hits(X):
    def functor(state):
        # when a 6 is rolled, we add X more hits to the pool
        for _ in range(0,X):
            state.pool['hit'].append(Dice())
        return state
    return modifier_critical_case('hit', functor)
def modifier_lethal_hits():
    def functor(state):
        # when a 6 is rolled, it wounds automatically
        # normally, a 6 is a success, and so the 'hit' pool will go up by one
        # here, we will subtract one from the 'hit' pool and instead increment the 'wound' pool by 1
        state.scratch['break_mod_loop'] = True
        state.pool['wound'].append(Dice())
        return state
    return modifier_critical_case('hit', functor)
def modifier_devastating_wounds():
    def functor(state):
        # when a 6 is rolled, skip the save
        # normally, a 6 is a success, and so the 'save' pool will go up by one
        # here, we will subtract one from the 'save' pool and add 'damage' to the 'damage' pool
        damage_to_add = 0
        try:
            # damage might be callable, this will trigger use of the roll
            damage_to_add = state.char['damage'](state.roll['damage'].value)
        except Exception as e:
            damage_to_add = state.char['damage']
        state.scratch['break_mod_loop'] = True
        for _ in range(0, damage_to_add):
            state.pool['damage'].append(Dice())
        return state
    return modifier_critical_case('wound', functor)

## basic stuff
def modifier_characteristic_subtract_one(sequence):
    def functor(state):
        if sequence == 'armourpen':
            # handle armour pen, which is a special snowflake
            state.char[sequence] -= 1
        else:
            state.char[sequence] -= 1
            state.char[sequence] = max(state.char[sequence], 1)
        return state
    return functor
def modifier_characteristic_add_one(sequence):
    def functor(state):
        state.char[sequence] += 1
        return state
    return functor
def modifier_roll_subtract_one(sequence):
    def functor(state):
        state.roll[sequence].value -= 1
        state.roll[sequence].value = max(state.roll[sequence].value, 1)
        return state
    return functor
def modifier_roll_add_one(sequence):
    def functor(state):
        state.roll[sequence].value += 1
        state.roll[sequence].value = min(state.roll[sequence].value, 6)
        return state
    return functor
def modifier_reroll_ones(sequence):
    def functor(state):
        if state.roll[sequence].value == 1 and state.roll[sequence].roll_count < 2:
            source = state.determine_pool_source(sequence)
            state.pool[source].append(state.roll[sequence])
            state.scratch['break_mod_loop'] = True
        return state
    return functor
def modifier_reroll_fails(sequence):
    def functor(state):
        if state.roll[sequence].value < state.determine_threshold(sequence) and state.roll[sequence].roll_count < 2:
            source = state.determine_pool_source(sequence)
            state.pool[source].append(state.roll[sequence])
            state.scratch['break_mod_loop'] = True
        return state
    return functor
def modifier_reroll_successes(sequence):
    def functor(state):
        if state.roll[sequence].value >= state.determine_threshold(sequence) and state.roll[sequence].roll_count < 2:
            source = state.determine_pool_source(sequence)
            state.pool[source].append(state.roll[sequence])
            state.scratch['break_mod_loop'] = True
        return state
    return functor
def modifier_reroll_variable_stat(sequence, sides):
    expected = np.sum(list(range(1,sides+1))) / sides
    norm_factor = sides / 6
    def functor(state):
        if np.ceil(state.roll[sequence].value * norm_factor) < expected and state.roll[sequence].roll_count < 2:
            source = state.determine_pool_source(sequence)
            state.pool[source].append(state.roll[sequence])
            state.scratch['break_mod_loop'] = True
        return state
    return functor

# =========================================================================== #
class Dice():
    def __init__(self, sides=6, fixed=None, bias=0):
        self.roll_count = 0
        self.sides = sides
        self.fixed_value = fixed
        self.value = None if self.fixed_value is None else self.fixed_value
        self.bias = bias
    
    def roll(self):
        self.roll_count += 1
        if self.fixed_value is None:
            self.value = random.randint(1,self.sides) + self.bias
        return self

def determine_wound_roll(strength, toughness):
    if strength == toughness:
        return 4
    if strength >= toughness * 2:
        return 2
    if strength > toughness:
        return 3
    if strength * 2 < toughness:
        return 6
    if strength < toughness:
        return 5

def determine_save(save, invuln, armourpen):
    result = max(save - armourpen, 0)
    if invuln is not None and result > invuln: # a 4++ is better than a 5+
        return invuln
    return result

class AttackSequenceState():
    def __init__(self):
        self.scratch = {} # for, you know, whatever
        # self.pool = {'attacks': [], 'hit': [], 'wound': [], 'save': [], 'damage': [], 'fnp': []} # this works
        # self.roll = {'hit': None, 'wound': None, 'save': None, 'damage': None, 'fnp': None} # this works
        # Pools are lists of Dice.  These dice move to the next pool when success is marked
        self.pool = {'preamble': [], 'attacks': [], 'hit': [], 'wound': [], 'save': [], 'damage': [], 'fnp': []}
        # Roll is the current dice being rolled.
        self.roll = {'attacks': None, 'hit': None, 'wound': None, 'save': None, 'damage': None, 'fnp': None}
        # attacker and defender fill in these when asked
        self.char = {
            'attacks': None, 
            'skill': None, 
            'strength': None, 
            'toughness': None, 
            'armourpen': None, 
            'invuln': None,
            'sv': None, 
            'damage': None, 
            'fnp': None,
            'criticalhit': 6,
            'criticalwound': 6}
        # game system will assign char to threshold when making the roll and determining success
        self.threshold = {
            'attacks': None, 
            'skill': None, 
            'strength': None, 
            'toughness': None, 
            'armourpen': None, 
            'invuln': None,
            'sv': None, 
            'save': None, 
            'damage': None, 
            'fnp': None}

    def __str__(self):
        result = f"pool: {self.pool}\n" + f"roll: {self.roll}\n" + f"char: {self.char}\n" + f"threshold: {self.threshold}"
        return result

    def resolve(self):
        return max(0, len(self.pool['fnp']))

    def determine_threshold(self, sequence):
        if sequence == 'hit':
            return self._determine_skill_threshold()
        if sequence == 'wound':
            return self._determine_wound_threshold()
        if sequence == 'save':
            return self._determine_save_threshold()
        if sequence == 'fnp':
            return self._determine_fnp_threshold()
    
    def _determine_skill_threshold(self):
        return self.char['skill']

    def _determine_fnp_threshold(self):
        return self.char['fnp']

    def _determine_wound_threshold(self):
        T = self.threshold['toughness']
        S = self.threshold['strength']
        succ = determine_wound_roll(S, T)
        return succ

    def _determine_save_threshold(self):
        return determine_save(self.threshold['sv'], self.threshold['invuln'], self.threshold['armourpen'])

    def determine_pool_source(self, sequence):
        # self.pool = {'preamble': [], 'attacks': [], 'hit': [], 'wound': [], 'save': [], 'damage': [], 'fnp': []}
        # self.roll = {'attacks': None, 'hit': None, 'wound': None, 'save': None, 'damage': None, 'fnp': None}
        if sequence == 'attacks':
            return 'preamble'
        if sequence == 'hit':
            return 'attacks'
        if sequence == 'wound':
            return 'hit'
        if sequence == 'save':
            return 'wound'
        if sequence == 'damage':
            return 'save'
        if sequence == 'fnp':
            return 'damage'

def identity():
    return lambda x: x

def create_standard_attack_modifier_sequence():
    def clamp_the_roll_modifier(unmodified, modified):
        # check the modified roll, as it is limited to +1/-1
        # unmod + value = modified, therefore
        #   value = modified - unmod
        modifier_value = modified - unmodified
        # check whether it's 
        modifier_value = np.clip(modifier_value, a_min=-1, a_max=1)
        return unmodified + modifier_value

    def intialize_handler(state):
        # Pools are lists of Dice.  These dice move to the next pool when success is marked

        # all that's needed is to initalize the number of attacks, which may or maynot be determined by a roll of the dice
        # this is a bit of a hack, but for static attack characteristics, we'll create a "fixed" dice.  This plugs into the existing framework more nicely (debatably).

        # state.char['attacks'] can only be 1 of 3 possibilities:
        #   int
        #   Dice
        #   [Dice,] 
        # check if state.char['attacks'] is list, if so, add it directly
        # check if state.char is a Dice.  if so, add it to the list
        # if it is an int, create a dice with the value fixed to that int
        try_again = False
        try: # it's a [Dice,]
            for item in state.char['attacks']:
                state.pool['preamble'].append(item)
        except Exception as e:
            try_again = True
        
        if try_again is True:
            try_again = False
            try: # it's a Dice
                if state.char['attacks'].sides > 0: # i.e. is rollable
                    state.pool['preamble'].append(state.char['attacks'])
            except Exception as e:
                try_again = True
        
        if try_again is True:
            # okay, it must be an int
            # if not, another handler can take exception
            state.pool['preamble'].append(Dice(sides=6, fixed=state.char['attacks']))
        return state
    def resolve_attack_pool(state):
        # the preamble determined how many dice, all we need to do is pass the value straight in
        attacks_to_add = 0
        try:
            # attacks might be callable, this will trigger use of the roll
            attacks_to_add = state.char['attacks'](state.roll['attacks'].value)
        except Exception as e:
            attacks_to_add += state.roll['attacks'].value
        for _ in range(0, attacks_to_add):
            state.pool['attacks'].append(Dice())
        return state
    def resolve_hit_pool(state):
        CR = state.char['criticalhit']
        clamped_roll = clamp_the_roll_modifier(unmodified=state.scratch['unmodified_roll'].value, modified=state.roll['hit'].value)
        if state.scratch['unmodified_roll'].value == 1:
            return state
        if state.scratch['unmodified_roll'].value >= CR or clamped_roll >= state.determine_threshold('hit'):
            state.pool['hit'].append(Dice())
        return state
    def assign_strength(state):
        state.threshold['strength'] = state.char['strength']
        return state
    def assign_toughness(state):
        state.threshold['toughness'] = state.char['toughness']
        return state
    def resolve_wound_pool(state):
        CR = state.char['criticalwound']
        if state.scratch['unmodified_roll'].value == 1:
            return state
        clamped_roll = clamp_the_roll_modifier(unmodified=state.scratch['unmodified_roll'].value, modified=state.roll['wound'].value)
        if state.scratch['unmodified_roll'].value >= CR or clamped_roll >= state.determine_threshold('wound'):
            state.pool['wound'].append(Dice())
        return state
    def assign_armourpen(state):
        state.threshold['armourpen'] = state.char['armourpen']
        return state
    def assign_sv(state):
        state.threshold['sv'] = state.char['sv']
        return state
    def assign_invuln(state):
        state.threshold['invuln'] = state.char['invuln']
        return state
    def resolve_save_pool(state):
        if state.scratch['unmodified_roll'].value == 1 or state.roll['save'].value < state.determine_threshold('save'):
            state.pool['save'].append(Dice())
        return state
    def resolve_damage_pool(state):
        damage_to_add = 0
        try:
            # damage might be callable, this will trigger use of the roll
            damage_to_add = state.char['damage'](state.roll['damage'].value)
        except Exception as e:
            damage_to_add += state.char['damage']
        for _ in range(0, damage_to_add):
            state.pool['damage'].append(Dice())
        return state
    def resolve_fnp_pool(state):
        try:
            # need to check the modified roll first, as we rely on EAFP because THAT'S THE PYTHON WAY!!
            roll_status = state.roll['fnp'].value < state.determine_threshold('fnp') 
            if state.scratch['unmodified_roll'].value == 1:
                return state
            if roll_status is True:
                state.pool['fnp'].append(Dice())
        except Exception as e:
            state.pool['fnp'].append(Dice())
        return state

    # the keys are, basically, the steps in the state machine.
    # the values are the last action to take
    post = {'preamble': [intialize_handler],
            'attacks': [resolve_attack_pool], 
            'hit': [resolve_hit_pool],
            'strength': [assign_strength],
            'toughness': [assign_toughness],
            'wound': [resolve_wound_pool], 
            'armourpen': [assign_armourpen],
            'sv': [assign_sv],
            'invuln': [assign_invuln],
            'save': [resolve_save_pool],
            'damage': [resolve_damage_pool],
            'fnp': [resolve_fnp_pool] }
    return post 

def assign_char(phase_str, value):
    def fun(state):
        if state.char[phase_str] is None:
            state.char[phase_str] = value
        else:
            state.char[phase_str] += value
        return state
    return fun

class AStat():
    def __init__(self, PTS, A, BS_WS, S, AP, D, name=None):
        self.attacks = A
        self.skill = BS_WS
        self.strength = S
        self.armourpen = AP
        self.damage = D
        self.name = name if name is not None else "NA"
        self.points = PTS

        # we only interact with the .char field
        self.modifiers = {'preamble': [assign_char('attacks', self.attacks), assign_char('damage', self.damage), assign_char('strength', self.strength), assign_char('armourpen', self.armourpen), assign_char('skill', self.skill)],
                          'attacks': [identity()],
                          'hit': [identity()], 
                          'strength': [identity()],
                          'toughness': [identity()],
                          'wound': [identity()], 
                          'armourpen': [identity()],
                          'invuln': [identity()], 
                          'sv': [identity()], 
                          'save': [identity()], 
                          'damage': [identity()],
                          'fnp': [identity()]}

    def __mul__(self, other):
        result = copy.deepcopy(self)
        result.modifiers[other.seq].append(other.func)
        return result
    
class DStat():
    def __init__(self, PTS, T, Sv, W, Inv=None, FNP=None, name=None):
        self.toughness = T
        self.save = Sv
        self.wounds = W
        self.invuln = Inv
        self.feelnopain = FNP
        self.name = name if name is not None else "NA"
        self.points = PTS

        self.the_d6 = Dice(sides=6)

        # we only interact with the .char field
        self.modifiers = {'preamble': [assign_char('toughness', self.toughness), assign_char('invuln', self.invuln), assign_char('sv', self.save), assign_char('fnp', self.feelnopain)],
                          'attacks': [identity()], 
                          'hit': [identity()], 
                          'strength': [identity()],
                          'toughness': [identity()],
                          'wound': [identity()], 
                          'armourpen': [identity()],
                          'invuln': [identity()], 
                          'sv': [identity()], 
                          'save': [identity()],
                          'damage': [identity()],
                          'fnp': [identity()]}

    def __str__(self):
        result = f"{self.name} (T:{self.toughness} Sv:{self.save}+"
        if self.invuln is not None:
            result += f"|{self.invuln}++"
        if self.feelnopain is not None:
            result += f"|{self.feelnopain}+++"
        result += f" W:{self.wounds})"
        return result


    def __mul__(self, other):
        result = copy.deepcopy(self)
        result.modifiers[other.seq].append(other.func)
        return result

    def __sub__(self, attacker):
        if type(attacker) is not AStat:
            raise ValueError("RHS must be an attacking statistic")

        # resolve standard modifiers
        state = AttackSequenceState()
        state.scratch['break_mod_loop'] = False
        postamble = create_standard_attack_modifier_sequence()
        for sequence in postamble.keys():
            if sequence in state.roll:
                pool_source = state.determine_pool_source(sequence)
                while len(state.pool[pool_source]) > 0:
                    # remove the dice from the pool, roll it, then apply any applicable modifiers
                    the_dice = state.pool[pool_source][0]
                    state.pool[pool_source] = state.pool[pool_source][1:]
                    state.scratch['unmodified_roll'] = the_dice.roll()
                    state.roll[sequence] = copy.deepcopy(state.scratch['unmodified_roll'])
                    for modifier in self.modifiers[sequence] + attacker.modifiers[sequence] + postamble[sequence]:
                        state = modifier(state)
                        if state.scratch['break_mod_loop'] is True:
                            state.scratch['break_mod_loop'] = False
                            break
            else:
                for modifier in self.modifiers[sequence] + attacker.modifiers[sequence] + postamble[sequence]:
                    state = modifier(state)
        return state.resolve()
        

class Modifier():
    def __init__(self, sequence, functor):
        self.seq = sequence
        self.func = functor 
    
RerollWounds = Modifier(sequence='wound', functor=modifier_reroll_fails('wound'))
RerollWoundsOne = Modifier(sequence='wound', functor=modifier_reroll_ones('wound'))
TwinLinked = RerollWounds
RerollHits = Modifier(sequence='hit', functor=modifier_reroll_fails('hit'))
RerollHitsOne = Modifier(sequence='hit', functor=modifier_reroll_ones('hit'))
Reroll_D6_Damage = Modifier(sequence='damage', functor=modifier_reroll_variable_stat(sequence='damage', sides=6))
Reroll_D3_Damage = Modifier(sequence='damage', functor=modifier_reroll_variable_stat(sequence='damage', sides=3))
PlusOneToWound = Modifier(sequence='wound', functor=modifier_roll_add_one('wound'))
PlusOneToHit = Modifier(sequence='hit', functor=modifier_roll_add_one('hit'))
LethalHits = Modifier(sequence='hit', functor=modifier_lethal_hits())
SustainedHits_1 = Modifier(sequence='hit', functor=modifier_sustained_hits(X=1))
DevestatingWounds = Modifier(sequence='wound', functor=modifier_devastating_wounds())
StrengthPlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_add_one('strength'))
AP_PlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_subtract_one('armourpen'))
AttacksPlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_add_one('attacks'))
DamagePlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_add_one('damage'))

def d6_plus(X):
    return lambda d6roll: d6roll + X
def d3_plus(X):
    return lambda d6roll: (d6roll+1)//2 + X

# =================================================================================== #
def mean_loop(attacker, defender, count):
    N = count
    acc = np.zeros((N,)) 
    if type(attacker) is list:
        for att in attacker:
            tmp = np.zeros((N,)) 
            for ii in range(0, N):
                tmp[ii] = defender - att
            acc += tmp
    else:
        for ii in range(0, N):
            acc[ii] = defender - attacker
    # return mean
    return np.mean(acc)

def phist_loop(attacker, defender, count):
    N = count
    acc = np.zeros((N,)) 
    if type(attacker) is list:
        for att in attacker:
            tmp = np.zeros((N,)) 
            for ii in range(0, N):
                tmp[ii] = defender - att
            acc += tmp
    else:
        for ii in range(0, N):
            acc[ii] = defender - attacker
        # create histogram
    phist = np.zeros((int(np.max(acc))+1,))
    for ii in range(0,len(phist)):
        phist[ii] = len(acc[acc == ii]) / len(acc)

    phist = phist[::-1]
    phist = np.cumsum(phist)
    phist = phist[::-1]
    return phist

def force_strictly_monotonic(xdata, ydata):
    # just along the y-axis
    # we'll just assume x is already stricly monotonic
    # also, the length of xdata and ydata are the same
    assert len(xdata) == len(ydata)

    index_list = [0]
    for ii in range(1, len(ydata)-1):
        if ydata[ii] != ydata[ii+1]:
            index_list.append(ii)
    index_list.append(len(ydata)-1)
    return xdata[index_list], ydata[index_list]

def mod_squad(squad_list, mod):
    tmp = copy.deepcopy([x * mod for x in squad_list])
    return tmp

def add_unit(squad, unit):
    tmp = copy.deepcopy(squad)
    tmp.append(unit)
    return tmp

# =================================================================================== #
#       TESTS ONLY
# =================================================================================== #
def run_test():
    # run system tests
    ATTACKS = 1
    SKILL = 4
    STRENGTH = 4
    AP = 0
    DAMAGE = 1
    VARDAMAGE = d3_plus(0)
    VARATTACKS = Dice(sides=3)

    TOUGHNESS = 5
    SAVE = 4
    WOUNDS = 1

    test_def = DStat(PTS=0, T=TOUGHNESS, Sv=SAVE, W=WOUNDS)

    attackers = [
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) , 0.0833 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=VARDAMAGE) , 2 * 0.0833 ),
        ( AStat(PTS=0, A=VARATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) , 2 * 0.0833 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=VARDAMAGE) * Reroll_D3_Damage, 2.333333 * 0.0833 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * LethalHits , 0.1389 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * SustainedHits_1 , 0.1111 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * RerollHits , 0.125 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * RerollHitsOne , 0.0972 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * RerollWounds , 0.1389 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * RerollWoundsOne , 0.0972 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * PlusOneToWound , 0.1250 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * PlusOneToHit , 0.1111 ),
        ( AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE) * RerollHits * RerollWounds , 0.2083 ),
    ]

    for test_att, expected in attackers:
        print(f"actual, expected: {mean_loop(attacker=test_att, defender=test_def, count=10000):0.4f}, {expected:0.4f}")

if __name__ == "__main__":
    if True:
        run_test()
    else:
        # The targets
        leman_russ_tank = DStat(PTS=170, T=11, Sv=2, W=13, name="Leman Russ")
        chimera = DStat(PTS=70, T=9, Sv=3, W=11, name="Chimera")
        wraithguard = DStat(PTS=190/5, T=7, Sv=2, W=3, name="Wraithguard")
        waveserpent = DStat(PTS=120, T=9, Sv=3, W=13, Inv=5, name="Wave Serpent")
        guardsmen = DStat(PTS=60/10, T=3, Sv=5, W=1, name="Humble Guardsmen")

        terminator_on_the_d = DStat(PTS=185/5, T=5, Sv=2, Inv=4, W=3, name="Space Marine Terminator")
        sword_bro_on_the_d = DStat(PTS=150/5, T=4, Sv=3, W=3, name="Primaris Sword Brethren")
        aintercessor_on_the_d = DStat(PTS=75/5, T=4, Sv=3, W=2, name="Assault Intercessor")
        neophyte_on_the_d = DStat(PTS=10, T=4, Sv=4, W=2, name="Primaris Neophyte")
        eradicator_on_the_d = DStat(PTS=10, T=6, Sv=3, W=3, name="Eradicator")

        # Our vow
        TemplarVow = LethalHits
        # TemplarVow = SustainedHits_1


        # Their boyz
        # ==================================================================================== #
        #       The dreaded Wraithguard
        # ==================================================================================== #
        elf_wraithguard_cannon = AStat(PTS=190/5, A=1, BS_WS=4, S=14, AP=-4, D=d6_damage_plus(0)) * DevestatingWounds
        elf_wraithguard_dscythe = AStat(PTS=190/5, A=1, BS_WS=4, S=10, AP=-4, D=1)

        # Our boyz
        # ==================================================================================== #
        #       Characters
        # ==================================================================================== #
        the_emperors_champion_strike = AStat(PTS=75, A=6, BS_WS=2, S=8, AP=-3, D=3)
        chaplain_gregor_ironmaw = AStat(PTS=60+15, A=5, BS_WS=2, S=6, AP=-1, D=2) * PlusOneToWound * StrengthPlusOne * AP_PlusOne * AttacksPlusOne

        characters = {
            'the_emperors_champion_strike': [ the_emperors_champion_strike * TemplarVow ],
            'chaplain_gregor_ironmaw': chaplain_gregor_ironmaw * TemplarVow
        }

        # ==================================================================================== #
        #       Ranged Boyz
        # ==================================================================================== #
        eradicator_firing_at_a_tank = AStat(PTS=95/3, A=1, BS_WS=3, S=9, AP=-4, D=d6_damage_plus(0))  * RerollHits  * RerollWounds * Reroll_D6_Damage
        eradicator_firing_at_a_tank_in_melta_range = AStat(PTS=95/3, A=1, BS_WS=3, S=9, AP=-4, D=d6_damage_plus(2))  * RerollHits  * RerollWounds * Reroll_D6_Damage
        devastator_lascannon_not_moved = AStat(PTS=120/5, A=1, BS_WS=4, S=12, AP=-3, D=d6_damage_plus(1)) * PlusOneToHit

        eradicators = [copy.deepcopy(eradicator_firing_at_a_tank) for _ in range(0,3)]
        eradicators_melta = [copy.deepcopy(eradicator_firing_at_a_tank_in_melta_range) for _ in range(0,3)]
        devastators = [copy.deepcopy(devastator_lascannon_not_moved) for _ in range(0,4)]
        
        ranged_boyz = {
            'eradicators': eradicators,
            'eradicators_melta': eradicators_melta,
            'devastators': devastators
        }

        # ==================================================================================== #
        #       Sword Brethern
        # ==================================================================================== #
        primaris_sword_brother_with_chainsword = AStat(PTS=150/5, A=5, BS_WS=3, S=4, AP=-1, D=1) * DamagePlusOne
        primaris_sword_brother_with_powerweapon = AStat(PTS=150/5, A=4, BS_WS=3, S=5, AP=-2, D=1) * DamagePlusOne
        primaris_sword_brother_with_thunderhammer = AStat(PTS=150/5, A=3, BS_WS=4, S=8, AP=-2, D=2) * DevestatingWounds * DamagePlusOne
        primaris_sword_brother_with_lclaws = AStat(PTS=150/5, A=5, BS_WS=3, S=5, AP=-2, D=1) * TwinLinked  * DamagePlusOne
        primaris_castellan_with_mastercraft_psword = AStat(PTS=150/5, A=4, BS_WS=2, S=5, AP=-2, D=2) * DamagePlusOne

        sword_brethern = [
            primaris_sword_brother_with_powerweapon * TemplarVow, 
            primaris_sword_brother_with_thunderhammer * TemplarVow, 
            primaris_sword_brother_with_powerweapon * TemplarVow, 
            primaris_sword_brother_with_lclaws * TemplarVow,
            primaris_castellan_with_mastercraft_psword * TemplarVow
            ]
        super_sword_brethern = add_unit(sword_brethern, the_emperors_champion_strike * TemplarVow * DamagePlusOne)
        super_sword_brethern_crusaders_wrath = mod_squad(mod_squad(super_sword_brethern, AP_PlusOne), StrengthPlusOne)

        sword_bros_dict = {
            'sword_brethern': sword_brethern,
            'super_sword_brethern': super_sword_brethern,
            'super_sword_brethern_crusaders_wrath': super_sword_brethern_crusaders_wrath 
        }

        # ==================================================================================== #
        #       Assault Intercessors
        # ==================================================================================== #
        assault_intercessor = AStat(PTS=75/5, A=4, BS_WS=3, S=4, AP=-1, D=1) * RerollWoundsOne

        assault_intercessors = [assault_intercessor*TemplarVow for _ in range(0,10)]
        super_ai = add_unit(mod_squad(assault_intercessors, PlusOneToWound), chaplain_gregor_ironmaw * TemplarVow * RerollWoundsOne)
        super_ai_crusaders_wrath = mod_squad(mod_squad(super_ai, AP_PlusOne), StrengthPlusOne)

        assault_inter_dict = {
            'assault_intercessors': assault_intercessors,
            'super_ai': super_ai,
            'super_ai_crusaders_wrath': super_ai_crusaders_wrath
        }

        # ==================================================================================== #
        #       Primaris Crusader Squad
        # ==================================================================================== #
        primaris_neophyte_w_chainsword = AStat(PTS=140/10, A=5, BS_WS=3, S=4, AP=-1, D=1)
        primaris_initiate_w_chainsword = AStat(PTS=140/10, A=5, BS_WS=3, S=4, AP=-1, D=1)
        primaris_initiate_w_power_fist = AStat(PTS=140/10, A=3, BS_WS=3, S=8, AP=-2, D=2)
        primaris_sword_brother_w_powerweapons = AStat(PTS=140/10, A=3, BS_WS=3, S=5, AP=-2, D=1)

        pri_crusaders = [
            primaris_neophyte_w_chainsword * TemplarVow,
            primaris_neophyte_w_chainsword * TemplarVow,
            primaris_neophyte_w_chainsword * TemplarVow,
            primaris_neophyte_w_chainsword * TemplarVow,
            primaris_initiate_w_chainsword * TemplarVow,
            primaris_initiate_w_chainsword * TemplarVow,
            primaris_initiate_w_chainsword * TemplarVow,
            primaris_initiate_w_power_fist * TemplarVow,
            primaris_initiate_w_power_fist * TemplarVow,
            primaris_sword_brother_w_powerweapons * TemplarVow
        ]
        pri_crusaders_w_gregor = add_unit(mod_squad(pri_crusaders, PlusOneToWound), chaplain_gregor_ironmaw * TemplarVow)
        pri_crusaders_w_gregor_wrath = mod_squad(mod_squad(pri_crusaders_w_gregor, AP_PlusOne), StrengthPlusOne)

        pri_cru_dict = {
            'pri_crusaders': pri_crusaders,
            'pri_crusaders_w_gregor': pri_crusaders_w_gregor,
            'pri_crusaders_w_gregor_wrath': pri_crusaders_w_gregor_wrath
        }

        # ==================================================================================== #
        #       Terminator Assault Squad
        # ==================================================================================== #
        assault_termie_with_hammer_shield = AStat(PTS=185/5, A=3, BS_WS=4, S=8, AP=-2, D=2) * DevestatingWounds
        assault_termie_with_lclaws = AStat(PTS=185/5, A=5, BS_WS=3, S=5, AP=-2, D=1) * TwinLinked

        assault_termies_0_5 = [
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
        ]
        assault_termies_0_5_wrath = mod_squad(mod_squad(assault_termies_0_5, AP_PlusOne), StrengthPlusOne)
        assault_termies_5_0 = [
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
        ]
        assault_termies_5_0_wrath = mod_squad(mod_squad(assault_termies_5_0, AP_PlusOne), StrengthPlusOne)
        assault_termies_3_2 = [
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
        ]
        assault_termies_3_2_wrath = mod_squad(mod_squad(assault_termies_3_2, AP_PlusOne), StrengthPlusOne)
        assault_termies_2_3 = [
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_hammer_shield * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
            assault_termie_with_lclaws * TemplarVow ,
        ]
        assault_termies_2_3_wrath = mod_squad(mod_squad(assault_termies_2_3, AP_PlusOne), StrengthPlusOne)
            
        terminator_assault_sqd_dict = {
            'assault_termies_5_0': assault_termies_5_0,
            'assault_termies_5_0_wrath': assault_termies_5_0_wrath,
            'assault_termies_0_5': assault_termies_0_5,
            'assault_termies_0_5_wrath': assault_termies_0_5_wrath,
            'assault_termies_2_3': assault_termies_2_3,
            'assault_termies_2_3_wrath': assault_termies_2_3_wrath,
            'assault_termies_3_2': assault_termies_3_2,
            'assault_termies_3_2_wrath': assault_termies_3_2_wrath
        }

        # ==================================================================================== #
        #       Statistical Reports
        # ==================================================================================== #
        # I want a plot of the probability that you score N or more damage

        DEFENDER_OPTIONS = {
            'chimera': chimera,
            'leman_russ': leman_russ_tank,
            'wraithguard': wraithguard,
            'waveserpent': waveserpent,
            'guardsmen': guardsmen,
        }
        ATTACKER_OPTIONS = {
            'termies': terminator_assault_sqd_dict,
            'pri_crusaders': pri_cru_dict,
            'a_inter': assault_inter_dict,
            'sword_bros': sword_bros_dict,
            'ranged': ranged_boyz,
            'chars': characters
        }
        
        par = argparse.ArgumentParser(description='Warhammer 40k 10th Ed. Math Hammer')
        par.add_argument('ATTACKER', type=str, choices=ATTACKER_OPTIONS.keys(), help='Attacker group to run in simulation.')
        par.add_argument('DEFENDER', type=str, choices=DEFENDER_OPTIONS.keys(), help='Defender to run in simulation.')
        par.add_argument('--count', type=str, help=f'Number of sequences to run.  Default is {DEFAULT_COUNT}', default=DEFAULT_COUNT)

        args = par.parse_args()

        the_list = ATTACKER_OPTIONS[args.ATTACKER]
        the_target = DEFENDER_OPTIONS[args.DEFENDER]

        h = plt.figure(1)

        VERY_LIKELY = 5/6.0
        for k in the_list:
            data = phist_loop(attacker=the_list[k], defender=the_target, count=args.count)
            xdata = np.asarray([ float(x) for x in range(0,len(data)) ])
            # X must be monotonically increasing!
            very_likely_damage_output = np.interp(VERY_LIKELY, data[::-1], xdata[::-1])
            likelyhood_of_kill = np.interp(the_target.wounds, xdata, data)
            # sum the points for each side
            def_points = the_target.points
            att_points = np.sum([x.points for x in the_list[k]])
            # potential relative to point cost
            points_per_damage = att_points / very_likely_damage_output


            print(f"================ {k} ")
            print(f"  {att_points} points attacking a target of {def_points} points")
            print(f"  {int(likelyhood_of_kill*100)}% chance of one-shot")
            print(f"  {int(VERY_LIKELY*100)}% chance {int(very_likely_damage_output)} or more damage is dealt.")
            print(f"  {points_per_damage:0.2f} PPD")
            plt.plot(data)
        plt.legend(the_list.keys())
        plt.title(f"versus {the_target}")
        plt.show()