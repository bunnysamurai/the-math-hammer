#!/usr/bin/env python

import random
import numpy as np
import numbers
import copy
import matplotlib.pyplot as plt
import argparse
from enum import Enum

class CharState(Enum):
    DiceList = 1
    Dice = 2
    Int = 3

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
def modifier_reroll_if_less_than(sequence, threshold):
    def functor(state):
        if state.roll[sequence].value < threshold and state.roll[sequence].roll_count < 2:
            source = state.determine_pool_source(sequence)
            state.pool[source].append(state.roll[sequence])
            state.scratch['break_mod_loop'] = True
        return state
    return functor
def modifier_always_succeed(sequence):
    def functor(state):
        state.pool[sequence].append(copy.deepcopy(state.roll[sequence]))
        state.scratch['break_mod_loop'] = True
        return state
    return functor



# =========================================================================== #
class Dice():
    '''
        TODO 'sides' could also be a list of integers, in which case we are 
        rolling multiple "dice" but to the framework, it's only a single 
        rerollable "thing".
    '''
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
        if self.roll_count > 2:
            raise ValueError(f"Roll count reached {self.roll_count}, which is illegal")
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
        modifier_value = np.clip(modifier_value, a_min=-1, a_max=1)
        return unmodified + modifier_value

    def test_for_diceness(state, characteristic):
        try: # it's a [Dice,]
            for item in state.char[characteristic]:
                pass
            return CharState.DiceList
        except Exception as e:
            pass
        
        try: # it's a Dice
            if state.char[characteristic].sides > 0: # i.e. is rollable
                pass
            return CharState.Dice
        except Exception as e:
            pass

        # it's an int, or someone else can throw if not
        return CharState.Int

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
        char_is_what = test_for_diceness(state, 'attacks')
        if char_is_what == CharState.DiceList:
            for item in state.char['attacks']:
                state.pool['preamble'].append(item)
        elif char_is_what == CharState.Dice:
            state.pool['preamble'].append(state.char['attacks'])
        elif char_is_what == CharState.Int:
            state.pool['preamble'].append(Dice(sides=6, fixed=state.char['attacks']))
        else:
            raise ValueError("Impossible")
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
            # what dice gets added to the pool?
            # well, if the user has already provided a Dice, use that
            # otherwise, add a Dice that has a fixed value equal to the damage char
            char_state = test_for_diceness(state, 'damage')
            if char_state is CharState.Int:
                state.pool['save'].append(Dice(fixed=state.char['damage']))
            elif char_state is CharState.DiceList:
                for item in state.char['damage']:
                    state.pool['save'].append(item)
            elif char_state is CharState.Dice:
                state.pool['save'].append(state.char['damage'])
            else:
                raise ValueError("Impossible save pool state")
        return state
    def resolve_damage_pool(state):
        damage_to_add = state.roll['damage'].value
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
    def __init__(self, A, BS_WS, S, AP, D, description="AStat"):
        self.attacks = A
        self.skill = BS_WS
        self.strength = S
        self.armourpen = AP
        self.damage = D
        self.description = description

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
        try:
            for mod, seq in zip(other.func, other.seq):
                result.modifiers[seq].append(mod)
        except Exception as e:
            result.modifiers[other.seq].append(other.func)
        return result

    def __str__(self):
        return f"{self.description}(A:{self.attacks} BS_WS:{self.skill} S:{self.strength} AP:{self.armourpen} D:{self.damage})"
    
class DStat():
    def __init__(self, T, Sv, W, Inv=None, FNP=None, description="DStat"):
        self.toughness = T
        self.save = Sv
        self.wounds = W
        self.invuln = Inv
        self.feelnopain = FNP
        self.description = description

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
        result = f"{self.description}(T:{self.toughness} Sv:{self.save}+"
        if self.invuln is not None:
            result += f"|{self.invuln}++"
        if self.feelnopain is not None:
            result += f"|{self.feelnopain}+++"
        result += f" W:{self.wounds})"
        return result


    def __mul__(self, other):
        result = copy.deepcopy(self)
        try:
            for mod in other.func:
                result.modifiers[other.seq].append(mod)
        except Exception as e:
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
                    the_dice = copy.deepcopy(state.pool[pool_source][0])
                    state.pool[pool_source] = state.pool[pool_source][1:]
                    state.scratch['unmodified_roll'] = copy.deepcopy(the_dice.roll())
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
        
