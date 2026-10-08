"""Step 2. The four tools, used by hand. No model yet."""
import agent
import tape
from save import save

base, folder = tape.fresh_project()

listing = agent.list_files(folder)
print('list_files\n' + listing + '\n')

report = agent.run_tests(folder)
lines = report.splitlines()
failed = [line.split()[0] for line in lines if line.endswith('... FAIL')]
ran = int([line for line in lines if line.startswith('Ran ')][0].split()[1])
print('run_tests: %d tests, %d fail: %s' % (ran, len(failed), ', '.join(failed)))
print('\n'.join(line for line in lines if 'Error' in line) + '\n')

text = agent.read_file(folder, 'cart.py')
print('read_file cart.py: %d lines, %d characters\n' % (len(text.splitlines()), len(text)))

# edit_file changes one exact piece of text. Here: a spelling fix in a comment, then undo it.
print(agent.edit_file(folder, 'cart.py', 'ships free', 'is shipped free'))
changed = agent.read_file(folder, 'cart.py')
print('  lines that differ:', sum(a != b for a, b in zip(text.splitlines(), changed.splitlines())))
agent.edit_file(folder, 'cart.py', 'is shipped free', 'ships free')
print('  put back:', agent.read_file(folder, 'cart.py') == text)

tape.clean(base)
save(2, files=len(listing.splitlines()), listing=listing.splitlines(), ran=ran, failed=failed,
     errors=[line for line in lines if 'Error' in line], cart_lines=len(text.splitlines()), cart_chars=len(text),
     report_lines=len(lines))
