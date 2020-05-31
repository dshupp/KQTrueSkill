import filecmp
import datetime

from trueskill import *
import csv


class KQTrueSkill:
    datetime_format: str = "%Y-%m-%dT%H:%M:%S%z"

    def __init__(self):
        self.matches: [] = []
        self.playerscenes = {}
        self.playerteams = {}
        self.playerratings = {}
        self.playertournaments = {}  # playertournaments[playername] = {"BB4","KQ30",...}
        self.playergames = {}
        self.tournaments = []
        self.teams = {}  # [tournament][team name] = {p1, p2, p3...}
        self.output_file_name: str = '2019PlayerSkill.csv'
        self.process()

    def process(self):
        # ingest all your players
        self.ingest_dataset('datasets/2019 KQ - 2019 Players.csv', 'datasets/2019 KQ - 2019 game results.csv')
        self.ingest_dataset('datasets/2018 KQ - GDC3 Players.csv', 'datasets/2018 KQ - GDC3 game results.csv')

        # ingest all your matches. sort them into historical order

        # run trueskill on the matches
        self.calculate_trueskills()

    def ingest_dataset(self, playerfile: str, matchfile: str):
        self.ingest_players_from_file(playerfile)
        self.ingest_matches_from_file(matchfile)
        self.matches = sorted(self.matches, key=lambda match: match["time"])

    def calculate_trueskills(self):
        for m in self.matches:
            t1ratings = []
            t2ratings = []
            tournament: str = m['tournament']
            team1name: str = m['team1name']
            team2name: str = m['team2name']
            team1wins: int = m['team1wins']
            team2wins: int = m['team2wins']

            for player in self.teams[tournament][team1name]:
                t1ratings.append(self.playerratings[player])
                self.playergames[player] += team1wins + team2wins  # update player games count
                # print(f'\tGot rating for {team1name}/{player}')
            for player in self.teams[tournament][team2name]:
                t2ratings.append(self.playerratings[player])
                self.playergames[player] += team1wins + team2wins  # update player games count
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
                self.playerratings[self.teams[tournament][team1name][i]] = t1ratings[i]
                # print(f'\tPut rating for {team1name}/{teams[tournament][team1name][i]}')
            for i in range(5):
                self.playerratings[self.teams[tournament][team2name][i]] = t2ratings[i]
                # print(f'\tPut rating for {team2name}/{teams[tournament][team2name][i]}')
            # print(f'\tt1players: {teams[tournament][team1name]}\n\tt1ratings: {t1ratings}\n\tt2players: {teams[tournament][team2name]}\n\tt2ratings: {t2ratings}')

            # either always put ratings objects right back onto the player, or use a dict that references player name->rating object

    def write_player_ratings(self, filename: str = None):
        if filename is None:
            filename = self.output_file_name
        with open(filename, mode='w') as playerskillfile:
            playerskill_writer = csv.writer(playerskillfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            playerskill_writer.writerow(['Player Name', 'scene', 'mu', 'sigma', 'trueskill', 'tourneys', 'games', 'teams'])
            for player in self.playerratings.keys():
                row = [player, self.playerscenes[player], self.playerratings[player].mu,
                       self.playerratings[player].sigma,
                       self.playerratings[player].mu - 2 * self.playerratings[player].sigma,
                       len(self.playertournaments[player]),
                       self.playergames[player]]
                for team in self.playerteams[player]:
                    row.append(team)
                playerskill_writer.writerow(row)

    def ingest_players_from_file(self, filename: str):
        with open(filename) as csv_file:
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
                    self.add_player(playername, playerscene, playerteam, tournament)
                    line_count += 1
            print(f'Processed {line_count} lines.')
            print(f'Player Scenes: {self.playerscenes}')
            print(f'****TEAMS: {self.teams}')

    def add_player(self, playername, playerscene, playerteam, tournament):
        # assumption - teams/games expect tournaments to be processed in order (tourney 1 teams/games listed first, tourney 2 second, etc
        if tournament not in self.tournaments:
            self.tournaments.append(tournament)
            self.teams[tournament] = {}
        # print(f'\t{playername}, {playerscene}, {playerteam}.')
        self.playerscenes[playername] = playerscene
        if playerteam in self.teams[tournament].keys():
            # print(
            #     f'\tteams[{tournament}][{playerteam}] is {self.teams[tournament][playerteam]}, adding {playername}')
            self.teams[tournament][playerteam].append(playername)
        else:
            self.teams[tournament][playerteam] = [playername]
            # print(
            #     f'\tmade new team for {playerteam}. teams[{tournament}][{playerteam}] is {self.teams[tournament][playerteam]}')
        self.playerratings[playername] = Rating()
        # print(f'\tmade Rating object for {playerteam}/{playername}.')
        if playername in self.playerteams.keys():
            self.playerteams[playername].append(playerteam + '/' + tournament)
        else:
            self.playerteams[playername] = [playerteam + '/' + tournament]
        if playername in self.playertournaments.keys():
            self.playertournaments[playername].append(tournament)
        else:
            self.playertournaments[playername] = [tournament]
        # print(f'\t\tplayertournaments[{playername}] = {self.playertournaments[playername]}.')
        self.playergames[playername] = 0

    def ingest_matches_from_file(self, filename: str):
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            for row in csv_reader:
                if line_count == 0:
                    # print(f' Game Results Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    # print(f'\t{row[0]}, {row[1]}, {row[2]}, {row[3]}, {row[4]}, {row[5]}, {row[6]}.')
                    tournament = row[0]
                    bracket = row[1]
                    team1name = row[2]
                    team2name = row[3]
                    team1wins = int(row[4])
                    team2wins = int(row[5])
                    time = datetime.datetime.strptime(row[6], self.datetime_format)

                    # we should not be adding any new members to our tourney/team lists here
                    if tournament not in self.tournaments:
                        raise Exception(
                            f" {tournament} not found in self.tournaments. tournaments found = {self.tournaments}")
                    if team1name not in self.teams[tournament].keys():
                        raise Exception(
                            f"{team1name} not found in teams[{tournament}]. teams found = {self.teams[tournament].keys()}")
                    if team2name not in self.teams[tournament].keys():
                        raise Exception(
                            f"{team2name} not found in teams[{tournament}]. teams found = {self.teams[tournament].keys()}")

                    self.matches.append(
                        {"tournament": tournament,
                         "bracket": bracket,
                         "team1name": team1name,
                         "team2name": team2name,
                         "team1wins": team1wins,
                         "team2wins": team2wins,
                         "time": time,
                         })
                    line_count += 1
        print(f"Processed {line_count-1} matches, now tracking {len(self.matches)} matches.")


def main():
    history: KQTrueSkill = KQTrueSkill()

    # print your player ratings
    history.write_player_ratings()

    print(f'Player Ratings: {history.playerratings}')

    # test whether processing changed values
    if filecmp.cmp("2019PlayerSkill.old.csv", "2019PlayerSkill.csv"):
        print("Files are same")
    else:
        print("Files are different")


if __name__ == '__main__':
    main()
