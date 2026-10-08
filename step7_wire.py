"""Step 7. The same run over real HTTP. The client in agent.py sends requests to a stand-in provider on this
computer. Nothing leaves the machine. To rent a real model, only the address, the key and the name change."""
import urllib.error
import urllib.request

import agent
import local_server
import meter
import tape
from save import save

# The run from step 3, with the model called directly.
base, folder = tape.fresh_project()
direct, _ = agent.run(tape.TapeModel(tape.GOOD), tape.TASK, folder)
tape.clean(base)

# The same run through the network code.
address, log, stop = local_server.start(tape.GOOD)
base, folder = tape.fresh_project()
client = agent.ApiModel(address, 'local-test-key', 'tape')
wired, ending = agent.run(client, tape.TASK, folder)
tests = agent.run_tests(folder).splitlines()[-1]
tape.clean(base)

print('requests sent over HTTP: %d' % len(log))
print('bytes sent: %s  (sum %d)' % (' '.join(str(r['bytes']) for r in log), sum(r['bytes'] for r in log)))
print('run ends: %s, tests: %s' % (ending, tests))
print('same conversation as the direct run: %s' % (wired == direct))
tokens_in = sum(u['prompt_tokens'] for u in client.usage)
tokens_out = sum(u['completion_tokens'] for u in client.usage)
print('usage reported by the server: %d tokens in, %d tokens out' % (tokens_in, tokens_out))

# A request with no key is turned away.
try:
    urllib.request.urlopen(urllib.request.Request(address, b'{}', {'Content-Type': 'application/json'}))
    no_key = 'accepted'
except urllib.error.HTTPError as e:
    no_key = 'HTTP %d' % e.code
print('a request with no key: %s' % no_key)
stop()

save(7, requests=len(log), bytes=[r['bytes'] for r in log], total_bytes=sum(r['bytes'] for r in log), ending=ending,
     tests=tests, same=wired == direct, tokens_in=tokens_in, tokens_out=tokens_out, no_key=no_key,
     changes=['AGENT_URL', 'AGENT_KEY', 'AGENT_MODEL'])
