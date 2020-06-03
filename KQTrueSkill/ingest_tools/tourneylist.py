import requests


class ChallongeAccount:
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
            raise Exception('GET /index/ {}'.format(resp.status_code))
        return resp.json()

    def print_tourney_list(self):
        tourneys: [] = self.get_tourney_list()
        for t in tourneys:
            print(f"{t['tournament']['name']}, {t['tournament']['url']}, {t['tournament']['id']}")
        pass


def main():
    # script to list all tourneys and asssociated challonge ids on an account

    api_key = 'OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd'

    subdomain = None  # get the tourneys from a larger challonge org that your account is part of

    account: ChallongeAccount = ChallongeAccount(api_key, subdomain)
    account.print_tourney_list()


if __name__ == '__main__':
    main()
