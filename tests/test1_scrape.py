import nhlpyscrape

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
