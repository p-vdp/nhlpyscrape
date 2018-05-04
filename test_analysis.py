"""
An example script to demonstrate API scraping and data analysis.

1. Construct season standings tables
2. Is there a relationship between games off and win/loss/tie?
"""

import nhlpyscrape
import sys

# Check for valid output folder
try:
    folderpath = sys.argv[1]
except IndexError:
    sys.exit('Error: Provide data destination folder as argument, e.g.\n'
             + 'python3 tests.py /file/path/')

# # Scrape 2017-2018 regular season data
# nhlpyscrape.scrape_season_to_file(2017, 2017, folderpath, '02', 1, 0.5)
# print('\nDone scraping')

# Process files into holding dictionary, create one entry per team per game
filelist = nhlpyscrape.list_files_in_folder(folderpath)
data_holding = {}
num_files = len(filelist)
cur_file = 0

for file in filelist:
    print('Processed data file:', file, '(', cur_file, '/', num_files, ')',
          end='\r', flush=True)

    game_data = nhlpyscrape.file_to_json(file)

    # Extract info from NHL API's JSON data
    try:
        game_id = nhlpyscrape.game_id(game_data)
        season = nhlpyscrape.season_id(game_data)
        game_datetime_z = nhlpyscrape.game_datetime_z(game_data)
        away = nhlpyscrape.away_abbrv(game_data)
        away_goals = nhlpyscrape.away_goals(game_data)
        away_shots = nhlpyscrape.away_shots(game_data)
        home = nhlpyscrape.home_abbrv(game_data)
        home_goals = nhlpyscrape.home_goals(game_data)
        home_shots = nhlpyscrape.home_shots(game_data)
        periods = nhlpyscrape.periods(game_data)
        shootout = nhlpyscrape.shootout(game_data)

    # Calculate OT status and game points -- only correct after 1999
        if periods > 3:
            overtime = True
        else:
            overtime = False

        winner, away_points, home_points = nhlpyscrape.calc_points(overtime,
                                                                   away_goals,
                                                                   home_goals)

        # Convert game date to PST for accurate gameday
        game_datetime_pst = nhlpyscrape.nhl_time_to_pst(game_datetime_z)

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

    except KeyError:
        pass            # Skip invalid data structure

    cur_file += 1

print('Processed data file:', file, '(', cur_file, '/', num_files, ')',
      end='\r', flush=True)
print('\nDone processing')

# Write data object to file
nhlpyscrape.json_to_file(data_holding, folderpath + 'data_holding.json')
print('Wrote data summary to', folderpath + 'data_holding.json')


# Analysis 1. Construct season standings tables
game_data = dict()
output_data = {}

game_data = nhlpyscrape.file_to_json(folderpath + 'data_holding.json')

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

# Construct standings table in CSV format
output = 'team,points,season\n'
for season in output_data:
    for team in sorted(output_data[season],
                       key=output_data[season].get, reverse=True):
        output += (team + ',' + str(output_data[season][team]) + ','
                   + str(season)[:4] + '-' + str(season)[4:] + '\n')

# Write to file and print output
nhlpyscrape.string_to_file(output, folderpath + 'data_standings.csv')
print('\nStandings derived from data:\n', output.replace(',', '\t'))
print('Wrote standings to', folderpath + 'data_standings.csv')


# Analysis 2. Is there a relationship between games off and win/loss/tie?