class Model():
    def __init__(self, weapons, defence, pts="N/A", name="N/A"):
        self.weapon = copy.deepcopy(weapons)
        self.defence = defence
        self.name = name
        self.pts = pts

    # TODO is this a bad idea?  Maybe!
    def __div__(self, other):
        self.defence = self.defence * other
        return self
    def __mul__(self, other):
        self.weapon = self.weapon * other
        return self
    def __sub__(self, attacker):
        '''
            model - model
        '''
        try:
            acc = 0
            for wpn in attacker.weapons:
                acc += self.defence - wpn
            return acc
        except Exception as e:
            return self.defence - attacker.weapons

    def __str__(self):
        return f"{self.name}({self.pts} pts):\n  {self.weapon}\n  {self.defence}"

class Unit():
    def __init__(self, model_list):
        self.models = model_list

    def __mul__(self, other):
        '''
            unit * modifier
        '''
        self.models = [x * other for x in self.models]

    def __sub__(self, other):
        '''
            unit - unit
            unit - model
        '''
        acc = 0
        defending_model = self._get_best_defender()
        success = True
        try: # unit - unit
            for model in other.models:
                acc += defending_model - model
        except Exception as e:
            success = False
        if success is True:
            return acc
        return defending_model - model
        


class Modifier():
    def __init__(self, sequence, functor):
        self.seq = [sequence]
        self.func = [functor]

    def __mul__(self, other):
        self.seq += other.seq
        self.func += other.func
        return self


    
Torrent = Modifier(sequence='hit', functor=modifier_always_succeed('hit'))
RerollWounds = Modifier(sequence='wound', functor=modifier_reroll_fails('wound'))
RerollWoundsOne = Modifier(sequence='wound', functor=modifier_reroll_ones('wound'))
TwinLinked = RerollWounds
RerollHits = Modifier(sequence='hit', functor=modifier_reroll_fails('hit'))
RerollHitsOne = Modifier(sequence='hit', functor=modifier_reroll_ones('hit'))
Reroll_D6_Damage = Modifier(sequence='damage', functor=modifier_reroll_if_less_than(sequence='damage', threshold=4))
Reroll_D3_Damage = Modifier(sequence='damage', functor=modifier_reroll_if_less_than(sequence='damage', threshold=2))
PlusOneToWound = Modifier(sequence='wound', functor=modifier_roll_add_one('wound'))
PlusOneToHit = Modifier(sequence='hit', functor=modifier_roll_add_one('hit'))
LethalHits = Modifier(sequence='hit', functor=modifier_lethal_hits())
SustainedHits_1 = Modifier(sequence='hit', functor=modifier_sustained_hits(X=1))
DevestatingWounds = Modifier(sequence='wound', functor=modifier_devastating_wounds())
StrengthPlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_add_one('strength'))
AP_PlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_subtract_one('armourpen'))
AttacksPlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_add_one('attacks'))
DamagePlusOne = Modifier(sequence='attacks', functor=modifier_characteristic_add_one('damage'))
CriticalHit_5up = Modifier(sequence='attacks', functor=modifier_characteristic_subtract_one('criticalhit'))

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

def stats_comp(sample):
    # create histogram
    phist = np.zeros((int(np.max(sample))+1,))
    for ii in range(0,len(phist)):
        phist[ii] = len(sample[sample == ii]) / len(sample)
    histogram = copy.deepcopy(phist)
    phist = phist[::-1]
    phist = np.cumsum(phist)
    cdf = phist[::-1]
    return cdf, histogram

def stats_loop(attacker, defender, count):
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
    cdf, histogram = stats_comp(acc)
    return cdf, histogram, acc

