"""
Tools module for the NHL stats API.

Info about the API at: https://github.com/dword4/nhlapi
"""
import json
import matplotlib.pyplot as plt
import os
import requests
import sys
import time
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from pytz import timezone
from scipy.stats import linregress
from statistics import mean, median


def json_to_file(obj, filepath):
    """Write JSON object to file."""
    try:
        with open(filepath, 'w') as f:
            json.dump(obj, f, indent=2)
            f.close()
    except FileNotFoundError:
        sys.exit('Error: Could not find ' + filepath)
    except FileNotFoundError:
        sys.exit('Error opening', filepath)
    except PermissionError:
        sys.exit('Error on permissions of', filepath)


def string_to_file(obj, filepath):
    """Write string object to file."""
    try:
        with open(filepath, 'w') as f:
            f.write(obj)
            f.close()
    except FileNotFoundError:
        sys.exit('Error: Could not find ' + filepath)
    except FileNotFoundError:
        sys.exit('Error opening', filepath)
    except PermissionError:
        sys.exit('Error on permissions of', filepath)


def file_to_json(filepath):
    """Read file into JSON object."""
    try:
        with open(filepath, 'r') as f:
            result = json.load(f)
            f.close()
            return result
    except FileNotFoundError:
        sys.exit('Error: Could not find ' + filepath)
    except FileNotFoundError:
        sys.exit('Error opening', filepath)
    except PermissionError:
        sys.exit('Error on permissions of', filepath)


def list_files_in_folder(folderpath):
    """Return an alpha-sorted list of files in a folder."""
    try:
        assert os.path.isdir(folderpath)
    except AssertionError:
        sys.exit("Error: File path is not a directory")

    filelist = list()

    for filename in os.listdir(folderpath):
        filepath = os.path.join(folderpath, filename)
        if (os.path.isdir(filepath)) or (filepath[-5:] != '.json'):
            continue
        else:
            filelist.append(filepath)

    return sorted(filelist)


def nhl_time_to_pst(date_string):
    """Convert NHL date/time format to PST."""
    raw_format = '%Y-%m-%dT%XZ'

    raw_date = datetime.strptime(date_string, raw_format).replace(
               tzinfo=timezone('UTC'))

    pst_date = str(raw_date.astimezone(timezone('US/Pacific')))

    return pst_date


def scrape_game(game_id):
    """Query the NHL API for a given game ID and return a JSON object."""
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

    return result


def scrape_season_to_file(start_year, end_year, filepath='', season_type='02',
                          start_game=1, wait_time=0.5):
    """
    Sequentially scrape NHL API by season and create a file for each game ID.

    start_year = First season to scrape, e.g. 2016 for 2016-2017
    end_year = Last season to scrape, e.g. 2017 for 2017-2018
    filepath = Folder to save JSON files in
    season_type = Season type: 01 preseason, 02 regular, 03 playoffs
    start_game = Game number to start at
    wait_time = Time in seconds to wait after each API call -- be polite!
    """
    run_status = True
    current_year = start_year
    current_game = start_game

    while run_status is True:
        # Set up game_id and output filename
        game_id = int(str(current_year) + season_type
                      + '{0:04d}'.format(current_game))
        filename = filepath + str(game_id) + '.json'

        # Scrape game
        result = scrape_game(game_id)

        # Write valid result to file, or else increment to next season
        try:
            result['gamePk'] == game_id
            json_to_file(result, filename)
            current_game += 1
            print('Scraped game ID:', game_id, end='\r', flush=True)
            time.sleep(wait_time)                   # Wait before next API call
        except KeyError:
            if current_year < end_year:
                current_year += 1
                current_game = 1
            else:
                run_status = False
                print('\n')


def game_id(obj):
    """Return game ID from NHL API's JSON (feed/live type)."""
    return obj['gameData']['game']['pk']


def season_id(obj):
    """Return season ID from NHL API's JSON  (feed/live type)."""
    return obj['gameData']['game']['season']


def game_datetime_z(obj):
    """Return game's date/time (GMT/Z) from NHL API's JSON (feed/live type)."""
    return obj['gameData']['datetime']['dateTime']


def away_abbrv(obj):
    """Return away team's abbreviation from NHL API's JSON (feed/live type)."""
    return obj['gameData']['teams']['away']['abbreviation']


def away_goals(obj):
    """Return away team's goals from NHL API's JSON (feed/live type)."""
    return obj['liveData']['linescore']['teams']['away']['goals']


def away_shots(obj):
    """Return away team's shots from NHL API's JSON (feed/live type)."""
    return obj['liveData']['linescore']['teams']['away']['shotsOnGoal']


def home_abbrv(obj):
    """Return home team's abbreviation from NHL API's JSON (feed/live type)."""
    return obj['gameData']['teams']['home']['abbreviation']


def home_goals(obj):
    """Return home team's goals from NHL API's JSON (feed/live type)."""
    return obj['liveData']['linescore']['teams']['home']['goals']


