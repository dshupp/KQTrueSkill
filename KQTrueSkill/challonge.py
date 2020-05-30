import requests
import json


class Challonge:
    API_KEY_DSHUPP: str = "OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd"
    URL_KQSF: str = "https://kq-sf.challonge.com/tournaments.json"
    URL_DSHUPP: str = "https://api.challonge.com/v1/"
    SUBDOMAIN_KQSF: str = "kq-sf"
    TOURNEY_ID: int = 5689203
    INDEX: str = "tournaments.json"

    

    def __init__(self):
        self.teams = {}
        self.build_participants_list()

    # GET https://api.challonge.com/v1/tournaments/{tournament}/matches.{json|xml}
    # https://api.challonge.com/v1/documents/matches/index
    def get_matches_from_tourney(self, tourney_id: int):
        url: str = f"{Challonge.URL_DSHUPP}tournaments/{tourney_id}/matches.json?api_key={Challonge.API_KEY_DSHUPP}&subdomain={Challonge.SUBDOMAIN_KQSF}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    def get_kqsf_tourneys(self) -> {}:
        url: str = f"{Challonge.URL_DSHUPP}tournaments.json?api_key={Challonge.API_KEY_DSHUPP}&subdomain={Challonge.SUBDOMAIN_KQSF}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    # GET https://api.challonge.com/v1/tournaments/{tournament}/participants.{json|xml}
    def build_participants_list(self):
        url: str = f"{Challonge.URL_DSHUPP}tournaments/{self.TOURNEY_ID}/participants.json?api_key={Challonge.API_KEY_DSHUPP}&subdomain={Challonge.SUBDOMAIN_KQSF}"
        print(url)
        resp = requests.get(url)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /index/ {}'.format(resp.status_code))
        for participant in resp.json():
            team_id = participant['participant']['id']
            team_name = participant['participant']['name']
            self.teams[team_id] = team_name
            self.teams[team_name] = team_id
            # print(f"{team_id}, {team_name}")


def main():
    print(f"testing challonge integration")
    c = Challonge()
    tourneys: [] = c.get_kqsf_tourneys()
    # print(json.dumps(tourneys, indent=1))
    # for t in tourneys:
    #     print(f"{t}")
    tourney_id: int = c.TOURNEY_ID
    tourney_name: str = "GDC4"
    matches = c.get_matches_from_tourney(tourney_id)
    for m in matches:
        match = m["match"]
        scores_csv: str = match["scores_csv"]
        scores_list: [] = scores_csv.split("-")
        team1wins = scores_list[0]
        team2wins = scores_list[1]
        team1name: str = c.teams[match['player1_id']]
        team2name: str = c.teams[match['player2_id']]

        print(f"{team1wins}, {team2wins}, {team1name}, {team2name}")


if __name__ == '__main__':
    main()
