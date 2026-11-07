"""PIE: natural-movement audit of every person on the island. Two samples 0.6 s apart: a person that moved
more than 25 cm while feet and hands kept the same offsets to the body (< 1.5 cm) is gliding. Prints the list."""
import sys, time, json
sys.argv = ['x']
exec(open('party_pie.py').read().split('def shot')[0])
if 'true' not in call('EditorToolset.EditorAppToolset', 'IsPIERunning', {}).lower():
    call('EditorToolset.EditorAppToolset', 'StartPIE', {'options': {'bSimulate': False}})
    time.sleep(45)
rounds = int(sys.argv_rounds) if hasattr(sys, 'argv_rounds') else 3
moving, gliding = {}, {}
for r in range(rounds):
    a = hud('gait')
    time.sleep(.6)
    b = hud('gait')
    pa = {x[0]: x for x in a}
    for x in b:
        o = pa.get(x[0])
        if not o or x[5]:
            continue
        moved = ((x[2][0] - o[2][0]) ** 2 + (x[2][1] - o[2][1]) ** 2) ** .5
        if moved < 25:
            continue
        limbs = max(abs(u - v) for u, v in zip(x[3], o[3]))
        moving[x[0]] = (x[1], x[4] or 'quaternius')
        if limbs < 1.5:
            gliding[x[0]] = (x[1], x[4] or 'quaternius', x[2], round(moved), round(limbs, 2))
    time.sleep(2)
print('people sampled:', len(b), '| moving:', len(moving), '| gliding:', len(gliding))
for k, v in gliding.items():
    print('GLIDE', k, v)
json.dump({'moving': moving, 'gliding': gliding}, open('D:/CodexTemp/beach/gait_audit.json', 'w'), ensure_ascii=False, indent=1)