def fold_to_models_removed_stats(damage_seq, target):
    W = target.wounds
    # move through the sequence, sequentially, and note how many "swings" it took to equal-or-exceed the wounds of the target
    # we also want to compute about how many models are removed per swing
    swings_taken = []
    models_removed = []
    acc = 0
    count = 0
    for damage_dealt in damage_seq:
        count += 1
        acc += damage_dealt
        if acc >= W:
            swings_taken.append(count)
            count = 0
            acc = 0
        models_removed.append(int(damage_dealt / W))
    # swings_taken is our sample
    cdf_rounds, _ = stats_comp(np.asarray(swings_taken))
    cdf_removed, _ = stats_comp(np.asarray(models_removed))
    return cdf_rounds, cdf_removed


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
    VARDAMAGE = Dice(sides=3)
    VARATTACKS = Dice(sides=3)

    TOUGHNESS = 5
    SAVE = 4
    WOUNDS = 1

    TestModelArmour = DStat(PTS=0, T=TOUGHNESS, Sv=SAVE, W=WOUNDS)
    TestModelGun = AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE)
    TestModelVarD = AStat(PTS=0, A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=VARDAMAGE)
    TestModelVarA = AStat(PTS=0, A=VARATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE)

    test_def = Model(TestModelGun, TestModelArmour)

    attackers = [
        ( Model(TestModelGun, TestModelArmour) , 0.0833, 'Nominal' ),
        ( Model(TestModelGun, TestModelArmour) * Torrent , 0.1667, 'Torrent' ),
        ( Model(TestModelVarD, TestModelArmour) , 2 * 0.0833, 'D3 Damage' ),
        ( Model(TestModelVarA, TestModelArmour) , 2 * 0.0833, 'D3 Attacks' ),
        ( Model(TestModelVarD, TestModelArmour) * Reroll_D3_Damage, 2.333333 * 0.0833, 'Rerolling D3 Damage'),
        ( Model(TestModelGun, TestModelArmour) * LethalHits , 0.1389, 'Lethal Hits' ),
        ( Model(TestModelGun, TestModelArmour) * SustainedHits_1 , 0.1111, 'Sustained Hits 1' ),
        ( Model(TestModelGun, TestModelArmour) * SustainedHits_1 * CriticalHit_5up, 0.1389, 'Sustained Hits 1, CritHit 5+' ),
        ( Model(TestModelGun, TestModelArmour) * RerollHits , 0.125, 'Reroll Hits' ),
        ( Model(TestModelGun, TestModelArmour) * RerollHitsOne , 0.0972, 'Reroll Hit Rolls of 1' ),
        ( Model(TestModelGun, TestModelArmour) * RerollWounds , 0.1389, 'Reroll Wounds' ),
        ( Model(TestModelGun, TestModelArmour) * RerollWoundsOne , 0.0972, 'Reroll Wound Rolls of 1' ),
        ( Model(TestModelGun, TestModelArmour) * PlusOneToWound , 0.1250, '+1 to Wound' ),
        ( Model(TestModelGun, TestModelArmour) * PlusOneToHit , 0.1111, '+1 to Hit' ),
        ( Model(TestModelGun, TestModelArmour) * RerollHits * RerollWounds , 0.2083, 'Full Rerolls' ),
    ]

    TEST_COUNT=10000
    print(f"Context: Attacks=Damage=1 (unless noted otherwise), Hit=0.5, Wound=0.333, Save=0.5, MonteCarlo Count={TEST_COUNT}")
    for test_att, expected, details in attackers:
        print(f"actual, expected: {mean_loop(attacker=test_att, defender=test_def, count=TEST_COUNT):0.4f}, {expected:0.4f}  ({details})")

