"""Step 8. The same conversation on four price lists. Token counts are from this repo's runs; prices were read from
each maker's public price page on the date in prices.json. No model was called: this is counted text times a price."""
import agent
import meter
import tape
from save import save


def metered(reel, loop=False, max_steps=20):
    base, folder = tape.fresh_project()
    model = meter.Metered(tape.TapeModel(reel, loop=loop))
    agent.run(model, tape.TASK, folder, max_steps=max_steps)
    tape.clean(base)
    return model


prices = meter.load_prices()
good = metered(tape.GOOD)
stuck = metered(tape.STUCK, loop=True, max_steps=100)

print('prices read %s, %s' % (prices['read'], prices['unit']))
print('one fix: %d tokens in, %d tokens out' % (good.tokens_in(), good.tokens_out()))
print('%-20s %6s %6s %6s | %9s %9s | %12s | %10s' % ('model', 'in', 'repeat', 'out', 'one fix', 'cached', '1,000 fixes', 'stuck 100'))
rows = []
for p in prices['models']:
    row = {'id': p['id'], 'name': p['name'], 'maker': p['maker'], 'in': p['in'], 'hit': p['hit'], 'out': p['out'],
           'fix': meter.bill(good.calls, p), 'fix_cached': meter.bill(good.calls, p, cache=True),
           'stuck': meter.bill(stuck.calls, p), 'stuck_cached': meter.bill(stuck.calls, p, cache=True)}
    row['thousand'] = row['fix'] * 1000
    row['thousand_cached'] = row['fix_cached'] * 1000
    rows.append(row)
    print('%-20s %6.2f %6.3f %6.2f | $%.5f $%.5f | $%5.2f $%5.2f | $%.2f' % (
        p['name'], p['in'], p['hit'], p['out'], row['fix'], row['fix_cached'], row['thousand'],
        row['thousand_cached'], row['stuck']))

share_in = good.tokens_in() * prices['models'][0]['in'] / (good.tokens_in() * prices['models'][0]['in']
                                                           + good.tokens_out() * prices['models'][0]['out'])
print('\nshare of the bill that is input, on the first list: %.0f%%' % (100 * share_in))
print('dearest to cheapest for one fix: %.0f times' % (max(r['fix'] for r in rows) / min(r['fix'] for r in rows)))

save(8, read=prices['read'], rows=rows, tokens_in=good.tokens_in(), tokens_out=good.tokens_out(),
     stuck_in=stuck.tokens_in(), share_in=round(100 * share_in),
     spread=round(max(r['fix'] for r in rows) / min(r['fix'] for r in rows)))
