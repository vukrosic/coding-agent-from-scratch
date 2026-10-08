"""A stand-in provider on this computer. It answers POST /v1/chat/completions in the same JSON form a rented model
uses, but the replies come from a tape. It lets the real client in agent.py be tested for free.

    python3 local_server.py          # then, in another window, the command it prints
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import meter
import tape


def start(reel, port=0):
    """Start the server in the background. Returns (address, log, stop)."""
    model = tape.TapeModel(reel)
    log = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            if self.path != '/v1/chat/completions' or not self.headers.get('Authorization', '').startswith('Bearer '):
                self.send_response(401 if self.path == '/v1/chat/completions' else 404)
                self.end_headers()
                return
            request = json.loads(raw)
            reply = model.next(request['messages'], request['tools'])
            counted = {'prompt_tokens': meter.request_tokens(request['messages'], request['tools']),
                       'completion_tokens': meter.message_tokens(reply)}
            counted['total_tokens'] = sum(counted.values())
            log.append({'bytes': len(raw), 'messages': len(request['messages']), 'usage': counted})
            answer = json.dumps({'id': 'local-%d' % len(log), 'object': 'chat.completion', 'model': request['model'],
                                 'choices': [{'index': 0, 'message': reply,
                                              'finish_reason': 'tool_calls' if reply.get('tool_calls') else 'stop'}],
                                 'usage': counted}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(answer)))
            self.end_headers()
            self.wfile.write(answer)

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return 'http://127.0.0.1:%d/v1/chat/completions' % server.server_address[1], log, server.shutdown


if __name__ == '__main__':
    base, folder = tape.fresh_project()
    address, _, _ = start(tape.GOOD, port=8765)
    print('a copy of the broken project is in %s' % folder)
    print('run this in another window:\n')
    print('AGENT_URL=%s AGENT_KEY=local AGENT_MODEL=tape python3 agent.py %s "%s"\n' % (address, folder, tape.TASK))
    print('ctrl-c stops the server')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        tape.clean(base)
