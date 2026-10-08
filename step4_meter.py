"""Step 4. The meter. How many tokens the good run sends, call by call, and why the sum is so large."""
import agent
import meter
import tape
from save import save


def metered_run(reel, loop=False, max_steps=20):
    base, folder = tape.fresh_project()
    model = meter.Metered(tape.TapeModel(reel, loop=loop))
    conversation, ending = agent.run(model, tape.TASK, folder, max_steps=max_steps)
    tape.clean(base)
    return model, conversation, ending


model, conversation, ending = metered_run(tape.GOOD)
tools = model.calls[0]['tools']
once = tools + sum(meter.message_tokens(m) for m in conversation)

print('call   tokens in   tokens out')
for i, call in enumerate(model.calls, 1):
    print('%4d %11d %12d' % (i, call['in'], call['out']))
print('sum  %11d %12d' % (model.tokens_in(), model.tokens_out()))
print('\nall the text of the run, counted once: %d tokens' % once)
print('tokens sent to the model:              %d  (%.1f times as many)' % (model.tokens_in(), model.tokens_in() / once))

# How often was each piece sent? A message that exists at call k is sent in every call from k to the end.
names = ['instructions', 'the task']
for m in conversation[2:]:
    if m['role'] == 'tool':
        names.append('result: ' + last)
    else:
        last = (m.get('tool_calls') or [{'function': {'name': 'summary'}}])[0]['function']['name']
        names.append('reply:  ' + last)
pieces = [{'name': 'tool notes', 'tokens': tools, 'times': len(model.calls)}]
for index, m in enumerate(conversation):
    times = sum(1 for call in model.calls if len(call['sent']) > index)
    pieces.append({'name': names[index], 'tokens': meter.message_tokens(m), 'times': times})
print('\npiece                  tokens  sent  paid')
for p in pieces:
    print('%-22s %6d %5d %5d' % (p['name'], p['tokens'], p['times'], p['tokens'] * p['times']))
assert sum(p['tokens'] * p['times'] for p in pieces) == model.tokens_in()

kinds = {'tool notes': tools * len(model.calls), 'instructions and task': 0, 'results': 0, 'replies': 0}
for p in pieces[1:]:
    key = 'instructions and task' if p['name'] in names[:2] else 'results' if p['name'].startswith('result') else 'replies'
    kinds[key] += p['tokens'] * p['times']
print('\nwhere the %d tokens go:' % model.tokens_in(), kinds)

# Longer runs. The stuck tape reads the same file at every step, so each step adds the same amount of text.
growth = []
print('\nsteps   tokens in   compared with half as many steps')
for steps in (5, 10, 20, 40, 80):
    stuck, _, _ = metered_run(tape.STUCK, loop=True, max_steps=steps)
    growth.append({'steps': steps, 'in': stuck.tokens_in(), 'last': stuck.calls[-1]['in']})
    ratio = '' if len(growth) < 2 else '%.1f times' % (growth[-1]['in'] / growth[-2]['in'])
    print('%5d %11d   %s' % (steps, stuck.tokens_in(), ratio))

cart = [p for p in pieces if p['name'] == 'result: read_file'][0]
save(4, calls=[{'in': c['in'], 'out': c['out']} for c in model.calls], tokens_in=model.tokens_in(),
     tokens_out=model.tokens_out(), once=once, ratio=round(model.tokens_in() / once, 2), pieces=pieces, kinds=kinds,
     growth=growth, cart=cart, tools=tools)
