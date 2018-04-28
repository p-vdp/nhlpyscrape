"""Summarize days off between games from processed data JSON."""

import json
import matplotlib.pyplot as plt
import sys
from collections import OrderedDict
from datetime import datetime
from datetime import timedelta
from pytz import timezone
from scipy.stats import linregress
from statistics import mean, median


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


# team_query = ['TBL']    # team(s) to analyze (three letter abbrev)
# team_query = []     # leave empty to analyze all available teams

team_data, axis_days_off, \
    axis_points, axis_last_10 = analysis_restdays(['SJS'])

subplt1 = points_regression(axis_days_off, axis_points, team_data,
                            'Days Since Previous Game', 'Points',
                            upperbound_x=6.0)
subplt2 = points_regression(axis_last_10, axis_points, team_data,
                            'Games in Previous 10 Days', 'Points')


team_data, axis_days_off, \
    axis_points, axis_last_10 = analysis_restdays([])

subplt3 = points_regression(axis_days_off, axis_points, team_data,
                            'Days Since Previous Game', 'Points',
                            upperbound_x=6.0)
subplt4 = points_regression(axis_last_10, axis_points, team_data,
                            'Games in Previous 10 Days', 'Points')


print('Plotting...')
plt.show()
print('Done.')
