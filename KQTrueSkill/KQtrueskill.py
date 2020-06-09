import copy
import filecmp
import datetime
import math

import trueskill
from trueskill import *
from dataclasses import dataclass
import csv
import collections


@dataclass
class RatingsUpdate:
    '''Class for reporting on the change in ratings after a match.'''
    tournament: str
    my_team_name: str
    their_team_name: str
    my_player_name: str
    my_old_rating: Rating
    my_new_rating: Rating
    wins: int
    losses: int


class AggregatedMatchStats:
    def __init__(self):
        self.wins = 0
        self.losses = 0
        self.net_rating_change = 0.0

    def aggregate(self, ratings_update: RatingsUpdate) -> None:
        self.wins += ratings_update.wins
        self.losses += ratings_update.losses
        self.net_rating_change += ratings_update.my_new_rating.mu - ratings_update.my_old_rating.mu

    def __repr__(self):
        return f'wins {self.wins}, losses {self.losses}, net_rating_change {self.net_rating_change:.3f}'



class RatingsChangeObserver:
    def __init__(self, teams):
        self.teams = teams

    def observe(self, ratings_update: RatingsUpdate) -> None:
        pass

    
class RatingsChangeByOpponent(RatingsChangeObserver):
    def __init__(self, teams):
        super().__init__(teams)
        self.ratings_change_by_opp = collections.defaultdict(lambda: collections.defaultdict(AggregatedMatchStats))

    def observe(self, ratings_update: RatingsUpdate):
        my_name = ratings_update.my_player_name
        for opp_name in self.teams[ratings_update.tournament][ratings_update.their_team_name]:
            self.ratings_change_by_opp[my_name][opp_name].aggregate(ratings_update)



class RatingsChangeByTeammate(RatingsChangeObserver):
    def __init__(self, teams):
        super().__init__(teams)
        self.ratings_change_by_teammate = collections.defaultdict(lambda: collections.defaultdict(AggregatedMatchStats))

    def observe(self, ratings_update: RatingsUpdate):
        my_name = ratings_update.my_player_name
        for teammate_name in self.teams[ratings_update.tournament][ratings_update.my_team_name]:
            if teammate_name != my_name:
                self.ratings_change_by_teammate[my_name][teammate_name].aggregate(ratings_update)

        

