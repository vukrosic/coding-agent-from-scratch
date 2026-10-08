"""Step 3. The loop. The stand-in model plays the good tape; the tools and the tests are real."""
import difflib
import os

import agent
import tape
from save import save

base, folder = tape.fresh_project()
before = agent.read_file(folder, 'cart.py')
tests_before = agent.run_tests(folder).splitlines()[-1]

log = []


def show(step, reply):
    calls = reply.get('tool_calls') or []
    what = calls[0]['function']['name'] if calls else 'finished'
    log.append({'step': step, 'tool': what, 'thought': reply.get('content') or ''})
    print('%d  %-10s %s' % (step, what, reply.get('content') or ''))


conversation, ending = agent.run(tape.TapeModel(tape.GOOD), tape.TASK, folder, show=show)

after = agent.read_file(folder, 'cart.py')
tests_after = agent.run_tests(folder).splitlines()[-1]
diff = [line for line in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm='', n=0)
        if line[:1] in '+-' and line[:3] not in ('+++', '---')]
others = all(open(os.path.join(folder, name)).read() == open(os.path.join(tape.HERE, 'bugshop', name)).read()
             for name in ('test_cart.py', 'test_inventory.py', 'inventory.py', 'README.md'))

print('\nending: %s after %d calls to the model, %d messages in the conversation' % (ending, len(log), len(conversation)))
print('tests before: %s   tests after: %s' % (tests_before, tests_after))
print('\n'.join(diff))
print('every other file unchanged:', others)

tape.clean(base)
save(3, log=log, ending=ending, calls=len(log), messages=len(conversation), tests_before=tests_before,
     tests_after=tests_after, diff=diff, others=others)
