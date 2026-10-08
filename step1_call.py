"""Step 1. What you send, and what comes back. Nothing is sent here: the request is built and measured."""
import json

import agent
import meter
import tape
from save import save

messages = [{'role': 'system', 'content': agent.SYSTEM}, {'role': 'user', 'content': tape.TASK}]
request = {'model': 'any-model', 'messages': messages, 'tools': agent.TOOLS}
body = json.dumps(request)

parts = {'instructions': meter.message_tokens(messages[0]), 'task': meter.message_tokens(messages[1]),
         'tools': meter.tokens(json.dumps(agent.TOOLS))}
first = sum(parts.values())
print('request 1: %d bytes of text' % len(body))
print('  instructions %4d tokens' % parts['instructions'])
print('  the task     %4d tokens' % parts['task'])
print('  4 tool notes %4d tokens' % parts['tools'])
print('  total        %4d tokens' % first)

reply = tape.TapeModel(tape.GOOD).next(messages, agent.TOOLS)
print('reply 1: %s' % json.dumps(reply)[:150])
print('  %d tokens' % meter.message_tokens(reply))

base, folder = tape.fresh_project()
result = agent.use_tool(folder, reply['tool_calls'][0])
tape.clean(base)
messages += [reply, {'role': 'tool', 'tool_call_id': reply['tool_calls'][0]['id'], 'content': result}]
second = meter.request_tokens(messages, agent.TOOLS)
print('request 2: everything in request 1 again, plus the reply, plus the result')
print('  total        %4d tokens, of which %d are new' % (second, second - first))

save(1, bytes1=len(body), parts=parts, first=first, reply1=meter.message_tokens(reply), second=second,
     new=second - first, exact=meter.EXACT, tool_names=[t['function']['name'] for t in agent.TOOLS],
     agent_lines=sum(1 for _ in open(agent.__file__)))
