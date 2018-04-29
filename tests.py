import nhlpyscrape
import sys

folderpath = sys.argv[1]

nhlpyscrape.scrape(2017, 2017, 'folderpath', '02', 1268)

# team_query = ['TBL']    # team(s) to analyze (three letter abbrev)
# team_query = []     # leave empty to analyze all available teams

team_data, axis_days_off, \
    axis_points, axis_last_10 = nhlpyscrape.analysis_restdays(['SJS'])

subplt1 = nhlpyscrape.points_regression(axis_days_off, axis_points, team_data,
                            'Days Since Previous Game', 'Points',
                            upperbound_x=6.0)
subplt2 = nhlpyscrape.points_regression(axis_last_10, axis_points, team_data,
                            'Games in Previous 10 Days', 'Points')
