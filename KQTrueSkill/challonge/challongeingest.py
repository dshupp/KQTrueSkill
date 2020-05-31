import csv
from aifc import Error
import datetime
import requests
import json

from KQTrueSkill.KQtrueskill import KQTrueSkill


class ChallongeAccount:
    API_KEY_DSHUPP: str = "OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd"
    SUBDOMAIN_KQSF = "kq-sf"

    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    API_URL: str = "https://api.challonge.com/v1/"

    def __init__(self, api_key: str = API_KEY_DSHUPP, subdomain: str = SUBDOMAIN_KQSF):
        self.subdomain = subdomain
        self.api_key = api_key

    def get_tourney_list(self) -> {}:
        url: str = f"{self.API_URL}tournaments.json?api_key={self.api_key}"
        if self.subdomain is not None:
            url += f"&subdomain={self.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    def get_tournament(self, parent_tourney_name, tourney_id):
        return ChallongeTournament(parent_tourney_name, tourney_id, self)


class ChallongeTournament:

    def __init__(self, parent_tourney_name: str, tourney_id: int, account: ChallongeAccount):
        if ChallongeAccount is not None:
            self.account: ChallongeAccount = account
        else:
            self.account: ChallongeAccount = ChallongeAccount()
        self.parent_tourney_name = parent_tourney_name
        self.tourney_id = tourney_id
        self.bracket_name = self.get_bracket_name()
        self.teams = {}
        self.team_ids: {} = {}
        self.teamnames: [] = []
        self.build_participants_list()
        self.match_results = []
        self.build_match_results()

    # GET https://api.challonge.com/v1/tournaments/{tournament}/matches.{json|xml}
    def get_matches(self):
        url: str = f"{self.account.API_URL}tournaments/{self.tourney_id}/matches.json?api_key={self.account.api_key}"
        if self.account.subdomain is not None:
            url += f"&subdomain={self.account.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    # GET https://api.challonge.com/v1/tournaments/{tournament}/participants.{json|xml}
    def build_participants_list(self):
        url: str = f"{self.account.API_URL}tournaments/{self.tourney_id}/participants.json?api_key={self.account.api_key}"
        if self.account.subdomain is not None:
            url += f"&subdomain={self.account.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        for participant in resp.json():
            team_id = participant['participant']['id']
            team_name = participant['participant']['name']
            self.teams[team_id] = team_name
            self.team_ids[team_name] = team_id
            self.teamnames.append(team_name)
            # print(f"{team_id}, {team_name}")

    def build_match_results(self):
        for m in self.get_matches():
            match = m["match"]
            scores_csv: str = match["scores_csv"]
            scores_list: [] = scores_csv.split("-")
            team1wins = scores_list[0]
            team2wins = scores_list[1]
            team1name: str = self.teams[match['player1_id']]
            team2name: str = self.teams[match['player2_id']]
            time = datetime.datetime.strptime(match['started_at'], ChallongeAccount.DATETIME_FORMAT)
            self.match_results.append(
                [self.parent_tourney_name, self.bracket_name, team1name, team2name, team1wins, team2wins, time])
            # print(
            #     f"{self.parent_tourney_name}, {self.bracket_name}, {team1wins}, {team2wins}, {team1name}, {team2name}, {time}")

    def get_bracket_name(self):
        url: str = f"{self.account.API_URL}tournaments/{self.tourney_id}.json?api_key={self.account.api_key}"
        if self.account.subdomain != None:
            url += f"&subdomain={self.account.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        return resp.json()['tournament']['name']

    def write_matchfile(self, filename: str = None):
        if filename is None:
            filename = self.output_file_name
        with open(filename, mode='w') as match_file:
            match_writer = csv.writer(match_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            match_writer.writerow(["tournament", "bracket",
                                   "team1name", "team2name", "team1wins", "team2wins", "time"])

            for match in self.match_results:
                row = [match[0],
                       'KO',
                       match[2],
                       match[3],
                       match[4],
                       match[5],
                       datetime.datetime.strftime(match[6], KQTrueSkill.datetime_format)
                       ]
                match_writer.writerow(row)


def main():
    # scripts for importing a tournament from challonge and getting it into an editable csv that can be read into a KQ history
    # subtourney_id: int = 5689203  # GDC4 Groups 1
    # subtourney_id: int = 4415714  # GDC3 DE
    # tourney_name: str = "GDC3"
    # account: ChallongeAccount = ChallongeAccount()
    # ct: ChallongeTournament = account.get_tournament(tourney_name, subtourney_id)
    # ct.write_matchfile('out.csv')

    # test the ingest. players must be loaded first
    history: KQTrueSkill = KQTrueSkill()
    print(history.tournaments)
    history.ingest_players_from_file('datasets/2018 KQ - GDC3 Players.csv')
    history.ingest_matches_from_file('datasets/2018 KQ - GDC3 game results.csv')

    history.write_player_ratings('')

    # tourneys: [] = account.get_tourney_list()
    # for t in tourneys:
    #     print(f"{t['tournament']}")


if __name__ == '__main__':
    main()
