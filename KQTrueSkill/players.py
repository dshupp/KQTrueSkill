import csv

from KQTrueSkill.KQtrueskill import KQTrueSkill




def compare_players_to_history(history: KQTrueSkill, filename: str = None):
    if filename is None:
        filename = 'datasets/2018 KQ - BB3 Players.csv'

    not_found = []
    with open(filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                line_count +=1
                print(line_count)
                tournament = row[0]
                playerteam = row[1]
                playername = row[2]
                playerscene = row[3]

                if playername not in history.playerteams.keys():
                    p = f"{playername} / {playerscene} not found. {tournament}/{playerteam} *************************"
                    # print(p)
                    not_found.append(p)
    all_players_sorted = sorted(history.get_player_scene_list() + not_found)
    for p in all_players_sorted:
        print(p)
    for p in not_found:
        print(p)


    # history.write_player_ratings('2018 KQ - HH1 game results.csv')


def main():
    history: KQTrueSkill = KQTrueSkill()
    print(history.tournaments)

    compare_players_to_history(history, 'datasets/2019 misc players.csv')

if __name__ == '__main__':
    main()
