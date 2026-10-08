# Coding agent from scratch

Code for the video **I Built a Coding Agent in 157 Lines. Here Is the Bill.**

`agent.py` is a whole coding agent: a loop, four tools (list files, read a file, edit a file, run the tests) and a
client for any chat-completions API. `bugshop/` is a small shop project with 14 tests, 2 of them failing. Python 3,
standard library only. `tiktoken` is optional: with it the token counts are exact for the `cl100k_base` word list,
without it they are estimated as characters / 4.

```bash
./run_all.sh          # the eight steps and the checks, about 10 seconds; expected output is in demo-output.txt
```

**Nothing here calls a real model or costs money.** In every step the "model" is a tape: replies written by hand in
`tape.py`, in the same form a provider sends. The files, the test runs, the fences and the token counts are real. How
many steps a real model needs, and whether it fixes the bug, is not measured here.

| File | Idea | What the run shows |
| --- | --- | --- |
| `step1_call.py` | One request | The first request is 363 tokens: instructions 49, task 21, the notes about the 4 tools 293. The second request is 417, of which 54 are new. |
| `step2_tools.py` | The hands | The 4 tools on the real folder: 5 files, 14 tests, 2 fail. |
| `step3_loop.py` | The loop | 7 requests: list, test, read, edit, edit, test, summary. Tests go from `FAILED (failures=2)` to `OK`; 2 lines of `cart.py` change. |
| `step4_meter.py` | The bill | Tokens sent per request: 363, 417, 777, 1,275, 1,346, 1,412, 1,630 = 7,220. All text counted once: 1,667. Twice the steps cost about four times the tokens. |
| `step5_guard.py` | Fences | A path outside the folder, a tool that does not exist and a wrong edit all come back as error text. A stuck model with a limit of 100 steps sends 2,481,600 tokens. |
| `step6_cut.py` | A smaller bill | Quiet tests −14%, forgetting old results −28%, cache price −58% at best. Forgetting and the cache price together cost more than the cache price alone. |
| `step7_wire.py` | The real client | `ApiModel` sends 7 HTTP requests to `local_server.py` on 127.0.0.1 and gets the same conversation. A request without a key gets HTTP 401. |
| `step8_price.py` | Four price lists | Counted tokens × public prices read on 2026-10-08 (`prices.json`): one fix costs $0.0168 to $0.0012. |

`meter.py` counts tokens and prices a run. `tests.py` checks the fences, the edit rule and the saved numbers.

## Use it with a real model (your key, your money)

```bash
AGENT_URL=https://api.example.com/v1/chat/completions AGENT_KEY=your-key AGENT_MODEL=model-name python3 agent.py bugshop "Make the tests pass."
```

Work on a copy of the folder. The agent stops after 20 requests.

## What this is not

- Not a measurement of any model. The tape takes 7 steps because 7 were written.
- Not a safe sandbox. The agent can edit test files and run the tests, so it can run any code it writes. Use a folder,
  a user account or a machine you can afford to lose.
- The token counts are an estimate of a provider's count; a real reply reports the provider's own count in `usage`.
- The cache figures assume every repeated start of a request is found in the cache. Providers set minimum lengths and
  lifetimes.
- Prices change. `prices.json` holds what four public pages said on 2026-10-08.
