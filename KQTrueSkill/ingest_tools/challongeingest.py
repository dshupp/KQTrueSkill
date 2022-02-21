import csv
import datetime
import configparser
import requests
import json
import challonge

from KQTrueSkill.KQtrueskill import KQTrueSkill


class ChallongeAccount:
    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    API_URL: str = "https://api.challonge.com/v1/"

    def __init__(self, api_key: str, subdomain: str):
        self.subdomain = subdomain
        if subdomain is None:
            self.subdomain_inject = ''
        else:
            self.subdomain_inject = f"{self.subdomain}-"
        self.api_key = api_key
        challonge.set_credentials('dshupp',api_key)

    # GET https://api.challonge.com/v1/tournaments/{tournament}.{json|xml}
    def print_tournament(self, id):
        print(json.dumps(challonge.tournaments.show(id), indent=1))

    def get_tourney_list(self) -> {}:

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

        self.tourney_object = challonge.tournaments.show(tourney_id)
        self.processing_errors = 0
        self.parent_tourney_name = parent_tourney_name
        self.tourney_id = tourney_id
        self.bracket_name = self.get_bracket_name()
        self.teams = {}
        self.group_ids = {}
        self.team_ids: {} = {}
        self.teamnames: [] = []
        self.build_participants_list()
        self.match_results = []
        self.build_match_results()
        self.first_write = True

    # GET https://api.challonge.com/v1/tournaments/{tournament}.{json|xml}
    def get_tournament_time(self):
        p = self.tourney_object['started_at']
        return datetime.datetime.strptime(p, ChallongeAccount.DATETIME_FORMAT)

    # GET https://api.challonge.com/v1/tournaments/{tournament}/participants.{json|xml}
    def build_participants_list(self):
        for participant in challonge.participants.index(self.tourney_object["id"]):
            team_id = participant['id']
            team_name = participant['name']
            self.teams[team_id] = team_name
            self.team_ids[team_name] = team_id
            self.teamnames.append(team_name)
            for gid in participant['group_player_ids']:
                # in a multistage challonge, the player id in groups is a group_player_id on the participants list
                self.group_ids[gid] = team_name
            # print(f"{team_id}, {team_name}")

    def build_match_results(self):
        print("building match results for "+self.tourney_id)
        for match in challonge.matches.index(self.tourney_id):
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
            elif isinstance(match['player1_id'], int):
                try:
                    team1name = self.get_team_name_from_id(match['player1_id'])
                except:
                    team1name = str(match['player1_id'])
            else:
                team1name: str = self.teams[match['player1_id']]

            if match['player2_id'] is None:
                team2name = 'XXX'
                print(f"ERROR - Empty player2_id in match {match}")
                self.processing_errors += 1
            elif isinstance(match['player2_id'], int):
                try:
                    team2name = self.get_team_name_from_id(match['player2_id'])
                except:
                    team2name = str(match['player2_id'])
            else:
                team2name: str = self.teams[match['player2_id']]

            if match['started_at'] is None:
                time = datetime.datetime.today()
                print(f"ERROR - Empty started_at in match {match}")
                self.processing_errors += 1
            else:
                time = match['started_at']

            self.match_results.append(
                [self.parent_tourney_name, self.bracket_name, team1name, team2name, team1wins, team2wins, time])
        print(f"{self.processing_errors} processing errors")

    def get_bracket_name(self):
        return self.tourney_object['name']

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

    def get_team_name_from_id(self, team_id):
        if team_id in self.teams.keys():
            return self.teams[team_id]

        try:
            name = challonge.participants.show(self.tourney_id,team_id)['name']
        except:
            for participant in challonge.participants.index(self.tourney_id):
                if len(participant['group_player_ids']) > 0:
                    if participant['group_player_ids'][0] == team_id:
                        self.teams[team_id] = challonge.participants.show(self.tourney_id,participant['id'])['name']
                        return self.teams[team_id]
        raise Exception("didn't find a matching team")


