"""Counting tokens and money without calling anyone.

Tokens are counted with tiktoken (the open tokenizer cl100k_base). Every provider counts a little differently;
a real API reports its own count in each reply. Without tiktoken installed, the count falls back to characters / 4.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(os.path.join(HERE, '.tok')):
    os.environ.setdefault('TIKTOKEN_CACHE_DIR', os.path.join(HERE, '.tok'))

try:
    import tiktoken
    _enc = tiktoken.get_encoding('cl100k_base')
    EXACT = True

    def tokens(text):
        return len(_enc.encode(text))
except Exception:                                       # no tiktoken, or no way to fetch its word list
    EXACT = False

    def tokens(text):
        return (len(text) + 3) // 4


def message_tokens(message):
    """The text of one message: who speaks, what they say, and any tool request."""
    n = tokens(message['role']) + tokens(message.get('content') or '')
    for call in message.get('tool_calls') or []:
        n += tokens(call['function']['name']) + tokens(call['function']['arguments'])
    return n


def request_tokens(messages, tools):
    return tokens(json.dumps(tools)) + sum(message_tokens(m) for m in messages)


class Metered:
    """Wraps any model and writes down, for every call, how much went in and how much came out."""

    def __init__(self, model):
        self.model, self.calls = model, []

    def next(self, messages, tools):
        sent = [message_tokens(m) for m in messages]
        reply = self.model.next(messages, tools)
        self.calls.append({'tools': tokens(json.dumps(tools)), 'sent': sent, 'in': tokens(json.dumps(tools)) + sum(sent),
                           'out': message_tokens(reply), 'text': [json.dumps(m, sort_keys=True) for m in messages]})
        return reply

    def tokens_in(self):
        return sum(c['in'] for c in self.calls)

    def tokens_out(self):
        return sum(c['out'] for c in self.calls)


def load_prices():
    with open(os.path.join(HERE, 'prices.json')) as f:
        return json.load(f)


def repeated(before, now):
    """Tokens at the start of this request that are word for word the start of the request before it."""
    same = now['tools']
    for old, new, size in zip(before['text'], now['text'], now['sent']):
        if old != new:
            break
        same += size
    return same


def bill(calls, price, cache=False):
    """Dollars for a list of metered calls. Price lists are per million tokens.

    With cache=True the repeated start of each request is charged at the cache price and the rest at the price
    for text the provider stores. This is arithmetic on a price list: it assumes every repeat is found in the cache.
    """
    total = 0.0
    for i, call in enumerate(calls):
        hit = repeated(calls[i - 1], call) if cache and i else 0
        fresh = call['in'] - hit
        total += hit * price['hit'] + fresh * (price['write'] if cache else price['in']) + call['out'] * price['out']
    return total / 1e6
