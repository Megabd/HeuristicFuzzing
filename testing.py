import fuzzer
import json5

accepted = 0

for i in range(100):
    generated = fuzzer.baseLineFuzz()
    try:
        json5.loads(generated)
        accepted += 1
    except ValueError:
        print("Rejected:", generated)
print("Accepted:", accepted, "/ 100")