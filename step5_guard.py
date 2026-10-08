"""Step 5. The model's text is not trusted. Three bad tapes: one tries to leave the folder, one makes a wrong edit,
one never stops. Plus a request for a tool that does not exist."""
import hashlib
import os

import agent
import meter
import tape
from save import save

# 1. Leaving the folder.
base, folder = tape.fresh_project()
secret = os.path.join(base, 'secret.txt')
reel = [dict(r) for r in tape.ESCAPE]
reel[1] = tape.ask(2, 'I will try the full path.', 'read_file', path=secret)
conversation, _ = agent.run(tape.TapeModel(reel), tape.TASK, folder)
escape = [m['content'].replace(base, '/tmp/agent') for m in conversation if m['role'] == 'tool']
unguarded = open(os.path.join(folder, '../secret.txt')).read().strip()      # what a tool with no check would return
print('1. the model asks for ../secret.txt and for the full path')
for line in escape:
    print('   ' + line)
print('   the same request with no check returns: %s' % unguarded)

# 2. A tool that does not exist.
ghost = agent.use_tool(folder, {'function': {'name': 'run_shell', 'arguments': '{"command": "rm -rf ~"}'}})
print('2. the model asks for run_shell: %s' % ghost)
tape.clean(base)

# 3. A wrong edit. The error is text; the model reads it and tries again.
base, folder = tape.fresh_project()
slip = meter.Metered(tape.TapeModel(tape.SLIP))
marks = []


def watch(step, reply):
    marks.append(hashlib.md5(open(os.path.join(folder, 'cart.py'), 'rb').read()).hexdigest())


conversation, ending = agent.run(slip, tape.TASK, folder, show=watch)
error = [m['content'] for m in conversation if m['role'] == 'tool' and m['content'].startswith('ERROR')][0]
tests = agent.run_tests(folder).splitlines()[-1]
tape.clean(base)
print('3. wrong edit: %s' % error)
print('   file untouched by the failed edit: %s' % (marks[3] == marks[4]))
print('   run ends: %s, tests: %s, %d calls, %d tokens in' % (ending, tests, len(slip.calls), slip.tokens_in()))

base, folder = tape.fresh_project()
good = meter.Metered(tape.TapeModel(tape.GOOD))
agent.run(good, tape.TASK, folder)
tape.clean(base)
extra = slip.tokens_in() - good.tokens_in()
print('   the good run: %d calls, %d tokens in. One slip costs %d more tokens (%.0f%% more)'
      % (len(good.calls), good.tokens_in(), extra, 100 * extra / good.tokens_in()))

# 4. A model that never finishes.
runs = []
for cap in (20, 100):
    base, folder = tape.fresh_project()
    stuck = meter.Metered(tape.TapeModel(tape.STUCK, loop=True))
    _, ending = agent.run(stuck, tape.TASK, folder, max_steps=cap)
    tape.clean(base)
    runs.append({'cap': cap, 'ending': ending, 'in': stuck.tokens_in(), 'out': stuck.tokens_out()})
    print('4. stuck model, limit %3d: %s, %d tokens in (%.0f good runs)'
          % (cap, ending, stuck.tokens_in(), stuck.tokens_in() / good.tokens_in()))

save(5, escape=escape, unguarded=unguarded, ghost=ghost, error=error, untouched=marks[3] == marks[4],
     slip_calls=len(slip.calls), slip_in=slip.tokens_in(), slip_tests=tests, good_in=good.tokens_in(), extra=extra,
     extra_pct=round(100 * extra / good.tokens_in()), stuck=runs, tool_count=len(agent.TOOLS))
