import fuzzer
import json5
import tomllib

is_json5 = True
accepted = 0
rejected = 0
crashes = 0

for i in range(10000):
    generated = fuzzer.heuristicFuzz(is_json5)

    try:
        if is_json5:
            json5.loads(generated)
        else:
            tomllib.loads(generated)
        accepted += 1

    except ValueError as e:
        rejected += 1
        print("Rejected:", repr(generated), "| Reason:", e)

    except Exception as e:
        crashes += 1
        print("CRASH:", repr(generated), "| Error:", type(e).__name__, e)

print("Accepted:", accepted)
print("Rejected:", rejected)
print("Crashes:", crashes)