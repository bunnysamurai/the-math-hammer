#!/usr/bin/env python

import random
import numpy as np
import copy
from enum import Enum
import scipy
import scipy.stats


MELEE_WEAPON_RANGE = 0
MELEE_RANGE_INCHES = 1

class CharState(Enum):
    DiceList = 1
    Dice = 2
    Int = 3

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
        state.scratch['break_mod_loop'] = True
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
        'sides' can also be a list of integers, in which case we are 
        rolling multiple "dice" but to the framework, it's only a single 
        rerollable "thing".
    '''
    def __init__(self, sides=6, fixed=None, bias=0):
        self.roll_count = 0
        self.sides = sides
        self.fixed_value = fixed
        try: # self.sides is a list
            if self.fixed_value is not None:
                self.value = [self.fixed_value for _ in self.sides]
            else:
                self.value = [None for _ in self.sides]
        except Exception as e: # self.sides is an int
            self.value = None if self.fixed_value is None else self.fixed_value
        self.bias = bias
    
    def roll(self):
        self.roll_count += 1
        try: # self.sides is a list
            for idx, sides in enumerate(self.sides):
                if self.fixed_value is None:
                    self.value[idx] = random.randint(1,sides) + self.bias
        except Exception as e: # self.sides is an int
            if self.fixed_value is None:
                self.value = random.randint(1,self.sides) + self.bias
        if self.roll_count > 2:
            raise ValueError(f"Roll count reached {self.roll_count}, which is illegal")
        return self
    
    def __str__(self):
        result = f"D{self.sides}"
        if self.bias > 0:
            result += f"+{self.bias}"
        return result

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
        self.pool = {'preamble': [], 'attacks': [], 'hit': [], 'wound': [], 'save': [], 'damage': []}
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
            'wounds': None,
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
        self.scratch['actual_damage_used'] = []
        self.scratch['damage_wasted'] = []

    def __str__(self):
        result = f"pool: {self.pool}\n" + f"roll: {self.roll}\n" + f"char: {self.char}\n" + f"threshold: {self.threshold}"
        return result

    def resolve(self):
        damage_used = max(0, np.sum(self.scratch['actual_damage_used']))
        damage_wasted = max(0, np.sum(self.scratch['damage_wasted']))
        return damage_used, damage_wasted

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
        # for _ in range(0, damage_to_add):
        state.pool['damage'].append(Dice([6 for _ in range(0, damage_to_add)]))
        return state
    def resolve_fnp_pool(state):
        def listify(item):
            try:
                _ = len(item)
                return np.asarray(item)
            except Exception as e:
                return np.asarray([item])

        # count up the number of fails
        thresh = state.determine_threshold('fnp') 
        rolls = listify(state.roll['fnp'].value)
        if thresh is not None:
            roll_status = rolls < thresh
            unmod_roll_is_1_status = listify(state.scratch['unmodified_roll'].value) == 1
            defender_fnp_fails = roll_status + unmod_roll_is_1_status
            damage_tally = np.sum(defender_fnp_fails == True)
        else:
            damage_tally = len(rolls)

        # of course, we can only do as much damage as there are wounds on the target
        target_wounds = state.char['wounds']
        state.scratch['actual_damage_used'].append(min(target_wounds, damage_tally))
        state.scratch['damage_wasted'].append(max(0, damage_tally - target_wounds))

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

class Modifier():
    def __init__(self, sequence, functor, id=None):
        self.seq = [sequence]
        self.func = [functor]
        self.id = [id]

    def __mul__(self, other):
        result = copy.deepcopy(self)
        result.seq += other.seq
        result.func += other.func
        result.id += other.id
        return result

class AStat():
    def __init__(self, A, BS_WS, S, AP, D, Range, description="AStat"):
        self.attacks = A
        self.skill = BS_WS
        self.strength = S
        self.armourpen = AP
        self.damage = D
        self.range = Range
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
        # solely for stringifying (json serialization)
        self.modifiers_ids = {
                'preamble': [],
                'attacks': [],
                'hit': [], 
                'strength': [],
                'toughness': [],
                'wound': [], 
                'armourpen': [],
                'invuln': [], 
                'sv': [], 
                'save': [], 
                'damage': [],
                'fnp': []}


    def __mul__(self, other: Modifier):
        result = copy.deepcopy(self)
        try:
            for mod, seq, id in zip(other.func, other.seq, other.id):
                result.modifiers[seq].append(mod)
                result.modifiers_ids[seq].append(id)
        except Exception as e:
            result.modifiers[other.seq].append(other.func)
            result.modifiers_ids[other.seq].append(other.id)
        return result

    def __str__(self):
        return f"{self.description}(R:{self.range} A:{self.attacks} BS_WS:{self.skill} S:{self.strength} AP:{self.armourpen} D:{self.damage})"
    
class DStat():
    def __init__(self, T, Sv, W, Inv=None, FNP=None, description="DStat"):
        self.toughness = T
        self.save = Sv
        self.wounds = W
        self.invuln = Inv
        self.feelnopain = FNP
        self.description = description

        # we only interact with the .char field
        self.modifiers = {'preamble': [assign_char('toughness', self.toughness), assign_char('invuln', self.invuln), assign_char('sv', self.save), assign_char('fnp', self.feelnopain), assign_char('wounds', self.wounds)],
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
        # solely for stringifying (json serialization)
        self.modifiers_ids = {
                'preamble': [],
                'attacks': [],
                'hit': [], 
                'strength': [],
                'toughness': [],
                'wound': [], 
                'armourpen': [],
                'invuln': [], 
                'sv': [], 
                'save': [], 
                'damage': [],
                'fnp': []}

    def __str__(self):
        result = f"{self.description}(T:{self.toughness} Sv:{self.save}+"
        if self.invuln is not None:
            result += f"|{self.invuln}++"
        if self.feelnopain is not None:
            result += f"|{self.feelnopain}+++"
        result += f" W:{self.wounds})"
        return result


    def __mul__(self, other: Modifier):
        result = copy.deepcopy(self)
        try:
            for mod, seq, id in zip(other.func, other.seq, other.id):
                result.modifiers[seq].append(mod)
                result.modifiers_ids[seq].append(id)
        except Exception as e:
            result.modifiers[other.seq].append(other.func)
            result.modifiers_ids[other.seq].append(other.id)
        return result

    def __sub__(self, attacker: AStat):
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
    def __init__(self, weapons, defence, pts="N/A", name="N/A", position=0):
        self.weapons = copy.deepcopy(weapons)
        self.defence = defence
        self.name = name
        self.points = pts
        self.wounds = self.defence.wounds
        self.pos = position

    # TODO is this a bad idea?  Maybe!
    def __div__(self, other):
        result = copy.deepcopy(self)
        result.defence = result.defence * other
        return result
    def __mul__(self, other):
        result = copy.deepcopy(self)
        try:
            result.weapons = [wpn * other for wpn in result.weapons]
        except Exception as e:
            result.weapons = result.weapons * other
        return result
    def __sub__(self, attacker):
        '''
            model - model
            model - unit
        '''

        def check_if_in_range(attack_pos, defend_pos, attack_wpn):
            # for melee, return true only if they are equal
            # for ranged, return true if distance is less than range AND positions are not equal
            result = False
            sep_dis = abs(attack_pos - defend_pos)
            if( attack_wpn.range == MELEE_WEAPON_RANGE ): # TODO make more explicit that melee weapons are designated by a range of "0 inches"
                result = sep_dis < MELEE_RANGE_INCHES
            else:
                result = sep_dis <= attack_wpn.range and sep_dis >= MELEE_RANGE_INCHES
            return result

        def handle_model(att_model):
            try:
                acc = np.zeros((2,))
                for wpn in att_model.weapons:
                    acc += 0 if not check_if_in_range(att_model.pos, self.pos, wpn) else self.defence - wpn
                return acc
            except Exception as e:
                if not check_if_in_range(att_model.pos, self.pos, att_model.weapons):
                    return 0
                else:
                    return self.defence - att_model.weapons

        try:
            acc = np.zeros((2,))
            for model in attacker.models:
                acc += handle_model(model)
            return acc
        except Exception as e:
            pass

        return handle_model(attacker)

    def __str__(self):
        result = f"{self.name}({self.points:0.2f} pts):"
        try:
            for wpn in self.weapons:
                result += f"\n  {wpn}"
        except Exception as e:
            result += f"\n  {self.weapons}"
        result += f"\n  {self.defence}"
        result += f"\n  @{self.pos}in"
        return result

class Unit():
    def __init__(self, model_list: list, name=None):
        '''
            unit_wounds is the total amount of wounds this unit has
            wounds is the **majority** wounds characteristic among models in the unit
        '''
        # the list of unmodified models
        self.models_untouched = model_list
        # the list of modified models, plus a book-keeping list of the modifiers active for the unit
        self.models = copy.deepcopy(self.models_untouched)
        self.unit_modifiers = []
        # the aggregate stats
        self.unit_wounds, self.wounds, self.points = self.__aggregate_model_stats()
        self.name = name


    def __aggregate_model_stats(self):
        unit_wounds = np.sum([mdl.defence.wounds for mdl in self.models_untouched])
        mode, _ = scipy.stats.mode([mdl.defence.wounds for mdl in self.models_untouched])
        wounds = np.max(mode)
        points = np.sum([mdl.points for mdl in self.models_untouched])
        return unit_wounds, wounds, points

    def __str__(self):
        return f"{self.models[0]}"

    def __mul__(self, other):
        '''
            unit * modifier
        '''
        result = copy.deepcopy(self)
        result.unit_modifiers.append(other)
        result.models = copy.deepcopy(result.models_untouched)
        for mod in result.unit_modifiers:
            result.models = [x * mod for x in result.models]
        return result

    def __add__(self, other: Model):
        ''' other had better be a Model'''
        result = copy.deepcopy(self)

        # when we add a unit, we need to:
        #   update the list of unmodifier models
        #   update the aggregate stats
        #   update the list of modified models

        result.models_untouched.append(copy.deepcopy(other))
        result.unit_wounds, result.wounds, result.points = result.__aggregate_model_stats()

        for mod in result.unit_modifiers:
            other = other * mod
        result.models.append(other)
        return result

    def __sub__(self, other):
        '''
            unit - unit
            unit - model
        '''
        acc = np.zeros((2,))
        defending_model = self._get_best_defender()
        try: # unit - unit
            for model in other.models:
                acc += defending_model - model
            return acc
        except Exception as e:
            pass
        return defending_model - other
    
    def _get_best_defender(self):
        ''' the rules generally are:
            1. use majority toughness
            2. use best save
            3. bodyguard models before leader
        '''
        # TODO for now, we'll just use the first model in the unit
        return self.models[0]
        
Torrent = Modifier(sequence='hit', functor=modifier_always_succeed('hit'))
RerollWounds = Modifier(sequence='wound', functor=modifier_reroll_fails('wound'))
RerollWoundsOne = Modifier(sequence='wound', functor=modifier_reroll_ones('wound'))
TwinLinked = RerollWounds
RerollHits = Modifier(sequence='hit', functor=modifier_reroll_fails('hit'))
RerollHitsOne = Modifier(sequence='hit', functor=modifier_reroll_ones('hit'))
Reroll_D6_Damage = Modifier(sequence='damage', functor=modifier_reroll_if_less_than(sequence='damage', threshold=4))
Reroll_D3_Damage = Modifier(sequence='damage', functor=modifier_reroll_if_less_than(sequence='damage', threshold=2))
Reroll_D3_Attacks = Modifier(sequence='attacks', functor=modifier_reroll_if_less_than(sequence='attacks', threshold=2))
Reroll_D6_Attacks = Modifier(sequence='attacks', functor=modifier_reroll_if_less_than(sequence='attacks', threshold=4))
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
    acc = np.zeros((N,2)) # used, wasted
    if type(attacker) is list:
        for att in attacker:
            tmp = np.zeros((N,2)) 
            for ii in range(0, N):
                # used, wasted = defender - att
                tmp[ii,:] = defender - att
            acc += tmp
    else:
        for ii in range(0, N):
            acc[ii,:] = defender - attacker
    return np.mean(acc[:,0]), np.mean(acc[:,1])

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
    acc = np.zeros((N,2)) # used, wasted
    if type(attacker) is list:
        for att in attacker:
            tmp = np.zeros((N,2)) 
            for ii in range(0, N):
                tmp[ii,:] = defender - att
            acc += tmp
    else:
        for ii in range(0, N):
            acc[ii,:] = defender - attacker
    cdf, histogram = stats_comp(acc[:,0])
    cdf_waste, histogram_waste = stats_comp(acc[:,1])
    return cdf, histogram, acc[:,0], cdf_waste, histogram_waste, acc[:,1]

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

class AnalysisResult():
    def __init__(self, attacker, defender, damage_cdf, damage_sequence, waste_data, pvalue, desc=None):
        self.attacker = attacker
        self.defender = defender
        self.damage_cdf = damage_cdf
        self.damage_sequence = damage_sequence
        self.waste_data = waste_data
        self.pvalue = pvalue
        self.desc = desc
        
        def compute_likelihood_value(data, thresh):
            xdata = np.asarray([ float(x) for x in range(0,len(data)) ])
            return np.interp(thresh, data[::-1], xdata[::-1])

        self.very_likely_damage_output = compute_likelihood_value(damage_cdf, self.pvalue)
        self.expected_damage_output = compute_likelihood_value(damage_cdf, 0.5)
        self.expected_damage_waste = compute_likelihood_value(waste_data, 0.5)

        # potential relative to point cost
        self.att_points = attacker.points
        self.def_points = defender.points
        self.points_per_damage = 0 if self.very_likely_damage_output == 0 else self.att_points / self.very_likely_damage_output
        
        # models-removed-per-round and rounds-taken-to-remove-model
        self.cdf_rounds_taken, self.cdf_models_removed = fold_to_models_removed_stats(damage_sequence, defender)
        self.very_likely_number_of_rounds_taken = compute_likelihood_value(self.cdf_rounds_taken, self.pvalue)
        self.very_likely_models_removed = compute_likelihood_value(self.cdf_models_removed, self.pvalue)
        self.expected_models_removed = compute_likelihood_value(self.cdf_models_removed, 0.5)

    def __str__(self):
        result = f"================ {self.desc}"
        result += f"\n  {self.att_points} points attacking a target of {self.def_points} points"
        result += f"\n  {int(self.pvalue*100)}% chance {int(self.very_likely_damage_output)} or more damage is dealt."
        result += f"\n    Expected value for damage is {int(self.expected_damage_output)}."
        result += f"\n    Expected value for damage wasted is {int(self.expected_damage_waste)}."
        result += f"\n  {int(self.pvalue*100)}% chance {self.very_likely_number_of_rounds_taken:0.1f} rounds taken to remove a model."
        result += f"\n  {int(self.pvalue*100)}% chance {int(self.very_likely_models_removed)} models or more are removed in a single round."
        result += f"\n  {self.points_per_damage:0.2f} PPD"
        return result

def perform_full_analysis(attacker, defender, count, pvalue, description):
    damage_cdf, _, damage_sequence, waste_data, _, _ = stats_loop(attacker=attacker, defender=defender, count=count)
    return AnalysisResult(attacker=attacker, defender=defender, damage_cdf=damage_cdf, damage_sequence=damage_sequence, waste_data=waste_data, pvalue=pvalue, desc=description)

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
    ATT_POS_INCHES = 0
    WPN_RANGE_INCHES = 24

    TOUGHNESS = 5
    SAVE = 4
    WOUNDS = 6
    DEF_POS_INCHES = 2

    TestModelArmour = DStat(T=TOUGHNESS, Sv=SAVE, W=WOUNDS)
    TestModelGun = AStat(A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE, Range=WPN_RANGE_INCHES)
    TestModelVarD = AStat(A=ATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=VARDAMAGE, Range=WPN_RANGE_INCHES)
    TestModelVarA = AStat(A=VARATTACKS, BS_WS=SKILL, S=STRENGTH, AP=AP, D=DAMAGE, Range=WPN_RANGE_INCHES)

    test_def = Model(weapons=TestModelGun, defence=TestModelArmour, position=DEF_POS_INCHES)

    attackers = [
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) , 0.0833, 'Nominal' ),
        ( Model([TestModelGun, TestModelGun, TestModelGun], TestModelArmour, ATT_POS_INCHES) , 3*0.0833, 'Nominal*3' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * Torrent , 0.1667, 'Torrent' ),
        ( Model(TestModelVarD, TestModelArmour, ATT_POS_INCHES) , 2 * 0.0833, 'D3 Damage' ),
        ( Model(TestModelVarD, TestModelArmour, ATT_POS_INCHES) * DevestatingWounds, 0.25, 'D3 Damage with Devestating' ),
        ( Model(TestModelVarD, TestModelArmour, ATT_POS_INCHES) * Reroll_D3_Damage, 2.333333 * 0.0833, 'Rerolling D3 Damage'),
        ( Model(TestModelVarA, TestModelArmour, ATT_POS_INCHES) , 2 * 0.0833, 'D3 Attacks' ),
        ( Model(TestModelVarA, TestModelArmour, ATT_POS_INCHES) * Reroll_D3_Attacks, 2.333333 * 0.0833, 'Rerolling D3 Attacks' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * LethalHits , 0.1389, 'Lethal Hits' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * SustainedHits_1 , 0.1111, 'Sustained Hits 1' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * SustainedHits_1 * CriticalHit_5up, 0.1389, 'Sustained Hits 1, CritHit 5+' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * RerollHits , 0.125, 'Reroll Hits' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * RerollHitsOne , 0.0972, 'Reroll Hit Rolls of 1' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * RerollWounds , 0.1389, 'Reroll Wounds' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * RerollWoundsOne , 0.0972, 'Reroll Wound Rolls of 1' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * PlusOneToWound , 0.1250, '+1 to Wound' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * PlusOneToHit , 0.1111, '+1 to Hit' ),
        ( Model(TestModelGun, TestModelArmour, ATT_POS_INCHES) * RerollHits * RerollWounds , 0.2083, 'Full Rerolls' ),
    ]

    shooting_dis = abs(ATT_POS_INCHES - test_def.pos)
    TEST_COUNT=10000
    print(f"Context: Attacks=Damage=1 (unless noted otherwise), Hit=0.5, Wound=0.333, Save=0.5, WpnRange={WPN_RANGE_INCHES}, Range={shooting_dis}, MonteCarlo Count={TEST_COUNT}")
    for test_att, expected, details in attackers:
        done, _ = mean_loop(attacker=test_att, defender=test_def, count=TEST_COUNT)
        print(f"actual, expected: {done:0.4f}, {expected:0.4f}  ({details})")

    test_def.pos = 400
    shooting_dis = abs(ATT_POS_INCHES - test_def.pos)
    TEST_COUNT=10000
    print(f"Context: Attacks=Damage=1 (unless noted otherwise), Hit=0.5, Wound=0.333, Save=0.5, WpnRange={WPN_RANGE_INCHES}, Range={shooting_dis}, MonteCarlo Count={TEST_COUNT}")
    for test_att, expected, details in attackers:
        done, _ = mean_loop(attacker=test_att, defender=test_def, count=TEST_COUNT)
        print(f"actual, expected: {done:0.4f}, {expected:0.4f}  ({details})")

if __name__ == "__main__":
    run_test()