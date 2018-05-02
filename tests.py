"""Development test suite."""

import nhlpyscrape
import json
import sys

try:
    folderpath = sys.argv[1]
except IndexError:
    sys.exit('Error: Provide data destination folder as argument, e.g.\n'
             + 'python3 tests.py /file/path/')

print(json.dumps(nhlpyscrape.scrape_game(2017020001), indent=2))
print('OK')

nhlpyscrape.scrape_season_to_file(2017, 2017, folderpath, '02', 1270, 0.2)
print('OK')
