"""
Postprocess relevant NHL API data fields to a single JSON file.

Receive folder containing NHL API "feed/live" JSON data from the command line.
"""

import nhlpyscrape
import json
import os
import sys
from datetime import datetime
from pytz import timezone


def calc_points(overtime, away_goals, home_goals):
    """Determine points for home/away."""
    if away_goals > home_goals:
        winner = 'away'
    elif away_goals < home_goals:
        winner = 'home'
    else:
        winner = 'tie'

    if overtime is False and winner == 'away':
        away_points = 2
        home_points = 0
    elif overtime is False and winner == 'home':
        away_points = 0
        home_points = 2
    elif overtime is True and winner == 'away':  # new rules overtime
        away_points = 2
        home_points = 1
    elif overtime is True and winner == 'home':
        away_points = 1
        home_points = 2
    elif overtime is True and winner == 'tie':   # old rules overtime
        away_points = 1
        home_points = 1
    else:
        sys.exit('Tie game error')

    return winner, home_points, away_points


def nhl_zulu_to_pst(date_string):
    """Convert NHL date/time format to PST."""
    raw_format = '%Y-%m-%dT%XZ'

    raw_date = datetime.strptime(date_string, raw_format).replace(
               tzinfo=timezone('UTC'))

    pst_date = str(raw_date.astimezone(timezone('US/Pacific')))

    return pst_date


# Start script timer
start_time = datetime.now()

# Validate command line input
try:
    folderpath = sys.argv[1]
    assert os.path.isdir(folderpath)
except IndexError:
    sys.exit("Error: Provide a folder containing JSON data")
except AssertionError:
    sys.exit("Error: File path is not a directory")

# Process file paths into a sorted list
filelist = []

for filename in os.listdir(folderpath):
    filepath = os.path.join(folderpath, filename)
    if (os.path.isdir(filepath)) or (filepath[-5:] != '.json'):
        continue
    else:
        filelist.append(filepath)

filelist = sorted(filelist)

# Process files into data holding, create one entry per team per game
data_holding = {}
num_files = len(filelist)
cur_file = 0
run_time = datetime.now() - start_time

for file in filelist:
    if cur_file % 60 == 0:
        run_time = datetime.now() - start_time
    print(' ', file, '(', cur_file, '/', num_files, run_time, ')',
          end='\r', flush=True)

    with open(file, 'r') as fname:
        game_data = json.load(fname)

        # Extract info from JSON data
        game_id = game_data['gameData']['game']['pk']
        season = game_data['gameData']['game']['season']
        game_datetime_z = game_data['gameData']['datetime']['dateTime']
        away = game_data['gameData']['teams']['away']['abbreviation']
        away_goals = game_data['liveData']['linescore']['teams']['away']['goals']
        away_shots = game_data['liveData']['linescore']['teams']['away']['shotsOnGoal']
        home = game_data['gameData']['teams']['home']['abbreviation']
        home_goals = game_data['liveData']['linescore']['teams']['home']['goals']
        home_shots = game_data['liveData']['linescore']['teams']['home']['shotsOnGoal']
        periods = game_data['liveData']['linescore']['currentPeriod']
        shootout = game_data['liveData']['linescore']['hasShootout']

        # Calculate OT status and game points -- only correct after 1999
        overtime = False
        if periods > 3:
            overtime = True

        winner, home_points, away_points = calc_points(overtime, away_goals, home_goals)

        # Convert game date to PST for accurate gameday
        game_datetime_pst = nhl_zulu_to_pst(game_datetime_z)

        # Add away team info to data holding
        data_holding[str(game_id) + '_' + away] = {
            'season': season,
            'game_id': game_id,
            'game_datetime_z': game_datetime_z,
            'game_datetime_pst': game_datetime_pst,
            'team': away,
            'goals': away_goals,
            'points': away_points,
            'shots': away_shots,
            'team_against': home,
            'goals_against': home_goals,
            'shots_against': home_shots,
            'overtime': overtime,
            'shootout': shootout
            }

        # Add home team info to data holding
        data_holding[str(game_id) + '_' + home] = {
            'season': season,
            'game_id': game_id,
            'game_datetime_z': game_datetime_z,
            'game_datetime_pst': game_datetime_pst,
            'team': home,
            'goals': home_goals,
            'points': home_points,
            'shots': home_shots,
            'team_against': away,
            'goals_against': away_goals,
            'shots_against': away_shots,
            'overtime': overtime,
            'shootout': shootout
            }

    fname.close()
    cur_file += 1

print(' ', file, '(', cur_file, '/', num_files, run_time, ')',
      end='\r', flush=True)

# Write data holding to file
print('Writing to output...')
filepath = 'nhl_api_bulk_data_processing_results.json'
with open(filepath, 'w') as fname:
    json.dump(data_holding, fname, indent=2)
    fname.close()

print('Done!')
