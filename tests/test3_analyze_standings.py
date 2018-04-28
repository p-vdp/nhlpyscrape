"""Summarize season standings from processed data JSON."""

import json
import nhlpyscrape

# Summarize game entries by season
game_data = dict()
output_data = {}

with open('nhl_api_bulk_data_processing_results.json', 'r') as fname:
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