class KQTrueSkill:
    datetime_format: str = "%Y-%m-%dT%H:%M:%S%z"

    def __init__(self):
        trueskill.setup(trueskill.MU, trueskill.SIGMA, trueskill.BETA, trueskill.TAU, draw_probability=0)
        self.snapshots = {}  # self.snapshots[tournament] = {'playername' = , 'trueskill' = }
        self.matches: [] = []
        self.playerscenes = {}
        self.playerteams = {}
        self.playerratings = {}
        self.playertournaments = {}  # playertournaments[playername] = ["BB4","KQ30",...]
        self.playergames = {}
        self.playerwins = {}
        self.playerlosses = {}
        self.incomplete_players = []  # list of playernames w/0 scenes
        self.tournaments = []
        self.tournamentdates = {}  # source data only ties matches directly to a date.
        self.teams = {}  # [tournament][team name] = {p1, p2, p3...}
        self.output_file_name: str = '../PlayerSkill.csv'
        self.ratings_change_by_opponent = RatingsChangeByOpponent(self.teams)
        self.ratings_change_by_teammate = RatingsChangeByTeammate(self.teams)
        self.observers = [self.ratings_change_by_opponent, self.ratings_change_by_teammate]
        self.process_approved_datasets()

    # ingest the known good datasets automatically
    def process_approved_datasets(self):
        self.ingest_dataset('datasets/2019 Players.csv', 'datasets/2019 game results.csv')
        self.ingest_dataset('datasets/SF-PDX-SEA-LA Players.csv', 'datasets/SF-PDX-SEA-LA game results.csv')
        self.ingest_dataset('datasets/BB Players.csv', 'datasets/BB game results.csv')
        self.ingest_dataset('datasets/CC Players.csv', 'datasets/CC game results.csv')
        self.ingest_dataset('datasets/Midwest players.csv', 'datasets/Midwest game results.csv')
        self.ingest_dataset('datasets/Coronation players.csv', 'datasets/Coronation game results.csv')

        # run trueskill on the matches
        self.calculate_trueskills()

    def test_dataset(self, player_file, results_file):
        self.ingest_dataset(player_file, results_file)
        # todo report teams with no matches
        # todo combine datasets into one file
        # self.calculate_trueskills()

    def ingest_dataset(self, playerfile: str, matchfile: str):
        # must ingest players first
        # reports new players found in this file
        self.ingest_players_from_file(playerfile)

        # expect Exceptions if your team names don't match
        self.ingest_matches_from_file(matchfile)

        # ensure matches will always process in historical order
        self.matches = sorted(self.matches, key=lambda match: match["time"])

    # wipe old ratings objects and recalculate trueskill, compare new result with old ratings
    # side effect: update player games & w/l counts
    def calculate_trueskills(self):
        # save old ratings for later comparison
        old_playerratings = self.playerratings

        # make clean ratings objects
        self.playerratings = {}
        for player in self.playerteams.keys():
            self.playerratings[player] = Rating()

        # calculate complete history
        current_tournament: str = ''
        for m in self.matches:
            t1ratings = []
            t2ratings = []
            tournament: str = m['tournament']
            team1name: str = m['team1name']
            team2name: str = m['team2name']
            team1wins: int = m['team1wins']
            team2wins: int = m['team2wins']

            if current_tournament != tournament:
                self.record_trueskill_snapshot(current_tournament)
                current_tournament = tournament
                print(f"processing {tournament}")

            # Trueskill wants arrays of ratings objects for each player
            # Order doesn't matter to trueskill, but it does matter to us, so preserve order as found in
            # the teams collection
            for player in self.teams[tournament][team1name]:
                t1ratings.append(self.playerratings[player])
                self.playergames[player] += team1wins + team2wins
                self.playerwins[player] += team1wins
                self.playerlosses[player] += team2wins


            for player in self.teams[tournament][team2name]:
                t2ratings.append(self.playerratings[player])
                self.playergames[player] += team1wins + team2wins
                self.playerwins[player] += team2wins
                self.playerlosses[player] += team1wins

            # teams with < 5 players are assumed to have played with bots.
            # we include bots as very low skill players, and don't track the results of their games
            if len(self.teams[tournament][team1name]) < 5:
                print(f"found team with <5 players: {team1name}")
                for _ in range(len(self.teams[tournament][team1name]), 5):
                    t1ratings.append(self.create_bot())
            if len(self.teams[tournament][team2name]) < 5:
                print(f"found team with <5 players: {team2name}")
                for _ in range(len(self.teams[tournament][team2name]), 5):
                    t2ratings.append(self.create_bot())

            # update ratings for each game win
            for x in range(team1wins):
                t1ratings, t2ratings = rate([t1ratings, t2ratings], ranks=[0, 1])

            for x in range(team2wins):
                t1ratings, t2ratings = rate([t1ratings, t2ratings], ranks=[1, 0])


            # Prepare a list of RatingsUpdate to send to observers
            all_updates = []
            for i in range(len(self.teams[tournament][team1name])):
                all_updates.append(RatingsUpdate(
                    tournament=tournament,
                    my_team_name=team1name,
                    their_team_name=team2name,
                    my_player_name=self.teams[tournament][team1name][i],
                    my_old_rating=self.playerratings[self.teams[tournament][team1name][i]],
                    my_new_rating=t1ratings[i],
                    wins=team1wins,
                    losses=team2wins))
            for i in range(len(self.teams[tournament][team2name])):
                all_updates.append(RatingsUpdate(
                    tournament=tournament,
                    my_team_name=team2name,
                    their_team_name=team1name,
                    my_player_name=self.teams[tournament][team2name][i],
                    my_old_rating=self.playerratings[self.teams[tournament][team2name][i]],
                    my_new_rating=t2ratings[i],
                    wins=team2wins,
                    losses=team1wins))

            for update in all_updates:
                for observer in self.observers:
                    observer.observe(update)

            # now put the ratings back into the main dict
            for i in range(len(self.teams[tournament][team1name])):
                self.playerratings[self.teams[tournament][team1name][i]] = t1ratings[i]
            for i in range(len(self.teams[tournament][team2name])):
                self.playerratings[self.teams[tournament][team2name][i]] = t2ratings[i]
        self.record_trueskill_snapshot(current_tournament)


    def compare_ratings(self, old_playerratings, playerratings):
        new_players = []
        removed_players = []
        shared_player_deltas = {}

        for p in old_playerratings.keys():
            if p in playerratings.keys():
                shared_player_deltas[
                    p] = f"mu: {playerratings[p].mu - old_playerratings[p].mu}, s: {playerratings[p].sigma - old_playerratings[p].sigma}"
            else:
                removed_players.append(p)

        for p in playerratings.keys():
            if p not in old_playerratings.keys():
                new_players.append(p)

        print(f"New Players: {new_players}")
        print(f"Removed players: {removed_players}")
        print(f"Changed players: {shared_player_deltas}")

    def ingest_players_from_file(self, filename: str):
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            last_seen_team = None
            for row in csv_reader:
                if line_count == 0:
                    print(f'Player List Column names are {", ".join(row)}')
                    line_count += 1
                else:
                    line_count += 1
                    tournament = row[0]
                    playerteam = row[1]
                    playername = row[2]
                    playerscene = row[3]

                    if playerteam is None or playerteam.strip() == '':
                        playerteam = last_seen_team
                    else:
                        last_seen_team = playerteam
                    self.add_player(playername, playerscene, playerteam, tournament)
            print(f'Processed {line_count} players from {filename}.')
            # print(f'Player Scenes: {self.playerscenes}')
            # print(f'****TEAMS: {self.teams}')

    def add_player(self, playername, playerscene, playerteam, tournament):
        if tournament not in self.tournaments:
            self.tournaments.append(tournament)
            self.teams[tournament] = {}

        if playerteam is None or playerteam.strip() == '':
            raise Exception(f"{tournament}.add_player: empty team")

        if playerteam in self.teams[tournament].keys():
            if playername is None or playername == '':
                playername = playerteam + f" {len(self.teams[tournament][playerteam]) + 1}"
                playerscene = None
                self.incomplete_players.append(f"{tournament}: {playername}")
            self.teams[tournament][playerteam].append(playername)
        else:
            if playername is None or playername == '':
                playername = playerteam + " 1"
                self.incomplete_players.append(f"{tournament}: {playername}")
                playerscene = None
            self.teams[tournament][playerteam] = [playername]

        self.playerscenes[playername] = playerscene

        if playername in self.playerteams.keys():
            self.playerteams[playername][tournament] = playerteam
        else:
            self.playerteams[playername] = {tournament: playerteam}

        if playername in self.playertournaments.keys():
            self.playertournaments[playername].append(tournament)
        else:
            self.playertournaments[playername] = [tournament]

        self.playergames[playername] = 0
        self.playerwins[playername] = 0
        self.playerlosses[playername] = 0

        # elif playerscene is None or playerscene.strip() == '':
        #     self.incomplete_players.append(f"{tournament}: {playerteam}, {playername}, {playerscene}")

    # side effect: updates tournament dates with dates found here
    def ingest_matches_from_file(self, filename: str):
        with open(filename) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            errors = ''
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
                        errors += f"{tournament} not found in self.tournaments. tournaments found = {self.tournaments}\n"
                    if team1name not in self.teams[tournament].keys():
                        errors += f"{team1name} not found in teams[{tournament}]. team 2 was {team2name}. teams found = {self.teams[tournament].keys()}\n"
                    if team2name not in self.teams[tournament].keys():
                        errors += f"{team2name} not found in teams[{tournament}]. team 1 was {team1name}. teams found = {self.teams[tournament].keys()}\n"

                    # track the date for this tournament, if not already tracked
                    if tournament not in self.tournamentdates.keys():
                        self.tournamentdates[tournament] = time.date()
                        print(f"sat {tournament} date to {time.strftime(KQTrueSkill.datetime_format)}")

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
        print(f"Processed {line_count - 1} matches, now tracking {len(self.matches)} matches.")
        if errors != '':
            raise Exception(errors)

    def write_player_ratings(self, filename: str = None):
        if filename is None:
            filename = self.output_file_name

        # make sure our csv rows align
        num_tourneys = len(self.tournaments)
        tourneylist = sorted(self.tournaments, key=lambda t: self.tournamentdates[t])

        headers = ['Player Name', 'scene', 'trueskill', 'tourneys', 'games', 'wins', 'losses', 'win%']
        headers += tourneylist * 2

        with open(filename, mode='w') as playerskillfile:
            playerskill_writer = csv.writer(playerskillfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            playerskill_writer.writerow(headers)
            for player in sorted(self.playerratings.keys()):
                try:
                    row = [player,
                           self.playerscenes[player],
                           self.playerratings[player].mu - 3 * self.playerratings[player].sigma,
                           len(self.playertournaments[player]),
                           self.playergames[player],
                           self.playerwins[player],
                           self.playerlosses[player],
                           "%.2f" % (self.playerwins[player] / self.playergames[player]),
                           ]
                    for t in tourneylist:
                        if t in self.playertournaments[player]:
                            row.append(t + " / " + self.playerteams[player][t])
                        else:
                            row.append('')
                    for t in tourneylist:
                        if self.snapshots[t][player].mu == trueskill.MU and self.snapshots[t][
                            player].sigma == trueskill.SIGMA:
                            row.append('')
                        else:
                            row.append(self.snapshots[t][player].mu - 3 * self.snapshots[t][player].sigma)
                    playerskill_writer.writerow(row)
                except ZeroDivisionError as e:
                    print(
                        f"{player}, {self.playerscenes[player]}, {self.playergames[player]}, {self.playerteams[player]}: {e}; probably a player with zero games")
                    raise e
                except Exception as e:
                    print(
                        f"{player}, {self.playerscenes[player]}, {self.playergames[player]}, {self.playerteams[player]}: {e}")
                    raise Exception(e)

    # returns win probability of 5 p1s vs 5 p2s
    def win_probability_players(self, p1, p2):
        return self.win_probability_teams(5 * [self.playerratings[p1]], 5 * [self.playerratings[p2]])

    # expects list of ratings objects for the 2 teams
    def win_probability_teams(self, team1, team2):
        delta_mu = sum(r.mu for r in team1) - sum(r.mu for r in team2)
        sum_sigma = sum(r.sigma ** 2 for r in team1) + sum(r.sigma ** 2 for r in team2)
        size = len(team1) + len(team2)
        ts: trueskill = trueskill.global_env()
        denom = math.sqrt(size * (ts.beta ** 2) + sum_sigma)
        return ts.cdf(delta_mu / denom)

    def get_player_scene_list(self):
        playerlist = []

        for playername in self.playerteams.keys():
            playerlist.append(f"{playername} / {self.playerscenes[playername]}")

        return playerlist

    def print_known_tournaments(self):
        printable_tournaments = {}
        for t in self.tournamentdates.keys():
            date: datetime.date = self.tournamentdates[t]
            if date.year in printable_tournaments.keys():
                printable_tournaments[date.year].append(t)
            else:
                printable_tournaments[date.year] = [t]
            printable_tournaments[date.year] = sorted(printable_tournaments[date.year],
                                                      key=lambda tourney: self.tournamentdates[tourney])
        for y in sorted(printable_tournaments.keys()):
            print(f"{y}: {printable_tournaments[y]}")

    def print_data_errors(self):
        # match errors are tracked during data scrubbing. known match errors hard coded into README
        # missing players should have an empty scene, so display players with empty scenes here
        for p in self.incomplete_players:
            print(p)

    def record_trueskill_snapshot(self, tournament):
        self.snapshots[tournament] = copy.deepcopy(self.playerratings)

    def create_bot(self):
        return Rating(mu=5.000, sigma=2)


def main():
    history: KQTrueSkill = KQTrueSkill()

    # stuff to copy into README
    history.print_known_tournaments()
    print("\n*************************\n")
    history.print_data_errors()

    # print your player ratings
    history.write_player_ratings()

    print(f"win probablity, 5 Dans vs 5 Wilks {history.win_probability_players('Dan Shupp', 'Andrew Wilkening')}")

    ni_howdy = [history.snapshots['BB4']['Woody Stanfield'],
                history.snapshots['BB4']['Helen Lau'],
                history.snapshots['BB4']['Dan Barron'],
                history.snapshots['BB4']['Nick Davis'],
                history.snapshots['BB4']['Andrew Quang'],
                ]

    clean = [history.snapshots['BB3']['Sam Beckman'],
             history.snapshots['BB3']['Prashant Sridhar'],
             history.snapshots['BB3']['Brian Wong'],
             history.snapshots['BB3']['Andrew Kelley'],
             history.snapshots['BB3']['Carissa Phong'],
             ]

    print(f"win probability, BB4 Ni Howdy vs BB3 CLEAN = {history.win_probability_teams(ni_howdy, clean)}")
    # print(f'Player Ratings: {history.playerratings}')


    def print_player_summary(player_name):
        print(player_name, 'teammates')
        teammate_info = history.ratings_change_by_teammate.ratings_change_by_teammate[player_name]
        for teammate in teammate_info:
            print(player_name, '+', teammate, teammate_info[teammate])

        print()
        print(player_name, 'opponents')
        opp_info = history.ratings_change_by_opponent.ratings_change_by_opp[player_name]
        for opp in opp_info:
            if opp_info[opp].wins + opp_info[opp].losses >= 6:
                print(player_name, '-', opp, opp_info[opp])

    print_player_summary('Rob Neuhaus')
    print_player_summary('Dan Shupp')

    # test whether processing changed values
    if filecmp.cmp("PlayerSkill.old.csv", history.output_file_name):
        print("Files are same")
    else:
        print("Files are different")


if __name__ == '__main__':
    main()
