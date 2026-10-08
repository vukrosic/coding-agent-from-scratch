"""A coding agent in one file: four tools, a sandbox, a loop, and one function that asks a model what to do next.

    python3 agent.py <project folder> "<task>"

The model is not in this file. It is rented: set AGENT_URL, AGENT_KEY and AGENT_MODEL to a provider's address,
your key and a model name. Every step in this repo runs without them, against a stand-in (tape.py).
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

SYSTEM = ('You are a coding agent working inside one project folder. Use the tools to look at the files, '
          'change them and run the tests. Do not change the tests. When every test passes, answer with a '
          'short summary and no tool call.')


# ---- 1. the tools: what the model is allowed to ask for ----------------------------------------------------

def describe(name, description, **params):
    """One tool in the form the API expects: a name, a sentence, and the arguments it takes."""
    return {'type': 'function', 'function': {
        'name': name, 'description': description,
        'parameters': {'type': 'object', 'required': list(params),
                       'properties': {p: {'type': 'string', 'description': d} for p, d in params.items()}}}}


TOOLS = [
    describe('list_files', 'List every file in the project folder with its size in bytes.'),
    describe('read_file', 'Return the full text of one file.', path='Path inside the project folder.'),
    describe('edit_file', 'Replace one exact piece of text in a file. The old text must appear exactly once.',
             path='Path inside the project folder.', old='The exact text to replace.', new='The new text.'),
    describe('run_tests', 'Run the project tests and return what they print.'),
]


class ToolError(Exception):
    pass


def inside(folder, path):
    """The sandbox: turn a path from the model into a real path, and refuse it if it leaves the folder."""
    root = os.path.realpath(folder)
    full = os.path.realpath(os.path.join(root, path))
    if full != root and not full.startswith(root + os.sep):
        raise ToolError('%s is outside the project folder' % path)
    return full


def list_files(folder):
    found = []
    for here, dirs, files in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if not d.startswith(('.', '__')))
        for name in sorted(files):
            full = os.path.join(here, name)
            found.append('%s  %d bytes' % (os.path.relpath(full, folder), os.path.getsize(full)))
    return '\n'.join(found)


def read_file(folder, path):
    full = inside(folder, path)
    if not os.path.isfile(full):
        raise ToolError('no file called %s' % path)
    with open(full) as f:
        return f.read()


def edit_file(folder, path, old, new):
    text = read_file(folder, path)
    seen = text.count(old)
    if seen != 1:
        raise ToolError('the old text appears %d times in %s, it must appear once; nothing was changed'
                        % (seen, path))
    with open(inside(folder, path), 'w') as f:
        f.write(text.replace(old, new))
    return 'edited %s' % path


def run_tests(folder):
    """The only command the agent can run. The model does not get a shell."""
    try:
        done = subprocess.run([sys.executable, '-m', 'unittest', '-v'], cwd=folder, capture_output=True, text=True,
                              timeout=60, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    except subprocess.TimeoutExpired:
        raise ToolError('the tests ran for more than 60 seconds and were stopped')
    out = (done.stdout + done.stderr).replace(os.path.realpath(folder) + os.sep, '')
    return re.sub(r' in [0-9.]+s', '', out).strip()


RUN = {'list_files': list_files, 'read_file': read_file, 'edit_file': edit_file, 'run_tests': run_tests}


def use_tool(folder, call):
    """Run one request from the model. A mistake becomes text the model can read, never a crash."""
    try:
        args = json.loads(call['function']['arguments'] or '{}')
        return RUN[call['function']['name']](folder, **args)
    except KeyError as e:
        return 'ERROR: no tool called %s' % e
    except (ToolError, TypeError, ValueError, OSError) as e:
        return 'ERROR: %s' % e


# ---- 2. the loop ---------------------------------------------------------------------------------------------

def run(model, task, folder, max_steps=20, show=None):
    """Ask, act, write the result down, ask again. Returns the whole conversation and why it ended."""
    messages = [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': task}]
    for step in range(1, max_steps + 1):
        reply = model.next(messages, TOOLS)             # the one line that costs money
        messages.append(reply)
        calls = reply.get('tool_calls') or []
        if show:
            show(step, reply)
        if not calls:
            return messages, 'done'
        for call in calls:
            result = use_tool(folder, call)
            messages.append({'role': 'tool', 'tool_call_id': call['id'], 'content': result})
    return messages, 'stopped at the step limit'


# ---- 3. the rented part: one request over the internet -------------------------------------------------------

class ApiModel:
    """Sends the conversation to a chat-completions address and returns the model's reply."""

    def __init__(self, url, key, name):
        self.url, self.key, self.name = url, key, name
        self.usage = []                                 # what the provider says it counted, per call

    def next(self, messages, tools):
        body = json.dumps({'model': self.name, 'messages': messages, 'tools': tools}).encode()
        request = urllib.request.Request(self.url, body, {'Content-Type': 'application/json',
                                                          'Authorization': 'Bearer ' + self.key})
        with urllib.request.urlopen(request, timeout=300) as answer:
            data = json.load(answer)
        self.usage.append(data.get('usage', {}))
        return data['choices'][0]['message']


def narrate(step, reply):
    for call in reply.get('tool_calls') or []:
        print('%2d  %s %s' % (step, call['function']['name'], call['function']['arguments']))
    if reply.get('content'):
        print('%2d  %s' % (step, reply['content']))


if __name__ == '__main__':
    if len(sys.argv) != 3 or not os.environ.get('AGENT_URL'):
        sys.exit('usage: AGENT_URL=... AGENT_KEY=... AGENT_MODEL=... python3 agent.py <project folder> "<task>"')
    rented = ApiModel(os.environ['AGENT_URL'], os.environ.get('AGENT_KEY', ''), os.environ.get('AGENT_MODEL', ''))
    conversation, ending = run(rented, sys.argv[2], sys.argv[1], show=narrate)
    print(ending, '|', sum(u.get('prompt_tokens', 0) for u in rented.usage), 'tokens in,',
          sum(u.get('completion_tokens', 0) for u in rented.usage), 'tokens out')