# BB3: [] = ['BB3', [{'id': 5057256, 'bracket': 'KO'},
#                    {'id': 5057264, 'bracket': 'Pool1'},
#                    {'id': 5057281, 'bracket': 'Pool2'},
#                    {'id': 5057309, 'bracket': 'Pool3'},
#                    {'id': 5057310, 'bracket': 'Pool4'},
#                    {'id': 5057312, 'bracket': 'Pool5'},
#                    {'id': 5057313, 'bracket': 'Pool6'},
#                    {'id': 5057316, 'bracket': 'Pool7'},
#                    {'id': 5057318, 'bracket': 'Pool8'},
#                    {'id': 5057321, 'bracket': 'Pool9'},
#                    {'id': 5057323, 'bracket': 'Pool10'},
#                    {'id': 5057324, 'bracket': 'WC'},
#                    ]]
#
# HH1: [] = ["HH1", [{'id': 5025209, 'bracket': 'Swiss'},
#                    {'id': 5026099, 'bracket': 'KO'},
#                    ]]
#
# CC1: [] = ["CC1", [{'id': 4230293, 'bracket': 'GroupA'},
#                    {'id': 4233246, 'bracket': 'GroupB'},
#                    {'id': 4233248, 'bracket': 'GroupC'},
#                    {'id': 4223960, 'bracket': 'KO'},
#                    ]]
#
# CC2: [] = ["CC2", [{'id': 5482725, 'bracket': 'GroupA'},
#                    {'id': 5482751, 'bracket': 'GroupB'},
#                    {'id': 5482814, 'bracket': 'GroupC'},
#                    {'id': 5482847, 'bracket': 'KO'},
#                    ]]
#
# CC3: [] = ["CC3", [{'id': 8048812, 'bracket': 'GroupA'},
#                    {'id': 8048841, 'bracket': 'GroupB'},
#                    {'id': 8048854, 'bracket': 'GroupC'},
#                    {'id': 8048858, 'bracket': 'GroupD'},
#                    {'id': 8048880, 'bracket': 'KO'},
#                    ]]
#
# MGF1: [] = ["MGF1", [{'id': 'MGFDE', 'bracket': 'KO'},
#                      {'id': 'MGFUD130', 'bracket': 'GroupUpdown1'},
#                      {'id': 'MGFUDNOON', 'bracket': 'GroupUpdown2'},
#                      ]]
#
# MCS_CBUS: [] = ["MCS-CBUS", [{'id': 'MCSFINALS', 'bracket': 'KO'},
#                              {'id': 'MCSwc', 'bracket': 'WC'},
#                              {'id': 'MCSGroup1', 'bracket': 'Group1'},
#                              {'id': 'MCSGroup2', 'bracket': 'Group2'},
#                              {'id': 'MCSGroup3', 'bracket': 'Group1'},
#                              {'id': 'MCSGroup4', 'bracket': 'Group2'},
#                              ]]
#
# MCS_CHI: [] = ["MCS-CHI", [{'id': 'mcschi', 'name': 'MCS-CHI', 'bracket': 'KO'},
#                            ]]
#
# MCS_MPLS: [] = ["MCS-MPLS", [{'id': 'mcsmpls', 'name': 'MCS-MPLS', 'bracket': 'KO'},
#                              ]]
#
# KQ15: [] = ["KQXV", [{'id': 'KQ15', 'name': 'KGXV', 'bracket': 'KO'},
#                      ]]
#
# KQ20: [] = ["KQXX", [{'id': 'kqxx', 'name': 'KQXX', 'bracket': 'KO'},
#                      {'id': 'kqxxwc', 'name': 'KQXX', 'bracket': 'WC'},
#                      {'id': 'kqxxgroupa', 'name': 'KQXX', 'bracket': 'Groupa'},
#                      {'id': 'kqxxgroupb', 'name': 'KQXX', 'bracket': 'Groupb'},
#                      {'id': 'kqxxgroupc', 'name': 'KQXX', 'bracket': 'Groupc'},
#                      {'id': 'kqxxgroupd', 'name': 'KQXX', 'bracket': 'Groupd'},
#                      {'id': 'kqxxgroupe', 'name': 'KQXX', 'bracket': 'Groupe'},
#                      {'id': 'kqxxgroupf', 'name': 'KQXX', 'bracket': 'Groupf'},
#                      {'id': 'kqxxgroupg', 'name': 'KQXX', 'bracket': 'Groupg'},
#                      {'id': 'kqxxgrouph', 'name': 'KQXX', 'bracket': 'Grouph'},
#                      ]]
#
# KQ25: [] = ["KQXXV", [{'id': 'kqxxv', 'name': 'KQXXV', 'bracket': 'KO'},
#                       {'id': 'kqxxvwc', 'name': 'KQXXV', 'bracket': 'WC'},
#                       {'id': 'kqxxva', 'name': 'KQXXV', 'bracket': 'GroupA'},
#                       {'id': 'kqxxvb', 'name': 'KQXXV', 'bracket': 'GroupB'},
#                       {'id': 'kqxxvc', 'name': 'KQXXV', 'bracket': 'GroupC'},
#                       {'id': 'kqxxvd', 'name': 'KQXXV', 'bracket': 'GroupD'},
#                       {'id': 'kqxxve', 'name': 'KQXXV', 'bracket': 'GroupE'},
#                       {'id': 'kqxxvf', 'name': 'KQXXV', 'bracket': 'GroupF'},
#                       {'id': 'kqxxvg', 'name': 'KQXXV', 'bracket': 'GroupG'},
#                       ]]
#
# # need groups
# Cor17s: [] = ["Cor17s", [{'id': 'BKCRN2017', 'name': 'Cor17s', 'bracket': 'KO'},
#                          ]]
# # need groups
# Cor17f: [] = ["Cor17f", [{'id': 'BKCFall2017', 'name': 'Cor17f', 'bracket': 'KO'},
#                          ]]
#
# # uses group stages in challonge
# Cor18s: [] = ["Cor18s", [{'id': 'springcoronation2018', 'name': 'Cor18s', 'bracket': 'KO'},
#                          ]]
#
# Cor19: [] = ["Cor19", [{'id': 'Coro2019', 'name': 'Cor19', 'bracket': 'KO'},
#                        {'id': 'Coro2019wc', 'name': 'Cor19', 'bracket': 'WC'},
#                        {'id': 'Coro2019Group1', 'name': 'Cor19', 'bracket': 'Group1'},
#                        {'id': 'Coro2019Group2', 'name': 'Cor19', 'bracket': 'Group2'},
#                        ]]
#
# MCS_KC: [] = ["MCS_KC", [{'id': 'KCKQMCS', 'bracket': 'KO'},
#                          ]]
#
# # https://docs.google.com/spreadsheets/d/1MqwEoKrd4gpCt0zgamePn3mtFt4WKx-cJfYq8Gc5ddI/edit#gid=0
# BBrawl4: [] = ["BBrawl4", [{'id': 'baltimorebrawlfour', 'bracket': 'KO'},
#                            {'id': 'baltimorebrawlwildcard', 'bracket': 'WC'},
#                            {'id': 'baltimorebrawlpoola', 'bracket': 'Group1'},
#                            {'id': 'baltimorebrawlpoolb', 'bracket': 'Group2'},
#                            ]]
#
# # https://docs.google.com/spreadsheets/d/1vIbZ4XPye3dsXB1wVuP-w3Wj4lGjLO8y5w7_ksSyUTE/edit?fbclid=IwAR1UOiEkgERBXM0eZc9sBucn2I5AyuWXTpZgf_vTwi1aoGRIhgqHt7HxHEs#gid=0
# QGW20: [] = ["QGW20", [{'id': 'QGW2020_DE', 'bracket': 'KO'},
#                        {'id': 'QGW2020_WC', 'bracket': 'WC'},
#                        {'id': 'QGW2020_GA', 'bracket': 'Group1'},
#                        {'id': 'QGW2020_GB', 'bracket': 'Group2'},
#                        {'id': 'QGW2020_GC', 'bracket': 'Group3'},
#                        {'id': 'QGW2020_GD', 'bracket': 'Group4'},
#                        ]]
#
# # Queens gone Wild 2019: https://docs.google.com/spreadsheets/d/1wwmeDl_QMP9liZWQTBVH7ew0JCCbW10VMDW0Y8wWdJY/edit?fbclid=IwAR1IwbzQ01cNzFDXiuzOSy1FyWyXNzW7SEA5NJvUbD3joiGyE9Rd_-zeY10#gid=0
# # https://hybridhypegaming.challonge.com/KQSFLFinals https://hybridhypegaming.challonge.com/8lw9xk6t https://hybridhypegaming.challonge.com/tw2mfmjg https://hybridhypegaming.challonge.com/f9lqxz8p https://hybridhypegaming.challonge.com/xqmd6gv4
# QGW19: [] = ["QGW19", [{'id': 'KQSFLFinals', 'bracket': 'KO'},
#                        {'id': '8lw9xk6t', 'bracket': 'Group1'},
#                        {'id': 'f9lqxz8p', 'bracket': 'WC'},
#                        {'id': 'tw2mfmjg', 'bracket': 'Group2'},
#                        {'id': 'xqmd6gv4', 'bracket': 'Group3'},
#                        ]]
# # https://docs.google.com/spreadsheets/d/1Jy0Ri9qBXm8M6uwbwS7htWCSnR_0sGeXEQQFJ-UqbeY/edit#gid=1999874923
# GFT: [] = ["GFT", [{'id': 'kckqGFT', 'bracket': 'KO'},
#                    ]]
#
# Hive City Classic 2021: https://docs.google.com/spreadsheets/d/12nkN7CFZ0DpeK-M1TzgVZ42SpuTnoJwRNFnq5ZZbHWg/edit#gid=175151071
# https://challonge.com/HCC_GA https://challonge.com/HCC_GB https://challonge.com/HCC_GC https://challonge.com/HCC_KO
HCC21: [] = ["HCC21", [{'id': 'HCC_GA', 'bracket': 'Group1'},
                       {'id': 'HCC_GB', 'bracket': 'Group2'},
                       {'id': 'HCC_GC', 'bracket': 'Group3'},
                       {'id': 'HCC_KO', 'bracket': 'KO'},
                       ]]
