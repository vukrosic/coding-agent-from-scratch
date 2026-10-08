"""The stand-in for the model. No money is spent anywhere in this repo: the replies come from tapes written by hand.

A tape is a list of replies in the exact form a chat-completions API returns them. The agent cannot tell a tape
from a rented model, and step 7 shows it over real HTTP.
"""
import json
import os
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = 'Two tests in this project fail. Find out why and fix the code so that every test passes.'


def ask(n, thought, tool, **args):
    """A reply that asks for one tool: a sentence of reasoning plus the request."""
    return {'role': 'assistant', 'content': thought, 'tool_calls': [
        {'id': 'call_%d' % n, 'type': 'function', 'function': {'name': tool, 'arguments': json.dumps(args)}}]}


def say(text):
    """A reply with no tool request: the model is finished."""
    return {'role': 'assistant', 'content': text}


FIX_QUANTITY = dict(path='cart.py',
                    old='return sum(price for name, price, quantity in self.items)',
                    new='return sum(price * quantity for name, price, quantity in self.items)')
FIX_SHIPPING = dict(path='cart.py', old='if after > FREE_SHIPPING_FROM:', new='if after >= FREE_SHIPPING_FROM:')
SUMMARY = ('Fixed two bugs in cart.py. subtotal() ignored the quantity of each item, and shipping() charged an '
           'order of exactly 50.00. All 14 tests pass now.')

# The good run: look, test, read, fix, fix, test, report.
GOOD = [
    ask(1, 'I will look at what is in the project first.', 'list_files'),
    ask(2, 'Now I run the tests to see which ones fail.', 'run_tests'),
    ask(3, 'Both failing tests are about the cart. I will read cart.py.', 'read_file', path='cart.py'),
    ask(4, 'subtotal() adds the price once and ignores the quantity. Two mugs must cost 1600.', 'edit_file',
        **FIX_QUANTITY),
    ask(5, 'shipping() uses > so an order of exactly 5000 still pays. The comment says 50.00 or more is free.',
        'edit_file', **FIX_SHIPPING),
    ask(6, 'Both fixes are in. I run the tests again.', 'run_tests'),
    say(SUMMARY),
]

# A reply that tries to leave the project folder.
ESCAPE = [
    ask(1, 'I will check the folder above for settings.', 'read_file', path='../secret.txt'),
    ask(2, 'I will try the full path.', 'read_file', path='@SECRET@'),
    say('I could not read outside the project.'),
]

# A reply with a wrong edit: the old text is not in the file. The error goes back and the next reply repairs it.
SLIP = GOOD[:3] + [
    ask(4, 'subtotal() ignores the quantity. I will fix the line.', 'edit_file', path='cart.py',
        old='return sum(price for item in self.items)', new=FIX_QUANTITY['new']),
    ask(5, 'The edit failed because my old text was not exact. I copy the line as it is in the file.', 'edit_file',
        **FIX_QUANTITY),
    ask(6, GOOD[4]['content'], 'edit_file', **FIX_SHIPPING),
    ask(7, GOOD[5]['content'], 'run_tests'),
    say(SUMMARY),
]

# A model that never finishes: it reads the same file again and again.
STUCK = [ask(1, 'I will read cart.py again to be sure.', 'read_file', path='cart.py')]


class TapeModel:
    """Plays a tape, one reply per call. With loop=True the tape starts over when it ends."""

    def __init__(self, tape, loop=False):
        self.tape, self.loop, self.calls = tape, loop, 0

    def next(self, messages, tools):
        reply = self.tape[self.calls % len(self.tape)] if self.loop else self.tape[self.calls]
        self.calls += 1
        reply = json.loads(json.dumps(reply))           # a fresh copy, as if it came over the wire
        for call in reply.get('tool_calls') or []:
            call['id'] = 'call_%d' % self.calls
        return reply


def fresh_project():
    """A new copy of the broken project in a temporary folder, with one file placed outside it."""
    base = tempfile.mkdtemp(prefix='agent-')
    folder = os.path.join(base, 'bugshop')
    shutil.copytree(os.path.join(HERE, 'bugshop'), folder, ignore=shutil.ignore_patterns('__pycache__'))
    with open(os.path.join(base, 'secret.txt'), 'w') as f:
        f.write('PAYMENT_KEY=this-is-a-made-up-key-for-the-test\n')
    return base, folder


def clean(base):
    shutil.rmtree(base)
