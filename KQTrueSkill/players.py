import csv

from KQTrueSkill.KQtrueskill import KQTrueSkill




def compare_players_to_history(history: KQTrueSkill, filename: str = None):
    if filename is None:
        filename = 'team scratch - Sheet1.csv'
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                tournament = row[0]
                playerteam = row[1]
                playername = row[2]
                playerscene = row[3]

                if playername not in history.playerteams.keys():
                    print(f"{playername} / {playerscene} not found. {tournament}/{playerteam}")

    history.write_player_ratings('out.csv')


def main():
    history: KQTrueSkill = KQTrueSkill()
    print(history.tournaments)

    compare_players_to_history(history, 'team scratch - Sheet1.csv')

if __name__ == '__main__':
    main()
