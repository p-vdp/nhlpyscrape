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


def scrape_season(start_year, end_year, filepath='', season_type='02', start_game=1, wait_time=0.5):
    """
    Sequentially scrape 'feed/live' by season; create a file for each game.

    start_year = First season to scrape, e.g. 2016 for 2016-2017
    end_year = Last season to scrape, e.g. 2017 for 2017-2018
    filepath = Folder to save JSON files in
    season_type = Season type: 01 preseason, 02 regular, 03 playoffs
    start_game = Game number to start at
    wait_time = Time in seconds to wait after each API call -- be polite!
    """
    # Initial parameters
    run_status = True
    current_year = start_year
    current_game = start_game

    # Main loop
    while run_status is True:
        # Set up game_id and output filename
        game_id = int(str(current_year) + season_type +
                      '{0:04d}'.format(current_game))
        print('Processing:', game_id)
        filename = filepath + str(game_id) + '.json'

        # Scrape game
        scrape_game(game_id)

        # Write valid result to file, or else increment to next season
        try:
            assert result['gamePk'] == game_id

            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
                f.close()

            current_game += 1
            time.sleep(wait_time)                   # Wait before next API call
        except KeyError:
            if current_year < end_year:
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


def postprocess(folderpath):
    """Postprocess relevant NHL API data fields to a single JSON file."""
    # Start script timer
    start_time = datetime.now()

    # Validate command line input
    try:
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


def analyze_standings(filepath):
    """Summarize season standings from processed data JSON."""
    # Summarize game entries by season
    game_data = dict()
    output_data = {}

    with open('filepath', 'r') as fname:
        game_data = json.load(fname)
        fname.close()

    for guid in game_data:
        season = int(game_data[guid]['season'])
        team = game_data[guid]['team']
        points = int(game_data[guid]['points'])

        if output_data.get(season) is None:
            output_data[season] = {}

        if output_data[season].get(team) is None:
            output_data[season][team] = points
        else:
            output_data[season][team] += points

    # Print to csv
    print('team,points,season')
    for season in output_data:
        for team in sorted(output_data[season],
                           key=output_data[season].get, reverse=True):
            print(team + ',' + str(output_data[season][team]) + ',' +
                  str(season)[:4] + '-' + str(season)[4:])


