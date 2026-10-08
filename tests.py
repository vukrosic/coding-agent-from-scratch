"""Checks. run_all.sh runs them last: some on the tools directly, some on the numbers the eight steps saved in runs/."""
import json
import os
import subprocess
import sys

import agent
import local_server
import meter
import tape

HERE = os.path.dirname(os.path.abspath(__file__))
r = {i: json.load(open(os.path.join(HERE, 'runs', 'step%d.json' % i))) for i in range(1, 9)}

# the sandbox: nothing outside the folder can be read or written, by any spelling of the path
base, folder = tape.fresh_project()
for path in ('../secret.txt', '../../etc/hosts', os.path.join(base, 'secret.txt'), '/etc/hosts', 'x/../../secret.txt'):
    for attempt in (lambda: agent.read_file(folder, path), lambda: agent.edit_file(folder, path, 'a', 'b')):
        try:
            attempt()
            raise SystemExit('sandbox let %s through' % path)
        except agent.ToolError:
            pass
os.symlink(os.path.join(base, 'secret.txt'), os.path.join(folder, 'link.txt'))      # a link that points outside
try:
    agent.read_file(folder, 'link.txt')
    raise SystemExit('sandbox followed a link out of the folder')
except agent.ToolError:
    pass
os.remove(os.path.join(folder, 'link.txt'))

# an edit must match exactly once, and a failed edit changes nothing
before = agent.read_file(folder, 'cart.py')
for old in ('not in the file', 'self.items'):                    # zero matches, many matches
    assert agent.use_tool(folder, {'function': {'name': 'edit_file', 'arguments': json.dumps(
        {'path': 'cart.py', 'old': old, 'new': 'x'})}}).startswith('ERROR')
assert agent.read_file(folder, 'cart.py') == before
# broken requests become text, not crashes
assert agent.use_tool(folder, {'function': {'name': 'read_file', 'arguments': 'not json'}}).startswith('ERROR')
assert agent.use_tool(folder, {'function': {'name': 'read_file', 'arguments': '{}'}}).startswith('ERROR')
assert agent.use_tool(folder, {'function': {'name': 'run_shell', 'arguments': '{}'}}).startswith('ERROR')
tape.clean(base)

# the command-line program works end to end against the local stand-in
address, log, stop = local_server.start(tape.GOOD)
base, folder = tape.fresh_project()
done = subprocess.run([sys.executable, os.path.join(HERE, 'agent.py'), folder, tape.TASK], capture_output=True, text=True,
                      env=dict(os.environ, AGENT_URL=address, AGENT_KEY='local', AGENT_MODEL='tape'))
assert done.returncode == 0 and 'done | 7220 tokens in, 235 tokens out' in done.stdout or not meter.EXACT, done.stdout
assert agent.run_tests(folder).splitlines()[-1] == 'OK' and len(log) == 7
tape.clean(base)
stop()

# step 1: the second request contains the first
assert r[1]['second'] > r[1]['first'] and r[1]['first'] == sum(r[1]['parts'].values())
# step 2 and 3: two tests fail before, none after, and only two lines of one file changed
assert r[2]['ran'] == 14 and len(r[2]['failed']) == 2
assert r[3]['tests_before'] == 'FAILED (failures=2)' and r[3]['tests_after'] == 'OK'
assert len(r[3]['diff']) == 4 and r[3]['others'] and r[3]['calls'] == 7
# step 4: every token sent is accounted for; the requests only grow; twice the steps is about four times the tokens
assert sum(p['tokens'] * p['times'] for p in r[4]['pieces']) == r[4]['tokens_in'] == sum(c['in'] for c in r[4]['calls'])
assert all(a['in'] < b['in'] for a, b in zip(r[4]['calls'], r[4]['calls'][1:]))
assert all(3.7 < b['in'] / a['in'] < 4.1 for a, b in zip(r[4]['growth'], r[4]['growth'][1:]))
# step 5: both escapes refused, the slip repaired, the stuck run stopped at its limit
assert all(line.startswith('ERROR') for line in r[5]['escape']) and r[5]['untouched'] and r[5]['slip_tests'] == 'OK'
assert all(run['ending'] == 'stopped at the step limit' for run in r[5]['stuck'])
# step 6: forgetting sends fewer tokens, but with the cache price it costs more than not forgetting
plain, quiet, forget = r[6]['rows'][0], r[6]['rows'][1], r[6]['rows'][2]
assert forget['in'] < quiet['in'] < plain['in'] and forget['plain'] < plain['plain']
assert forget['cached'] > plain['cached'] and r[6]['long'][1]['cached'] > r[6]['long'][0]['cached']
# step 7: the run over HTTP is the same run
assert r[7]['same'] and r[7]['requests'] == 7 and r[7]['tokens_in'] == r[4]['tokens_in'] and r[7]['no_key'] == 'HTTP 401'
# step 8: the bill is tokens times price
first = r[8]['rows'][0]
assert abs(first['fix'] - (r[8]['tokens_in'] * first['in'] + r[8]['tokens_out'] * first['out']) / 1e6) < 1e-12

print('all checks passed')
