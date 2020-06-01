import csv
from aifc import Error
import datetime
import requests
import json

from KQTrueSkill.KQtrueskill import KQTrueSkill


class ChallongeAccount:
    API_KEY_DSHUPP: str = "OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd"
    API_KEY_DYLAN: str = "gp3v3gPX3aWcMPPtDiSDVP7rpEyX4hZokJ5w3WFj"
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

    def get_tournament(self, parent_tourney_name, tourney_id, bracket_name):
        return ChallongeTournament(parent_tourney_name, tourney_id, bracket_name, self)


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


def main():
    # scripts for importing a tournament from challonge and getting it into an editable csv that can be read into a KQ history
    # subtourney_id: int = 5689203  # GDC4 Groups 1
    # subtourney_id: int = 4415714  # GDC3 DE
    bb3_subtourneys = [{'id': 5057256, 'name': 'BB3', 'bracket': 'KO'},
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
                       ]
    tourney_name: str = "BB3"
    account: ChallongeAccount = ChallongeAccount(ChallongeAccount.API_KEY_DYLAN, None)

    # for tourney in account.get_tourney_list():
    #     t = tourney['tournament']
    #     print(f"{t['name']}, {t['id']}")

    # print(json.dumps(account.get_tourney_list(),indent=1))

    for subtourney in bb3_subtourneys:
        print(f"writing {subtourney['name']} / {subtourney['bracket']}")
        ct: ChallongeTournament = account.get_tournament(tourney_name, subtourney['id'], subtourney['bracket'])
        # ct.parent_tourney_name = 'BB3'
        # ct.bracket_name = subtourney['bracket']
        ct.write_matchfile('out.csv', True)

    # tourneys: [] = account.get_tourney_list()
    # for t in tourneys:
    #     print(f"{t['tournament']}")

    # test the ingest. players must be loaded first
    # history: KQTrueSkill = KQTrueSkill()
    # print(history.tournaments)
    # history.ingest_players_from_file('2018 KQ - BB3 Players.csv')
    # history.ingest_matches_from_file('out.csv')

    # history.write_player_ratings('')

    # tourneys: [] = account.get_tourney_list()
    # for t in tourneys:
    #     print(f"{t['tournament']}")


if __name__ == '__main__':
    main()