def points_regression(axis_x, points_axis_y, teams, label_x='x', label_y='y',
                      upperbound_x=False, lowerbound_x=False):
    """Calculate linear regresssion for NHL points and plot graph."""
    # Preprocess input
    if len(axis_x) != len(points_axis_y):
        sys.exit('Error: axes lengths do not match')

    if upperbound_x is not False:
        for i in range(0, len(axis_x)):
            if axis_x[i] > upperbound_x:
                axis_x[i] = upperbound_x

    if lowerbound_x is not False:
        for i in range(0, len(axis_x)):
            if axis_x[i] < lowerbound_x:
                axis_x[i] = lowerbound_x

    # Linear regression
    grad, intercept, r_val, p_val, std_err = linregress(axis_x, points_axis_y)

    regline_string = 'y=' + str(round(grad, 3)) + \
                     'x+' + str(round(intercept, 3)) + ''

    axis_reg_x = []
    axis_reg_y = []

    for i in range(round(min(axis_x)), round(max(axis_x)) + 1, 1):
        axis_reg_x.append(i)
        axis_reg_y.append((i * grad) + intercept)

    # Calculate distributions for 0, 1, and 2 points scenarios
    axis_0 = []
    axis_1 = []
    axis_2 = []

    for i in range(0, len(axis_x)):
        if points_axis_y[i] == 0:
            axis_0.append(axis_x[i])
        elif points_axis_y[i] == 1:
            axis_1.append(axis_x[i])
        elif points_axis_y[i] == 2:
            axis_2.append(axis_x[i])
        else:
            print('Error: points calc')

    # Set up plots:
    # Overall figure
    f, subplt = plt.subplots(figsize=(8, 6))

    subplt.set_title(label_x + ' vs. ' + label_y)
    subplt.set_xlabel(label_x)
    subplt.set_ylabel(label_y)

    subplt.annotate('n=' + "{:,}".format(len(axis_x)) + ' games',
                    va='top', ha='left',
                    xy=(0.01, 0.99), xycoords='figure fraction')
    subplt.annotate('\n'.join(sorted(teams)),
                    va='top', ha='right',
                    xy=(0.99, 0.99), xycoords='figure fraction')
    subplt.annotate('mean',
                    va='bottom', ha='left',
                    xy=(0.01, 0.03), xycoords='axes fraction', fontsize=8)
    subplt.annotate('median',
                    va='bottom', ha='left',
                    xy=(0.01, 0.01), xycoords='axes fraction',
                    fontsize=8, style='italic')

    # Violin plots
    # 0 points
    subplt.violinplot(axis_0, positions=[0], vert=False, showmeans=True,
                      showmedians=True, widths=0.5, showextrema=True)
    subplt.annotate(round(mean(axis_0), 2),
                    va='bottom', ha='center',
                    xy=(mean(axis_0), 0.15), xycoords='data',
                    fontsize=8)
    subplt.annotate(round(median(axis_0), 2),
                    va='top', ha='center',
                    xy=(median(axis_0), -0.15), xycoords='data',
                    fontsize=8, style='italic')

    # 1 point
    subplt.violinplot(axis_1, positions=[1], vert=False, showmeans=True,
                      showmedians=True, widths=0.5, showextrema=True)
    subplt.annotate(round(mean(axis_1), 2),
                    va='bottom', ha='center',
                    xy=(mean(axis_1), 1.15), xycoords='data',
                    fontsize=8)
    subplt.annotate(round(median(axis_1), 2),
                    va='top', ha='center',
                    xy=(median(axis_1), 0.85), xycoords='data',
                    fontsize=8, style='italic')

    # 2 points
    subplt.violinplot(axis_2, positions=[2], vert=False, showmeans=True,
                      showmedians=True, widths=0.5, showextrema=True)
    subplt.annotate(round(mean(axis_2), 2),
                    va='bottom', ha='center',
                    xy=(mean(axis_2), 2.15), xycoords='data',
                    fontsize=8)
    subplt.annotate(round(median(axis_2), 2),
                    va='top', ha='center',
                    xy=(median(axis_2), 1.85), xycoords='data',
                    fontsize=8, style='italic')

    # Regression line
    subplt.plot(axis_reg_x, axis_reg_y)
    subplt.annotate(regline_string,
                    va='bottom', ha='center',
                    xy=(mean(axis_reg_x), mean(axis_reg_y)), xycoords='data',
                    rotation=int(grad * 100), fontsize=8)
    subplt.annotate('p-value=' + str(round(p_val, 8)),
                    va='bottom', ha='left',
                    xy=(0.01, 0.01), xycoords='figure fraction')

    return subplt


def analysis_restdays(team_query):
    """Crunch numbers for queried team(s)."""
    # Initial parameters
    raw_format = '%Y-%m-%d %X'      # datetime format
    league_data = dict()
    team_data = dict()

    # Load data from file
    with open('nhl_api_bulk_data_processing_results.json', 'r') as fname:
        league_data = json.load(fname)
        fname.close()

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
            game_date = datetime.strptime(game_date[:-6], raw_format).replace(
                       tzinfo=timezone('US/Pacific'))

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

    # print(json.dumps(team_data, indent=2))

    # Analyze games_in_last_10_days

    analysis_window = 10                # look at last n days
    analysis_window_tag = 'games_in_last_' + str(analysis_window) + '_days'
    for team in team_data:
        for game in team_data[team]:
            game_date = team_data[team][game]['game_datetime_pst']
            game_date = datetime.strptime(game_date[:-6], raw_format).replace(
                       tzinfo=timezone('US/Pacific'))

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

    # STATS
    # Create empty lists for statistical analysis axes
    axis_game_date = []
    axis_days_off = []
    axis_points = []
    axis_last_10 = []

    for team in team_data:
        for game in team_data[team]:
            game_date = team_data[team][game]['game_datetime_pst']
            game_date = datetime.strptime(game_date[:-6], raw_format).replace(
                       tzinfo=timezone('US/Pacific'))

            axis_game_date.append(game_date)
            axis_days_off.append(team_data[team][game]['time_off_days'])
            axis_points.append(team_data[team][game]['points'])
            axis_last_10.append(team_data[team][game]['games_in_last_10_days'])

    return team_data, axis_days_off, axis_points, axis_last_10
