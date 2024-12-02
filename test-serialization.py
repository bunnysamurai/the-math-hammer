#!/usr/bin/env python

from math_hammer import perform_full_analysis, json_loads, json_dumps
import dill as pickle

from black_templars import the_emperors_champion_sweep, sword_brethern

VERY_LIKELY = 5/6.0
def run_test(attacker, defender):
    models_removed = {}
    damage_done = {}
    result = perform_full_analysis(attacker=attacker, defender=defender, count=1000, pvalue=VERY_LIKELY, description="test")
    models_removed[attacker.name] = result.very_likely_models_removed
    damage_done[attacker.name] = result.very_likely_damage_output


    def print_report(modl_dict, header):
        print(header)
        for k in modl_dict:
            print(f"{int(modl_dict[k]): 3d} : {k}")

    print_report(models_removed, f"{int(VERY_LIKELY*100)}% chance M models removed:")
    print_report(damage_done, f"{int(VERY_LIKELY*100)}% chance N damage done:")

print("===================================")
print("  PICKLE TEST ")
print("===================================")
# run test:
#   brother grammituis - champion
print("before")
run_test(the_emperors_champion_sweep, sword_brethern)

# serialize a list of stuff, say, the Black Templars library
champ_bytes = pickle.dumps(the_emperors_champion_sweep)
dread_bytes = pickle.dumps(sword_brethern)
# write it to disk, confirm it wrote
# read from disk and deserialize
# then, run test again:
#   brother grammituis - champion
print("after")
run_test(pickle.loads(champ_bytes), pickle.loads(dread_bytes))


# print("===================================")
# print("  JSON TEST ")
# print("===================================")
# # here we serialize to json and back
# champ_json = json_dumps(the_emperors_champion_sweep)
# dread_json = json_dumps(sword_brethern)

# print("should be human-readable. ish.")
# print(champ_json)
# print(dread_json)

# print("after")
# run_test(json_loads(champ_json), json_loads(dread_json))