#
# City-State Swat https://docs.google.com/spreadsheets/d/14uoTbnH7DCwF63xc0UReMBlNqorooDeqonXKS-2sEQ8/edit?fbclid=IwAR2mBg4z48OVkV4HR06FB86rkCdZb7cRftarvtKAcIsFB6gzODE4Qtftdv0#gid=0
# https://challonge.com/csswat/
CSSwat1: [] = ["CSSwat1", [{'id': 'csswat', 'bracket': 'KO'},
#                           {'id': 'csswat/groups', 'bracket': 'Groups'},
                           ]]
#
# # https://docs.google.com/spreadsheets/d/1Jy0Ri9qBXm8M6uwbwS7htWCSnR_0sGeXEQQFJ-UqbeY/edit#gid=1999874923
# GFT: [] = ["GFT", [{'id': 'kckqGFT', 'bracket': 'KO'},
#                    ]]
#
# # Nooga Hive Turkey - https://docs.google.com/spreadsheets/d/1xvGTsCpQwBVCIwXfn7IB4sfZIlKSsFyoRBH8q4D0ync/edit#gid=1808814704
# CHA_HT: [] = ["CHA_HT", [{'id': 'Hiveturkeyfinals', 'bracket': 'KO'},
#                          {'id': 'Hiveturkeyswiss', 'bracket': 'WC'},
#                          ]]
#
# BnB1: [] = ["BnB1", [{'id': 'batb17', 'bracket': 'KO'},
#                      ]]
# BnB2: [] = ["BnB2", [{'id': 'bandb2', 'bracket': 'KO'},
#                      ]]
# BnB3: [] = ["BnB3", [{'id': 'bandb3', 'bracket': 'KO'},
#                      ]]
# MAD420: [] = ["MAD420", [{'id': 'KQBuds420', 'bracket': 'KO'},
#                          {'id': 'KQBuds1', 'bracket': 'Group1'},
#                          {'id': 'KQBuds2', 'bracket': 'Group2'},
#                          ]]
#
# # no groups
# GDC1: [] = ["GDC1", [{'id': 'SFGDC', 'name': 'GDC1', 'bracket': 'KO'},
#                      ]]
#
# GDC2: [] = ["GDC2", [{'id': 'kqgdc2', 'name': 'GDC2', 'bracket': 'KO'},
#                      ]]
#
# Camp17: [] = ["Camp17", [{'id': 'campkq', 'bracket': 'KO'},
#                          ]]
#
# Camp19: [] = ["Camp19", [{'id': 'campkq2019', 'bracket': 'KO'},
#                          ]]
#
# ECC1: [] = ["ECC1", [{'id': 'ECC2019finals', 'bracket': 'KO'},
#                      {'id': 'ECC2019poolA', 'bracket': 'Group1'},
#                      {'id': 'ECC2019poolB', 'bracket': 'Group2'},
#                      ]]
#
# BB1: [] = ["BB1", [{'id': 'KQBBFinals', 'bracket': 'KO'},
#                    {'id': 'KQBBWC', 'bracket': 'WC'},
#                    {'id': 'KQBB1', 'bracket': 'Group1'},
#                    {'id': 'KQBB2', 'bracket': 'Group2'},
#                    {'id': 'KQBB3', 'bracket': 'Group3'},
#                    {'id': 'KQBB4', 'bracket': 'Group4'},
#                    {'id': 'KQBB5', 'bracket': 'Group5'},
#                    ]]
# BB2: [] = ["BB2", [{'id': 'BB2Knockout', 'bracket': 'KO'},
#                    {'id': 'bb2wildcard', 'bracket': 'WC'},
#                    {'id': 'BB2groupa', 'bracket': 'Group1'},
#                    {'id': 'BB2groupb', 'bracket': 'Group2'},
#                    {'id': 'BB2groupc', 'bracket': 'Group3'},
#                    {'id': 'BB2groupd', 'bracket': 'Group4'},
#                    {'id': 'BB2groupe', 'bracket': 'Group5'},
#                    {'id': 'BB2groupf', 'bracket': 'Group6'},
#                    {'id': 'BB2groupg', 'bracket': 'Group7'},
#                    {'id': 'BB2grouph', 'bracket': 'Group8'},
#                    ]]
#
# WC1: [] = ["WC1", [{'id': 'WinterClusterFinals', 'bracket': 'KO'},
#                 {'id': 'WinterClusterWildCard', 'bracket': 'WC'},
#                 {'id': 'WinterClusterGroups', 'bracket': 'Groups'},
#                 ]]
# # KQWC2Pools has pools and a fake DE together in the same challonge
# WC2: [] = ["WC2", [{'id': 'KQWC2Finals', 'bracket': 'KO'},
#                 {'id': 'KQWC2WildCard', 'bracket': 'WC'},
#                 {'id': 'KQWC2Pools', 'bracket': 'Groups'},
#                 ]]
# WC3: [] = ["WC3", [{'id': 'WinterCluster3', 'bracket': 'KO'},
#                 {'id': 'WC3Group1', 'bracket': 'Group1'},
#                 {'id': 'WC3Group2', 'bracket': 'Group2'},
#                 {'id': 'WC3Group3', 'bracket': 'Group3'},
#                 ]]
#
# SSwarm1: [] = ["SS1", [{'id': 'SummerSwarmDE', 'bracket': 'KO'},
# # groups challonge contains groups & a DE tourney with diff't results from the KO. using KO results, filter those out
#                        {'id': 'SummerSwarm', 'bracket': 'Groups'},
#                     ]]
#
# SSwarm2: [] = ["SS2", [{'id': 'SummerSwarm2', 'bracket': 'KO'},
#                     {'id': 'SummerSwarm2A', 'bracket': 'Group1'},
#                     {'id': 'SummerSwarm2B', 'bracket': 'Group2'},
#                     {'id': 'SummerSwarm2C', 'bracket': 'Group3'},
#                     ]]
# CBM2018: [] = ["CBM2018", [{'id': 'kh0ywbvz', 'bracket': 'KO'},
#                     ]]