# # plot results
# gradient, intercept, r_val, p_val, std_err = points_linear_reg()
# regline_string = 'y=' + str(round(grad, 3)) + \
#                  'x+' + str(round(intercept, 3)) + ''
#
# axis_reg_x = []
# axis_reg_y = []
#
# for i in range(round(min(axis_x)), round(max(axis_x)) + 1, 1):
#     axis_reg_x.append(i)
#     axis_reg_y.append((i * grad) + intercept)
#
# # Calculate distributions for 0, 1, and 2 points scenarios
# axis_0 = []
# axis_1 = []
# axis_2 = []
#
# for i in range(0, len(axis_x)):
#     if points_axis_y[i] == 0:
#         axis_0.append(axis_x[i])
#     elif points_axis_y[i] == 1:
#         axis_1.append(axis_x[i])
#     elif points_axis_y[i] == 2:
#         axis_2.append(axis_x[i])
#     else:
#         sys.exit('Error: Bad data found in points calculations')
#
# # Set up plots:
# # Overall figure
# f, subplt = plt.subplots(figsize=(8, 6))
#
# subplt.set_title(label_x + ' vs. ' + label_y)
# subplt.set_xlabel(label_x)
# subplt.set_ylabel(label_y)
#
# subplt.annotate('n=' + "{:,}".format(len(axis_x)) + ' games',
#                 va='top', ha='left',
#                 xy=(0.01, 0.99), xycoords='figure fraction')
# subplt.annotate('\n'.join(sorted(teams)),
#                 va='top', ha='right',
#                 xy=(0.99, 0.99), xycoords='figure fraction')
# subplt.annotate('mean',
#                 va='bottom', ha='left',
#                 xy=(0.01, 0.03), xycoords='axes fraction', fontsize=8)
# subplt.annotate('median',
#                 va='bottom', ha='left',
#                 xy=(0.01, 0.01), xycoords='axes fraction',
#                 fontsize=8, style='italic')
#
# # Violin plots
# # 0 points
# subplt.violinplot(axis_0, positions=[0], vert=False, showmeans=True,
#                   showmedians=True, widths=0.5, showextrema=True)
# subplt.annotate(round(mean(axis_0), 2),
#                 va='bottom', ha='center',
#                 xy=(mean(axis_0), 0.15), xycoords='data',
#                 fontsize=8)
# subplt.annotate(round(median(axis_0), 2),
#                 va='top', ha='center',
#                 xy=(median(axis_0), -0.15), xycoords='data',
#                 fontsize=8, style='italic')
#
# # 1 point
# subplt.violinplot(axis_1, positions=[1], vert=False, showmeans=True,
#                   showmedians=True, widths=0.5, showextrema=True)
# subplt.annotate(round(mean(axis_1), 2),
#                 va='bottom', ha='center',
#                 xy=(mean(axis_1), 1.15), xycoords='data',
#                 fontsize=8)
# subplt.annotate(round(median(axis_1), 2),
#                 va='top', ha='center',
#                 xy=(median(axis_1), 0.85), xycoords='data',
#                 fontsize=8, style='italic')
#
# # 2 points
# subplt.violinplot(axis_2, positions=[2], vert=False, showmeans=True,
#                   showmedians=True, widths=0.5, showextrema=True)
# subplt.annotate(round(mean(axis_2), 2),
#                 va='bottom', ha='center',
#                 xy=(mean(axis_2), 2.15), xycoords='data',
#                 fontsize=8)
# subplt.annotate(round(median(axis_2), 2),
#                 va='top', ha='center',
#                 xy=(median(axis_2), 1.85), xycoords='data',
#                 fontsize=8, style='italic')
#
# # Regression line
# subplt.plot(axis_reg_x, axis_reg_y)
# subplt.annotate(regline_string,
#                 va='bottom', ha='center',
#                 xy=(mean(axis_reg_x), mean(axis_reg_y)), xycoords='data',
#                 rotation=int(grad * 100), fontsize=8)
# subplt.annotate('p-value=' + str(round(p_val, 8)),
#                 va='bottom', ha='left',
#                 xy=(0.01, 0.01), xycoords='figure fraction')



# team_query = ['TBL']    # team(s) to analyze (three letter abbrev)
# team_query = []     # leave empty to analyze all available teams
#
# team_data, axis_days_off, \
#     axis_points, axis_last_10 = nhlpyscrape.analysis_restdays(['SJS'])
#
# subplt1 = nhlpyscrape.points_regression(axis_days_off, axis_points, team_data,
#                             'Days Since Previous Game', 'Points',
#                             upperbound_x=6.0)
# subplt2 = nhlpyscrape.points_regression(axis_last_10, axis_points, team_data,
#                             'Games in Previous 10 Days', 'Points')
