"""
NHL bulk data scraper.

Scrape game data sequentially for a range of seasons. Write a JSON file to
current directory for each game with game details from the '/feed/live'
portion of the NHL's API.

Info about the API at: https://github.com/dword4/nhlapi
"""
import json
import requests
import time


# User parameters, change these to meet your needs
START_YEAR = 2016       # First season to scrape, e.g. 2016 for 2016-2017
END_YEAR = 2017         # Last season to scrape, e.g. 2017 for 2017-2018
START_GAME = 1          # Game number to start at
SEASON_TYPE = '02'      # Season type: 01 preseason, 02 regular, 03 playoffs
WAIT_TIME = 2.0         # Time to wait after each API call -- be polite!

# Initial parameters
run_status = True
current_year = START_YEAR
current_game = START_GAME

# Main loop
while run_status is True:
    # Set up game_id and output filename
    game_id = int(str(current_year) + SEASON_TYPE +
                  '{0:04d}'.format(current_game))
    print('Processing:', game_id)
    filename = str(game_id) + '.json'

    # Set up API request
    url = 'https://statsapi.web.nhl.com/api/v1/game/' + str(game_id) + \
          '/feed/live'

    # Make API request and load result into JSON object
    # Thanks to https://github.com/robhowley/nhlscrapi for headers
    req = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11\
            (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;\
            q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'})

    result = json.loads(req.text)

    # Write valid result to file, or else increment to next season
    try:
        assert result['gamePk'] == game_id

        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
            f.close()

        current_game += 1
        time.sleep(WAIT_TIME)                   # Wait before next API call
    except KeyError:
        if current_year < END_YEAR:
            current_year += 1
            current_game = 1
        else:
            run_status = False
    # File/permissions errors kill the script
    except FileNotFoundError:
        print('Error opening', filename)
        run_status = False
    except PermissionError:
        print('Error on permissions of', filename)
        run_status = False