# WH1: [] = ["WH1", [{'id': 'KQJaxWinterHarvest2018', 'bracket': 'KO'},
#                     ]]
#
# WH2: [] = ["WH2", [{'id': 'kqjaxwh2020', 'bracket': 'KO'},
#                     ]]
# KQC2: [] = ["KQC2", [{'id': 'kqci2', 'bracket': 'KO'},
#                      ]]
# KQC4: [] = ["KQC4", [{'id': 'kqc4', 'bracket': 'KO'},
#                      {'id': 'kqc4a', 'bracket': 'Group1'},
#                      {'id': 'kqc4b', 'bracket': 'Group2'},
#                      {'id': 'kqc4c', 'bracket': 'Group3'},
#                      ]]
# DSM1: [] = ["DSM1", [{'id': '658n8vsq', 'bracket': 'KO'},
#                      ]]
# HIVE_FEST: [] = ["HF", [{'id': 'hivefest', 'bracket': 'KO'},
#                         ]]
# processed tourneys go above this line

BBR: [] = ["BBR", [{'id': 'BB_Remix', 'bracket': 'KO'},
                     {'id': 'BB_Remix_GroupA', 'bracket': 'GroupA'},
                     {'id': 'BB_Remix_GroupB', 'bracket': 'GroupB'},
                     {'id': 'BB_Remix_GroupC', 'bracket': 'GroupC'},
                     {'id': 'BB_Remix_GroupD', 'bracket': 'GroupD'},
                     ]]

