import filecmp
import datetime

from trueskill import *
import csv


class KQTrueSkill:


    def process(self):
        playerscenes = {}
        playerteams = {}
        playerratings = {}
        playertournaments = {}  # playertournaments[playername] = {"BB4","KQ30",...}
        playergames = {}
        tournaments = []
        teams = {}  # [tournament][team name] = {p1, p2, p3...}
        BB4ratings = {}

        with open('2019 KQ - 2019 Players.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    print(f'Player List Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    tournament = row[0]
                    playerteam = row[1]
                    playername = row[2]
                    playerscene = row[3]

                    # assumption - teams/games expect tournaments to be processed in order (tourney 1 teams/games listed first, tourney 2 second, etc
                    if tournament not in tournaments:
                        tournaments.append(tournament)
                        teams[tournament] = {}

                    print(f'\t{playername}, {playerscene}, {playerteam}.')
                    playerscenes[playername] = playerscene
                    # unused?
                    # playerteams[playername] = playerteam # use .append() here if we need this later

                    if playerteam in teams[tournament].keys():
                        print(
                            f'\tteams[{tournament}][{playerteam}] is {teams[tournament][playerteam]}, adding {playername}')
                        teams[tournament][playerteam].append(playername)
                    else:
                        teams[tournament][playerteam] = [playername]
                        print(
                            f'\tmade new team for {playerteam}. teams[{tournament}][{playerteam}] is {teams[tournament][playerteam]}')

                    playerratings[playername] = Rating()
                    print(f'\tmade Rating object for {playerteam}/{playername}.')

                    if playername in playerteams.keys():
                        playerteams[playername].append(playerteam + '/' + tournament)
                    else:
                        playerteams[playername] = [playerteam + '/' + tournament]

                    if playername in playertournaments.keys():
                        playertournaments[playername].append(tournament)
                    else:
                        playertournaments[playername] = [tournament]
                    print(f'\t\tplayertournaments[{playername}] = {playertournaments[playername]}.')

                    playergames[playername] = 0

                    line_count += 1
            print(f'Processed {line_count} lines.')
            print(f'Player Scenes: {playerscenes}')
            print(f'****TEAMS: {teams}')

        matches: [] = []
        with open('2019 KQ - 2019 game results.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    #  print(f' Game Results Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    # print(f'\t{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}.')
                    tournament = row[0]
                    bracket = row[1]
                    team1name = row[2]
                    team2name = row[3]
                    team1wins = int(row[4])
                    team2wins = int(row[5])

                    time = datetime.datetime.strptime(row[6], "%Y-%m-%dT%H:%M:%S%z")
                    matches.append(
                        {"tournament": tournament,
                         "bracket": bracket,
                         "team1name": team1name,
                         "team2name": team2name,
                         "team1wins": team1wins,
                         "team2wins": team2wins,
                         "time": time,
                         })
                    line_count += 1
        print(f"Processed {line_count} lines, matches has {len(matches)} entries.")

        ordered_matches = sorted(matches, key=lambda match: match["time"])

        for m in ordered_matches:
            t1ratings = []
            t2ratings = []
            tournament: str = m['tournament']
            team1name: str = m['team1name']
            team2name: str = m['team2name']
            team1wins: int = m['team1wins']
            team2wins: int = m['team2wins']

            for player in teams[tournament][team1name]:
                t1ratings.append(playerratings[player])
                playergames[player] += team1wins + team2wins  # update player games count
                # print(f'\tGot rating for {team1name}/{player}')
            for player in teams[tournament][team2name]:
                t2ratings.append(playerratings[player])
                playergames[player] += team1wins + team2wins  # update player games count
                # print(f'\tGot rating for {team2name}/{player}')
            # print(f'\tt1ratings: {t1ratings}\n\tt2ratings: {t2ratings}')
            # update ratings for each game win
            # print(f'\tupdate ratings for {team1name} {team1wins}-{team2wins} {team2name}:')
            # print(f'\tt1players: {teams[tournament][team1name]}\n\tt1ratings: {t1ratings}\n\tt2players: {teams[tournament][team2name]}\n\tt2ratings: {t2ratings}')
            for x in range(team1wins):
                # print(f'\t{team1name} won a game')
                t1ratings, t2ratings = rate([t1ratings, t2ratings], ranks=[0, 1])
                # print(f'\tt1players: {teams[tournament][team1name]}\nt1ratings: {t1ratings}\n\tt2players: {teams[tournament][team2name]}\nt2ratings: {t2ratings}')
            else:
                # print(f'\tdone with t1')
                pass
            for x in range(team2wins):
                # print(f'\t{team2name} won a game')
                t1ratings, t2ratings = rate([t1ratings, t2ratings], ranks=[1, 0])
                # print(f'\tt1players: {teams[tournament][team1name]}\nt1ratings: {t1ratings}\n\tt2players: {teams[tournament][team2name]}\nt2ratings: {t2ratings}')
            else:
                # print(f'\tdone with t2')
                pass

            # now put the ratings back into the main dict
            for i in range(5):
                playerratings[teams[tournament][team1name][i]] = t1ratings[i]
                # print(f'\tPut rating for {team1name}/{teams[tournament][team1name][i]}')
            for i in range(5):
                playerratings[teams[tournament][team2name][i]] = t2ratings[i]
                # print(f'\tPut rating for {team2name}/{teams[tournament][team2name][i]}')
            # print(f'\tt1players: {teams[tournament][team1name]}\n\tt1ratings: {t1ratings}\n\tt2players: {teams[tournament][team2name]}\n\tt2ratings: {t2ratings}')

            # either always put ratings objects right back onto the player, or use a dict that references player name->rating object

        with open('2019PlayerSkill.csv', mode='w') as playerskillfile:
            playerskill_writer = csv.writer(playerskillfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            playerskill_writer.writerow(['Player Name', 'mu', 'sigma', 'tourneys', 'games', 'teams'])
            for player in playerratings.keys():
                row = [player, playerratings[player].mu, playerratings[player].sigma, len(playertournaments[player]),
                       playergames[player]]
                for team in playerteams[player]:
                    row.append(team)
                playerskill_writer.writerow(row)

        print(f'Player Ratings: {playerratings}')


def main():
    history: KQTrueSkill = KQTrueSkill()
    history.process()
    # test whether processing changed values
    if filecmp.cmp("2019PlayerSkill.old.csv", "2019PlayerSkill.csv"):
        print("Files are same")
    else:
        print("Files are different")


if __name__ == '__main__':
    main()
