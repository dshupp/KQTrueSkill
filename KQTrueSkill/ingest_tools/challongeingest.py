import csv
from aifc import Error
import datetime
import configparser

import requests

import json

from KQTrueSkill.KQtrueskill import KQTrueSkill


class ChallongeAccount:
    SUBDOMAIN_KQSF = "kq-sf"

    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    API_URL: str = "https://api.challonge.com/v1/"

    def __init__(self, api_key: str, subdomain: str):
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

    def get_tournament(self, parent_tourney_name, tourney_id, bracket_name):
        return ChallongeTournament(parent_tourney_name, tourney_id, bracket_name, self)

    def print_tourney_list(self):
        tourneys: [] = self.get_tourney_list()
        for t in tourneys:
            print(f"{t['tournament']['name']}, {t['tournament']['id']}")
        pass


class ChallongeTournament:

    def __init__(self, parent_tourney_name: str, tourney_id: int, bracket_name: str, account: ChallongeAccount):
        if ChallongeAccount is not None:
            self.account: ChallongeAccount = account
        else:
            self.account: ChallongeAccount = ChallongeAccount()

        self.processing_errors = 0
        self.parent_tourney_name = parent_tourney_name
        self.tourney_id = tourney_id
        self.bracket_name = bracket_name  # self.get_bracket_name()
        self.teams = {}
        self.team_ids: {} = {}
        self.teamnames: [] = []
        self.build_participants_list()
        self.match_results = []
        self.build_match_results()
        self.first_write = True

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

    # GET https://api.challonge.com/v1/tournaments/{tournament}.{json|xml}
    def get_tournament_time(self):
        url: str = f"{self.account.API_URL}tournaments/{self.tourney_id}.json?api_key={self.account.api_key}"
        if self.account.subdomain is not None:
            url += f"&subdomain={self.account.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        p = resp.json()['tournament']['started_at']
        return datetime.datetime.strptime(p, ChallongeAccount.DATETIME_FORMAT)

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
            if scores_csv is None or scores_csv == '':
                team1wins = 'XXX'
                team2wins = 'XXX'
                print(f"ERROR - Empty scores_csv in match {match}")
                self.processing_errors += 1
            else:
                scores_list: [] = scores_csv.split("-")
                team1wins = scores_list[0]
                team2wins = scores_list[1]
            if match['player1_id'] is None:
                team1name = 'XXX'
                print(f"ERROR - Empty player1_id in match {match}")
                self.processing_errors += 1
            else:
                team1name: str = self.teams[match['player1_id']]

            if match['player2_id'] is None:
                team2name = 'XXX'
                print(f"ERROR - Empty player2_id in match {match}")
                self.processing_errors += 1
            else:
                team2name: str = self.teams[match['player2_id']]

            if match['started_at'] is None:
                time = datetime.datetime.today()
                print(f"ERROR - Empty started_at in match {match}")
                self.processing_errors += 1
            else:
                time = datetime.datetime.strptime(match['started_at'], ChallongeAccount.DATETIME_FORMAT)

            self.match_results.append(
                [self.parent_tourney_name, self.bracket_name, team1name, team2name, team1wins, team2wins, time])
        print(f"{self.processing_errors} processing errors")

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

    def write_matchfile(self, filename: str = None, append=False):
        if filename is None:
            filename = self.output_file_name
        mode = 'w'

        if append:
            mode = 'a'
        # print(f"mode is '{mode}', append is '{append}', first_write is '{self.first_write}'")

        with open(filename, mode=mode) as match_file:
            match_writer = csv.writer(match_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            if mode == 'w':
                match_writer.writerow(["tournament", "bracket",
                                       "team1name", "team2name", "team1wins", "team2wins", "time"])

            for match in self.match_results:
                row = [match[0],
                       match[1],
                       match[2],
                       match[3],
                       match[4],
                       match[5],
                       datetime.datetime.strftime(match[6], KQTrueSkill.datetime_format)
                       ]
                match_writer.writerow(row)


BB3: [] = ['BB3', [{'id': 5057256, 'name': 'BB3', 'bracket': 'KO'},
                   {'id': 5057264, 'name': 'BB3', 'bracket': 'Pool1'},
                   {'id': 5057281, 'name': 'BB3', 'bracket': 'Pool2'},
                   {'id': 5057309, 'name': 'BB3', 'bracket': 'Pool3'},
                   {'id': 5057310, 'name': 'BB3', 'bracket': 'Pool4'},
                   {'id': 5057312, 'name': 'BB3', 'bracket': 'Pool5'},
                   {'id': 5057313, 'name': 'BB3', 'bracket': 'Pool6'},
                   {'id': 5057316, 'name': 'BB3', 'bracket': 'Pool7'},
                   {'id': 5057318, 'name': 'BB3', 'bracket': 'Pool8'},
                   {'id': 5057321, 'name': 'BB3', 'bracket': 'Pool9'},
                   {'id': 5057323, 'name': 'BB3', 'bracket': 'Pool10'},
                   {'id': 5057324, 'name': 'BB3', 'bracket': 'WC'},
                   ]]

HH1: [] = ["HH1", [{'id': 5025209, 'name': 'HH1', 'bracket': 'Swiss'},
                   {'id': 5026099, 'name': 'HH1', 'bracket': 'KO'},
                   ]]

CC1: [] = ["CC1", [{'id': 4230293, 'name': 'CC1', 'bracket': 'GroupA'},
                   {'id': 4233246, 'name': 'CC1', 'bracket': 'GroupB'},
                   {'id': 4233248, 'name': 'CC1', 'bracket': 'GroupC'},
                   {'id': 4223960, 'name': 'CC1', 'bracket': 'KO'},
                   ]]

CC2: [] = ["CC2", [{'id': 5482725, 'name': 'CC2', 'bracket': 'GroupA'},
                   {'id': 5482751, 'name': 'CC2', 'bracket': 'GroupB'},
                   {'id': 5482814, 'name': 'CC2', 'bracket': 'GroupC'},
                   {'id': 5482847, 'name': 'CC2', 'bracket': 'KO'},
                   ]]

CC3: [] = ["CC3", [{'id': 8048812, 'name': 'CC3', 'bracket': 'GroupA'},
                   {'id': 8048841, 'name': 'CC3', 'bracket': 'GroupB'},
                   {'id': 8048854, 'name': 'CC3', 'bracket': 'GroupC'},
                   {'id': 8048858, 'name': 'CC3', 'bracket': 'GroupD'},
                   {'id': 8048880, 'name': 'CC3', 'bracket': 'KO'},
                   ]]


# subtourney_id: int = 5689203  # GDC4 Groups 1
# subtourney_id: int = 4415714  # GDC3 DE

def get_match_results_from_challonge(account, tourney_name, subtourney_list, filename):
    first_write = True
    for subtourney in subtourney_list:
        print(f"writing {subtourney['name']} / {subtourney['bracket']}")
        ct: ChallongeTournament = account.get_tournament(tourney_name, subtourney['id'], subtourney['bracket'])
        # ct.parent_tourney_name = 'BB3'
        # ct.bracket_name = subtourney['bracket']
        ct.write_matchfile(filename, not first_write)
        first_write = False


def main():
    # scripts for importing a tournament from ingest_tools and getting it into an editable csv that can be read into a KQ history

    cp: configparser.RawConfigParser = configparser.RawConfigParser()
    cp.read('api_keys.properties')
    api_key = cp.get('APIKeys', 'api_key.tyler')

    parent_tourney: str = CC3[0]
    subtourney_list: [] = CC3[1]



    account: ChallongeAccount = ChallongeAccount(api_key, None)
    # account.print_tourney_list()

    get_match_results_from_challonge(account, parent_tourney, subtourney_list, '2019 - CC3 game results.csv')


if __name__ == '__main__':
    main()