# subtourney_id: int = 5689203  # GDC4 Groups 1
# subtourney_id: int = 4415714  # GDC3 DE

# groups?
# Cor15: [] = ["Cor15", [{'id': 'BrooklynCoronation2015', 'name': 'Cor15', 'bracket': 'KO'},
#                        ]]
#
# # https://ehgaming.challonge.com/users/charlesjpratt/tournaments
# Cor16: [] = ["Cor16", [{'id': 'BrooklynCoronationFall2016', 'name': 'Cor16', 'bracket': 'KO'},
#                        ]]
# No Team Sheet
# CLT1: [] = ["CLT1", [{'id': 'KQCInvitational', 'bracket': 'KO'},
#                      ]]



# can't imprt this challonge rn
# MM19: [] = ["MM19", [{'id': 'MantisMayhem2019_Finals', 'bracket': 'KO'},
#                      {'id': 'MantisMayhem2019', 'bracket': 'Groups'},
#                      ]]

# TEMPLATE[0] = the tourney identifier KQTrueskill will use
# TEMPLATE[1] = list of dictionaries, one dict for each challonge url
TEMPLATE: [] = ["", [{'id': '', 'bracket': 'KO'},
                     {'id': '', 'bracket': 'WC'},
                     {'id': '', 'bracket': 'Group1'},
                     {'id': '', 'bracket': 'Group2'},
                     ]]


