"""Frame helpers for tests: select map frames by year, not by index."""
import re, os
_core = open(os.path.join(os.path.dirname(__file__), '..', 'dist', 'core.mjs'), encoding='utf-8').read()
FRAMES = [int(x) for x in re.search(r'export const FRAMES=\[([^\]]*)\]', _core).group(1).split(',')]
def fsel(year):
    return f'[data-frame="{FRAMES.index(year)}"]'
