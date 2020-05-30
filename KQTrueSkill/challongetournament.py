from aifc import Error

import requests
import json


class ChallongeTournament:
    API_KEY_DSHUPP: str = "OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd"
    URL_KQSF: str = "https://kq-sf.challonge.com/tournaments.json"
    URL_DSHUPP: str = "https://api.challonge.com/v1/"
    INDEX: str = "tournaments.json"

    def __init__(self, tourney_name: str, tourney_id: int, subdomain: str = None):
        self.tourney_name = tourney_name
        self.tourney_id = tourney_id
        self.subdomain = subdomain
        self.bracket_name = self.get_bracket_name()
        self.teams = {}
        self.build_participants_list()
        self.match_results = []
        self.build_match_results()

    # GET https://api.challonge.com/v1/tournaments/{tournament}/matches.{json|xml}
    def get_matches(self):
        url: str = f"{ChallongeTournament.URL_DSHUPP}tournaments/{self.tourney_id}/matches.json?api_key={ChallongeTournament.API_KEY_DSHUPP}&subdomain={self.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    def get_tourney_list(self) -> {}:
        url: str = f"{ChallongeTournament.URL_DSHUPP}tournaments.json?api_key={ChallongeTournament.API_KEY_DSHUPP}"
        if self.subdomain != None:
            url += f"&subdomain={self.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    # GET https://api.challonge.com/v1/tournaments/{tournament}/participants.{json|xml}
    def build_participants_list(self):
        url: str = f"{ChallongeTournament.URL_DSHUPP}tournaments/{self.tourney_id}/participants.json?api_key={ChallongeTournament.API_KEY_DSHUPP}"
        if self.subdomain != None:
            url += f"&subdomain={self.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        for participant in resp.json():
            team_id = participant['participant']['id']
            team_name = participant['participant']['name']
            self.teams[team_id] = team_name
            self.teams[team_name] = team_id
            # print(f"{team_id}, {team_name}")

    def build_match_results(self):
        matches = self.get_matches()
        for m in matches:
            match = m["match"]
            scores_csv: str = match["scores_csv"]
            scores_list: [] = scores_csv.split("-")
            team1wins = scores_list[0]
            team2wins = scores_list[1]
            team1name: str = self.teams[match['player1_id']]
            team2name: str = self.teams[match['player2_id']]
            self.match_results.append(
                [self.tourney_name, self.bracket_name, team2name, team2name, team1wins, team2wins])
            print(f"{self.tourney_name}, {self.bracket_name}, {team1wins}, {team2wins}, {team1name}, {team2name}")

    def get_bracket_name(self):
        url: str = f"{ChallongeTournament.URL_DSHUPP}tournaments/{self.tourney_id}.json?api_key={ChallongeTournament.API_KEY_DSHUPP}"
        if self.subdomain != None:
            url += f"&subdomain={self.subdomain}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise Error('GET /index/ {}'.format(resp.status_code))
        return resp.json()['tournament']['name']


def main():
    print(f"testing challonge integration")
    subtourney_id: int = 5689203  # GDC4 Groups 1
    tourney_name: str = "GDC4"
    kqsf_subdomain: str = "kq-sf"
    ct = ChallongeTournament(tourney_name, subtourney_id, kqsf_subdomain)
    tourneys: [] = ct.get_tourney_list()
    # print(json.dumps(tourneys, indent=1))
    # for t in tourneys:
    #     print(f"{t}")


if __name__ == '__main__':
    main()