# needs:
# Coro 17s/f groups?


def get_match_results_from_challonge(account, tourney_name, subtourney_list, filename, append=False):
    first_write = True
    for subtourney in subtourney_list:
        ct: ChallongeTournament = account.get_tournament(tourney_name, subtourney['id'], subtourney['bracket'])
        ct.write_matchfile(filename, append or not first_write)
        first_write = False


# importing a new dataset starts here.
# start with challonge links, and create an object of the

# scripts for importing a tournament from ingest_tools and getting it into an editable csv that can be read into a KQ history


def main():
    # cp: configparser.RawConfigParser = configparser.RawConfigParser()
    # cp.read('properties/api_keys.cfg')
    # api_key = cp.get('APIKeys', '')

    account: ChallongeAccount = ChallongeAccount('OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd', None)
    account_kqsf: ChallongeAccount = ChallongeAccount('OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd', 'kq-sf')
    account_sfl: ChallongeAccount = ChallongeAccount('OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd', 'hybridhypegaming')
    account_stl: ChallongeAccount = ChallongeAccount('OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd', 'killerqueenstl')
    account_cha: ChallongeAccount = ChallongeAccount('OJxf8wmFKHb5afldGJ1HzTn5Omg4s7BcuevuQXCd',
                                                     'killer-queen-chattanooga')


    # account.print_tournament('BKCRN2017')

    # get_match_results_from_challonge(account, KQC2[0], KQC2[1], 'tmp.csv', append=False)
    # get_match_results_from_challonge(account, KQC4[0], KQC4[1], 'tmp.csv', append=True)
    # get_match_results_from_challonge(account, MM19[0], MM19[1], 'tmp.csv', append=True)
    # get_match_results_from_challonge(account, HIVE_FEST[0], HIVE_FEST[1], 'tmp.csv', append=True)

    # get_match_results_from_challonge(account, HCC21[0], HCC21[1], 'tmp.csv', append=False)
    # get_match_results_from_challonge(account, CSSwat1[0], CSSwat1[1], 'tmp.csv', append=True)
    # get_match_results_from_challonge(account, BBR[0], BBR[1], 'tmp.csv', append=True)



    # template/examples
    # get_match_results_from_challonge(account, [0], [1], 'tmp.csv', append=False)
    # get_match_results_from_challonge(account, [0], [1], 'tmp.csv', append=True)
    # get_match_results_from_challonge(account, [0], [1], 'tmp2.csv', append=False)
    # get_match_results_from_challonge(account_cha, CHA_HT[0], CHA_HT[1], '2019 misc game results.csv', append=True)


if __name__ == '__main__':
    main()