def home_shots(obj):
    """Return home team's shots from NHL API's JSON (feed/live type)."""
    return obj['liveData']['linescore']['teams']['home']['shotsOnGoal']


def periods(obj):
    """Return number of periods from NHL API's JSON (feed/live type)."""
    return obj['liveData']['linescore']['currentPeriod']


def shootout(obj):
    """Return shootout status (boolean) from NHL API's JSON (feed/live)."""
    return obj['liveData']['linescore']['hasShootout']


def calc_points(overtime, away_goals, home_goals):
    """
    Determine points for home/away for a given game (post-2005 rules).

    overtime = boolean
    away_goals = integer
    home_goals = integer
    """
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

    return winner, away_points, home_points


def points_linear_reg(ax_x, points_ax_y, teams, label_x='x', label_y='y',
                      upperbound_x=False, lowerbound_x=False):
    """Calculate linear regresssion for NHL points."""
    # Preprocess input
    if len(ax_x) != len(points_ax_y):
        sys.exit('Error: axes lengths do not match')

    if upperbound_x is not False:
        for i in range(0, len(ax_x)):
            if ax_x[i] > upperbound_x:
                ax_x[i] = upperbound_x

    if lowerbound_x is not False:
        for i in range(0, len(ax_x)):
            if ax_x[i] < lowerbound_x:
                ax_x[i] = lowerbound_x

    # Linear regression
    gradient, intercept, r_val, p_val, std_err = linregress(ax_x, points_ax_y)

    return gradient, intercept, r_val, p_val, std_err


def analysis_restdays(team_query, filepath):
    """Crunch numbers for a list of team abbreviations."""
    # Initial parameters
    league_data = dict()
    team_data = dict()

    # Load data from file
    league_data = file_to_json(filepath)

    # Populate teams if none provided
    if len(team_query) == 0:
        for guid in league_data:
            team = league_data[guid]['team']
            if team not in team_query:
                team_query.append(team)

    # Extract team data for analysis
    print('Processing:\n', team_query)

    for team in team_query:
        team_data_temp = dict()

        for guid in league_data:
            if guid[-3:] == team:
                game_date = league_data[guid]['game_datetime_pst'][:10]
                game_date = int(game_date.replace('-', ''))
                team_data_temp[game_date] = league_data[guid]
            else:
                pass

        team_data_temp = OrderedDict(sorted(team_data_temp.items(),
                                            key=lambda t: t[0]))
        team_data[team] = team_data_temp

    league_data.clear()

    # Process games and add data for time off
    for team in team_data:
        # Dummy date for first date
        prev_game = datetime(year=1990, month=1, day=1).replace(
                    tzinfo=timezone('US/Pacific'))

        for game in team_data[team]:
            # Calculate time off status, days, hours
            game_date = team_data[team][game]['game_datetime_pst']
            game_date = nhl_time_to_pst(game_date)

            if game_date > prev_game:
                time_off = game_date - prev_game
            else:
                sys.exit('Error on subtracting ' + str(prev_game) + ' '
                         + str(game_date))

            hours_off = (time_off.days * 24.0) + (time_off.seconds / 3600.0)
            days_off = hours_off / 24.0

            if hours_off > 480:                         # more than 20 days off
                team_data[team][game]['time_off_note'] = 'opener'
            elif hours_off > 120:                       # more than 5 days off
                team_data[team][game]['time_off_note'] = 'break'
            else:
                team_data[team][game]['time_off_note'] = 'regular'

            team_data[team][game]['time_off_days'] = float(days_off)
            team_data[team][game]['time_off_hours'] = float(hours_off)

            prev_game = game_date

    # Analyze games_in_last_10_days
    analysis_window = 10                # look at last n days
    analysis_window_tag = 'games_in_last_' + str(analysis_window) + '_days'
    for team in team_data:
        for game in team_data[team]:
            game_date = team_data[team][game]['game_datetime_pst']
            game_date = nhl_time_to_pst(game_date)

            analysis_window_start = game_date - timedelta(days=analysis_window)
            analysis_day = analysis_window_start

            match_count = 0
            while(analysis_day < game_date):
                analysis_game = int(str(analysis_day)[:10].replace('-', ''))
                analysis_day += timedelta(days=1)

                try:
                    team_data[team][analysis_game]['game_id']
                    match_count += 1
                except KeyError:
                    pass

            team_data[team][game][analysis_window_tag] = int(match_count)

    # Statistical analysis
    axis_game_date = []
    axis_days_off = []
    axis_points = []
    axis_last_10 = []

    for team in team_data:
        for game in team_data[team]:
            game_date = team_data[team][game]['game_datetime_pst']
            game_date = nhl_time_to_pst(game_date)

            axis_game_date.append(game_date)
            axis_days_off.append(team_data[team][game]['time_off_days'])
            axis_points.append(team_data[team][game]['points'])
            axis_last_10.append(team_data[team][game]['games_in_last_10_days'])

    return team_data, axis_days_off, axis_points, axis_last_10