if __name__ == "__main__":
    if False:
        run_test()
    else:
        # The targets
        leman_russ_tank = Model(
            weapons=[
                AStat(A=Dice(bias=3), BS_WS=4, S=10, AP=-1, D=3, description="Battle Cannon"),
                AStat(A=Dice(sides=3), BS_WS=4, S=8, AP=-3, D=2, description="Plasma Cannon (supercharged)"),
                AStat(A=Dice(sides=3), BS_WS=4, S=8, AP=-3, D=2, description="Plasma Cannon (supercharged)"),
                AStat(A=3, BS_WS=4, S=5, AP=-1, D=2, description="Heavy Bolter"),
            ], 
            defence=DStat(T=11, Sv=2, W=13), 
            pts=170, name="Leman Russ Battle Tank")
        chimera = DStat(PTS=70, T=9, Sv=3, W=11, name="Chimera")
        wraithguard = DStat(PTS=190/5, T=7, Sv=2, W=3, name="Wraithguard")
        waveserpent = DStat(PTS=120, T=9, Sv=3, W=13, Inv=5, name="Wave Serpent")
        guardsmen = DStat(PTS=60/10, T=3, Sv=5, W=1, name="Humble Guardsmen")

        terminator_on_the_d = DStat(PTS=185/5, T=5, Sv=2, Inv=4, W=3, name="Space Marine Terminator")
        sword_bro_on_the_d = DStat(PTS=150/5, T=4, Sv=3, W=3, name="Primaris Sword Brethren")
        aintercessor_on_the_d = DStat(PTS=75/5, T=4, Sv=3, W=2, name="Assault Intercessor")
        neophyte_on_the_d = DStat(PTS=10, T=4, Sv=4, W=2, name="Primaris Neophyte")
        eradicator_on_the_d = DStat(PTS=10, T=6, Sv=3, W=3, name="Eradicator")
        redemptor_on_the_d = DStat(PTS=210, T=10, Sv=2, W=12, name="Redemptor Dreadnought")

        # Our vow
        TemplarVow = LethalHits
        # TemplarVow = SustainedHits_1


        # Their boyz
        # ==================================================================================== #
        #       The dreaded Wraithguard
        # ==================================================================================== #
        elf_wraithguard_cannon = AStat(PTS=190/5, A=1, BS_WS=4, S=14, AP=-4, D=Dice()) * DevestatingWounds
        elf_wraithguard_dscythe = AStat(PTS=190/5, A=1, BS_WS=4, S=10, AP=-4, D=1)

        # Our boyz
        # ==================================================================================== #
        #       Characters
        # ==================================================================================== #
        the_emperors_champion_strike = AStat(PTS=75, A=6, BS_WS=2, S=8, AP=-3, D=3)
        chaplain_gregor_ironmaw = AStat(PTS=60+15, A=5, BS_WS=2, S=6, AP=-1, D=2) * PlusOneToWound * StrengthPlusOne * AP_PlusOne * AttacksPlusOne
        apothecary_bio_gun = AStat(PTS=55+30, A=1, BS_WS=3, S=5, AP=-1, D=2)

        characters = {
            'the_emperors_champion_strike': [ the_emperors_champion_strike * TemplarVow ],
            'chaplain_gregor_ironmaw': [ chaplain_gregor_ironmaw * TemplarVow ]
        }

        # ==================================================================================== #
        #       Ranged Boyz
        # ==================================================================================== #
        TotalObliteration = RerollHits  * RerollWounds * Reroll_D6_Damage
        melta_rifle = AStat(PTS=95/3, A=1, BS_WS=3, S=9, AP=-4, D=Dice())
    # def __init__(self, PTS, T, Sv, W, Inv=None, FNP=None, name=None):
        eradicator_firing_at_a_tank = AStat(PTS=95/3, A=1, BS_WS=3, S=9, AP=-4, D=Dice())  * TotalObliteration
        eradicator_firing_at_a_tank_in_melta_range = AStat(PTS=95/3, A=1, BS_WS=3, S=9, AP=-4, D=Dice(bias=2))  * TotalObliteration
        eradicator_multi_firing_at_a_tank = AStat(PTS=95/3, A=2, BS_WS=4, S=9, AP=-4, D=Dice())  * TotalObliteration
        eradicator_multi_firing_at_a_tank_in_melta_range = AStat(PTS=95/3, A=2, BS_WS=4, S=9, AP=-4, D=Dice(bias=2))  * TotalObliteration
        devastator_lascannon_not_moved = AStat(PTS=120/5, A=1, BS_WS=4, S=12, AP=-3, D=Dice(bias=1)) * PlusOneToHit

        devastators = [copy.deepcopy(devastator_lascannon_not_moved) for _ in range(0,4)]

        eradicators = [copy.deepcopy(eradicator_firing_at_a_tank) for _ in range(0,3)]
        eradicators_melta = [copy.deepcopy(eradicator_firing_at_a_tank_in_melta_range) for _ in range(0,3)]
        eradicators_if_i_built_them_different = [copy.deepcopy(eradicator_firing_at_a_tank) for _ in range(0,2)] + [copy.deepcopy(eradicator_multi_firing_at_a_tank) for _ in range(0,1)]
        eradicators_melta_if_i_built_them_different = [copy.deepcopy(eradicator_firing_at_a_tank_in_melta_range) for _ in range(0,2)] + [copy.deepcopy(eradicator_multi_firing_at_a_tank_in_melta_range) for _ in range(0,1)]

        full_squad_eradicators = [copy.deepcopy(eradicator_firing_at_a_tank) for _ in range(0,4)] + [copy.deepcopy(eradicator_multi_firing_at_a_tank) for _ in range(0,2)]
        full_squad_eradicators2 = [copy.deepcopy(eradicator_firing_at_a_tank2) for _ in range(0,4)] + [copy.deepcopy(eradicator_multi_firing_at_a_tank) for _ in range(0,2)]
        full_squad_eradicators_melta = [copy.deepcopy(eradicator_firing_at_a_tank_in_melta_range) for _ in range(0,4)] + [copy.deepcopy(eradicator_multi_firing_at_a_tank_in_melta_range) for _ in range(0,2)]

        # Eradicators + Apothecary Biologis with Fire Discipline = A lot of hurt
        full_eradicators_firedis_stack = mod_squad(mod_squad(mod_squad(add_unit(full_squad_eradicators, apothecary_bio_gun), LethalHits), SustainedHits_1), CriticalHit_5up)
        full_eradicators_melta_firedis_stack = mod_squad(mod_squad(mod_squad(add_unit(full_squad_eradicators_melta, apothecary_bio_gun), LethalHits), SustainedHits_1), CriticalHit_5up)

        blastadd = 0
        # Venerable Brother Grammituis has 3 gun
        ven_brother_grammituis_firing = [
            AStat(PTS=210/3, A=Dice(), BS_WS=3, S=5, AP=-1, D=1) * Torrent, # heavy flamer
            AStat(PTS=210/3, A=12, BS_WS=3, S=6, AP=0, D=1) * DevestatingWounds, # heavy onslaught gatling cannon
            AStat(PTS=210/3, A=Dice(bias=blastadd), BS_WS=3, S=4, AP=0, D=1) * TwinLinked, # twin fragstorm grenade launcher
        ] 

        # The other dread has 4 gun
        the_other_redemptor_firing = [
            AStat(PTS=210/4, A=Dice(), BS_WS=3, S=5, AP=-1, D=1) * Torrent, # heavy flamer
            AStat(PTS=210/4, A=Dice(bias=blastadd), BS_WS=3, S=4, AP=0, D=1) * TwinLinked, # twin fragstorm grenade launcher
            AStat(PTS=210/4, A=Dice(bias=1+blastadd), BS_WS=3, S=9, AP=-4, D=3), # macro plasma incinerator
            AStat(PTS=210/4, A=Dice(sides=3), BS_WS=3, S=8, AP=-1, D=2), # icarus rocket pod
        ]

        ranged_boyz = {
            'devastators': devastators,
            'eradicators': eradicators,
            'eradicators_melta': eradicators_melta,
            'eradicators_built_right': eradicators_if_i_built_them_different,
            'eradicators_melta_built_right': eradicators_melta_if_i_built_them_different,
            'full_squad_eradicators': full_squad_eradicators,
            'full_squad_eradicators2': full_squad_eradicators2,
            'full_squad_eradicators_melta' : full_squad_eradicators_melta,
            'redemptor_using_gun': the_other_redemptor_firing,
            'ven_brother_grammituis_using_gun': ven_brother_grammituis_firing,
            # 'full_eradicators_firedis_stack': full_eradicators_firedis_stack,
            # 'full_eradicators_melta_firedis_stack': full_eradicators_melta_firedis_stack,
        }

        # ==================================================================================== #
        #       Redemptor Fists
        # ==================================================================================== #
        redemptor_claw = [ AStat(PTS=210, A=Dice(), BS_WS=3, S=5, AP=-1, D=1) * TemplarVow ]
        brutalis_redemptor_talons_strike = [ AStat(PTS=160, A=6, BS_WS=3, S=12, AP=-2, D=3) * TemplarVow * TwinLinked]
        brutalis_redemptor_talons_sweep = [ AStat(PTS=160, A=10, BS_WS=3, S=7, AP=-2, D=1) * TemplarVow * TwinLinked]
        redemptor_claw_wrath = mod_squad(mod_squad(redemptor_claw, AP_PlusOne), StrengthPlusOne)
        brutalis_redemptor_talons_strike_wrath = mod_squad(mod_squad(brutalis_redemptor_talons_strike, AP_PlusOne), StrengthPlusOne)
        brutalis_redemptor_talons_sweep_wrath = mod_squad(mod_squad(brutalis_redemptor_talons_sweep, AP_PlusOne), StrengthPlusOne)

        redemptor_boyz = {
            'redemptor_claw': redemptor_claw,
            'redemptor_claw_wrath': redemptor_claw_wrath,
            'brutalis_redemptor_talons_strike': brutalis_redemptor_talons_strike,
            'brutalis_redemptor_talons_strike_wrath': brutalis_redemptor_talons_strike_wrath,
            'brutalis_redemptor_talons_sweep': brutalis_redemptor_talons_sweep,
            'brutalis_redemptor_talons_sweep_wrath': brutalis_redemptor_talons_sweep_wrath,
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
            'terminator': terminator_on_the_d,
            'sword_bro': sword_bro_on_the_d,
            'intercessor': aintercessor_on_the_d,
            'neophyte': neophyte_on_the_d,
            'eradicator': eradicator_on_the_d,
        }
        ATTACKER_OPTIONS = {
            'termies': terminator_assault_sqd_dict,
            'pri_crusaders': pri_cru_dict,
            'a_inter': assault_inter_dict,
            'sword_bros': sword_bros_dict,
            'ranged': ranged_boyz,
            'chars': characters,
            'redemptor_boyz': redemptor_boyz,
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

        VERY_LIKELY = args.verylikely
        for k in the_list:
            data, _, damage_sequence = stats_loop(attacker=the_list[k], defender=the_target, count=args.count)

            def compute_likelihood_value(data, thresh):
                xdata = np.asarray([ float(x) for x in range(0,len(data)) ])
                return np.interp(thresh, data[::-1], xdata[::-1])

            xdata = np.asarray([ float(x) for x in range(0,len(data)) ])
            likelyhood_of_kill = np.interp(the_target.wounds, xdata, data)
            very_likely_damage_output = compute_likelihood_value(data, VERY_LIKELY)

            # sum the points for each side
            def_points = the_target.points
            att_points = np.sum([x.points for x in the_list[k]])
            # potential relative to point cost
            points_per_damage = att_points / very_likely_damage_output
            
            # models-removed-per-round and rounds-taken-to-remove-model
            cdf_rounds_taken, cdf_models_removed = fold_to_models_removed_stats(damage_sequence, the_target)
            very_likely_number_of_rounds_taken = compute_likelihood_value(cdf_rounds_taken, VERY_LIKELY)
            very_likely_models_removed = compute_likelihood_value(cdf_models_removed, VERY_LIKELY)

            print(f"================ {k} ")
            print(f"  {att_points} points attacking a target of {def_points} points")
            print(f"  {int(VERY_LIKELY*100)}% chance {int(very_likely_damage_output)} or more damage is dealt.")
            print(f"  {int(VERY_LIKELY*100)}% chance {very_likely_number_of_rounds_taken:0.1f} rounds taken to remove a model.")
            print(f"  {int(VERY_LIKELY*100)}% chance {int(very_likely_models_removed)} models or more are removed in a single round.")
            print(f"  {points_per_damage:0.2f} PPD")
            plt.plot(data)
        plt.legend(the_list.keys())
        plt.title(f"versus {the_target}")
        plt.show()