"""Step 6. Three ways to make the same run cheaper, measured on the good run and on a long run.

1. Quieter tools: the test tool stops listing the tests that passed.
2. Forgetting: results older than the last two are replaced by one short line before the request is sent.
3. The cache price: the start of each request repeats the request before it, and providers charge less for a repeat.
"""
import json

import agent
import meter
import tape
from save import save

STUB = '[old result removed to save space]'
loud_tests = agent.run_tests


def quiet_tests(folder):
    return '\n'.join(line for line in loud_tests(folder).splitlines() if not line.endswith('... ok'))


class Forgetful:
    """Sits between the loop and the model. The loop keeps everything; the model is sent a shorter copy."""

    def __init__(self, model, keep=2):
        self.model, self.keep = model, keep

    def next(self, messages, tools):
        results = [i for i, m in enumerate(messages) if m['role'] == 'tool']
        old = set(results[:-self.keep])
        return self.model.next([dict(m, content=STUB) if i in old else m for i, m in enumerate(messages)], tools)


def measure(reel, quiet=False, forget=False, loop=False, max_steps=20):
    agent.RUN['run_tests'] = quiet_tests if quiet else loud_tests
    base, folder = tape.fresh_project()
    metered = meter.Metered(tape.TapeModel(reel, loop=loop))
    _, ending = agent.run(Forgetful(metered) if forget else metered, tape.TASK, folder, max_steps=max_steps)
    passed = agent.run_tests(folder).splitlines()[-1]
    tape.clean(base)
    agent.RUN['run_tests'] = loud_tests
    return metered, ending, passed


price = [m for m in meter.load_prices()['models'] if m['id'] == 'claude-sonnet-5.5'][0]
rows = []
print('good run (7 calls), prices of %s' % price['name'])
print('%-28s tokens in   dollars   with cache price' % '')
for label, quiet, forget in (('as built', False, False), ('quiet tests', True, False), ('forgetting', False, True),
                             ('quiet tests and forgetting', True, True)):
    m, ending, passed = measure(tape.GOOD, quiet, forget)
    assert (ending, passed) == ('done', 'OK')
    row = {'label': label, 'in': m.tokens_in(), 'out': m.tokens_out(), 'plain': meter.bill(m.calls, price),
           'cached': meter.bill(m.calls, price, cache=True),
           'hit': sum(meter.repeated(m.calls[i - 1], m.calls[i]) for i in range(1, len(m.calls)))}
    rows.append(row)
    print('%-28s %9d   %.5f   %.5f' % (label, row['in'], row['plain'], row['cached']))
base_in = rows[0]['in']
base, folder = tape.fresh_project()
report = {'loud': meter.tokens(loud_tests(folder)), 'quiet': meter.tokens(quiet_tests(folder))}
tape.clean(base)
print('the first test report: %d tokens loud, %d tokens quiet' % (report['loud'], report['quiet']))
print('quiet tests save %d tokens on the run (%.0f%%)'
      % (base_in - rows[1]['in'], 100 * (base_in - rows[1]['in']) / base_in))
print('the cache price alone: %.0f%% off the bill' % (100 * (1 - rows[0]['cached'] / rows[0]['plain'])))
print('repeated tokens in the good run: %d of %d' % (rows[0]['hit'], base_in))

long_rows = []
print('\nlong run (40 steps, each step reads the same 474-token file)')
for label, forget in (('as built', False), ('forgetting', True)):
    m, ending, _ = measure(tape.STUCK, forget=forget, loop=True, max_steps=40)
    row = {'label': label, 'in': m.tokens_in(), 'last': m.calls[-1]['in'], 'plain': meter.bill(m.calls, price),
           'cached': meter.bill(m.calls, price, cache=True)}
    long_rows.append(row)
    print('%-28s %9d   %.5f   %.5f   last request %d tokens' % (label, row['in'], row['plain'], row['cached'], row['last']))

save(6, price=price, rows=rows, long=long_rows, quiet_saved=base_in - rows[1]['in'],
     report=report, stub=STUB, quiet_pct=round(100 * (base_in - rows[1]['in']) / base_in),
     cache_off_pct=round(100 * (1 - rows[0]['cached'] / rows[0]['plain'])))
