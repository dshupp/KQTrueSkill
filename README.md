This tool uses historical match results at KQ invitationals to calculate estimated skills for players, according to the TrueSkill algorithm. Goals include: 
- create a complete historical dataset for tournament play, with game wins/losses tracked for each player and team, and player names normalized across teams
- this dataset is inteded for use by future projects to inform discussions on team balance, player development, and game analysis
- as an example of analysis you can do with this dataset, calculate relative rankings of KQ players at current and historical times, including a numerical skill estimate and a confidence level

## Roadmap

    Use cases to explore
        Leaderboard 
            - Trueskill can be used to provide a ranking for all players.
            - Current understanding is that Trueskill is really only valid as a snapshot at a point time.   
        Balancing teams 
            - How do you use trueskill to run a draft tournament?
        Tournament Predictions
            - Am I better than a bot at picking tournament placements?     
    
    Questions about Trueskill and KQ
        How predictive is Trueskill for KQ?
            - Are there other ways to benchmark other than predictive power?                  
        What does improvement look like when you're tracking trueskill across tournaments? 
            - How much does a tournament change a player's trueskill?
        How much does including/excluding data affect predictiveness?
            - How much does the data from a group stage affect predictive power?
            - How much does local league night data improve the accuracy of rankings in tournaments?
            - How much does it change my ranking to exclude tournaments from back when I sucked
        How does changing the algorithm affect its performance? 
            - How does weighting the impact of queens vs drones affect predictiveness
            - How does messing with Beta
            
            
    Current Priority: add all touramnet KO & Group stages from all KQ invitationals
    
    Next: Review results, benchmark predictive power vs tournaments
    
    Future:
        - Track a player's skill over time
        

## Project contents 

KQtrueskill.py - Python object that builds a complete history from canonical player and match datasets, does some simple data validation, and runs trueskill on the matches

/datasets - scrubbed, canonical player and match results files for different tournaments.  

/ingest_tools: 
- challengeingest.py - builds a match results files from challong with 'XXX' for errors that need scrubbing  
- players.py - builds a player file for a tournmaent from a sanitized version of the team sheet 

PlayerSkill.csv - Trueskill by player for the current set of tournaments


## Currently tracked tournaments
    2016: ['KQXV']
    2017: ['GDC2', 'Coro17s', 'KQXX', 'Camp17', 'Coro17f']
    2018: ['CC1', 'GDC3', 'MCS-MPLS', 'Coro18s', 'MCS-CHI', 'KQXXV', 'MCS_KC', 'MGF1', 'HH1', 'MCS-CBUS', 'BB3', 'CHA_HT']
    2019: ['CC2', 'QGW19', 'KQC3', 'GDC4', 'Coro19', 'GFT', 'KQ30', 'Camp19', 'MGF2', 'ECC1', 'BBrawl4', 'BB4', 'HH2']
    2020: ['CC3', 'QGW20']
    
If you'd like to see a tournament added to the list, send dshupp@gmail.com links to the teamsheet and challonge

***
## Trueskill notes
Trueskill was built by Microsoft for matchmaking in Halo, which is, like KQ, a team game where team members change between games.  It estimates skill for each player based on wins and losses. It also measures how statistically confident it is in its estimate so far.    

A player's skill is represented as a normal distribution with mean mu (representing perceived skill) and a variance of sigma (representing how "unconfident" the system is in the player's mu value. This means that Trueskill is 95% confident that a player's true skill is at least mu - 2 * sigma.  

All players start with mu = 25 and sigma = 25/3; mu always increases after a win and always decreases after a loss, and how much it changes depends on how surprising the result was, given the players involved. Unbalanced games, for example, don't affect percieved skill much when the favorite wins, but affects it more in an upset.

The best way to improve your 'trueskill' is to win a match between balanced teams.  

Since game order matters in trueskill, we use the match time for all tournament games, and process them in historical order

### FAQ
Q: Are my old tournament performances from when I was new keeping my ratings low? 

A: Very little, if at all. The algorithm assumes that your skill level is changing over time, 
and it takes a few dozen games to adjust to a new skill level, so within a tournament or two 
it will have you pegged at your current level, and the effects of older tournaments will fade.

## Known Data Issues
### Tournaments where we can't find the Team Sheet
    Coronation 2015, 2016
    GDC 1
### Tournaments where we can't find the Challonge
    Camp 2017 Groups, Camp 2019 Groups
### Matches with missing data
    None currently
    
### Teams with missing players

    GDC3: Better than bots, Better than bots 5, 
    BB3: Warp World, Warp World 5, 
    BB3: BeeDeeOhNo, BeeDeeOhNo 5, 
    BB3: Show Me Your Boops, Show Me Your Boops 4, 
    BB3: Show Me Your Boops, Show Me Your Boops 5, 
    KQXX: Blood HoNYC, George, 
    KQXX: Kogan's Heroes, Kogan's Heroes 5, None
    KQXX: What Hive School Did You Go To?, Morgan Ryman, 
    KQXX: Superteam: Return of the Private Cab, Bryan Boyer, 
    KQXX: Superteam: Return of the Private Cab, David Spencer, 
    KQXX: Rob's Slobs, Miranda, 
    KQXX: Garbage Snail Kids, Garbage Snail Kids 5, None
    KQXV: Fake Palidrones, Fake Palidrones 1, None
    KQXV: Fake Palidrones, Fake Palidrones 2, None
    KQXV: Fake Palidrones, Fake Palidrones 3, None
    KQXV: Fake Palidrones, Fake Palidrones 4, None
    KQXV: Fake Palidrones, Fake Palidrones 5, None
    KQXV: Harambae Watch, Harambae Watch 1, None
    KQXV: Harambae Watch, Harambae Watch 2, None
    KQXV: Harambae Watch, Harambae Watch 3, None
    KQXV: Harambae Watch, Harambae Watch 4, None
    KQXV: Harambae Watch, Harambae Watch 5, None
    MCS-CHI: Mad Chuck, Mad Chuck 1, None
    MCS-CHI: Mad Chuck, Mad Chuck 2, None
    MCS-CHI: Mad Chuck, Mad Chuck 3, None
    MCS-CHI: Mad Chuck, Mad Chuck 4, None
    MCS-CHI: Mad Chuck, Mad Chuck 5, None
    MGF1: Y U Dumb Tho?, Y U Dumb Tho? 5, None
    BBrawl4: Some Side Cab Scrubs, Anna Willoughby, 
    QGW19: 3 Dollar PBRs, 3 Dollar PBRs 4, None
    QGW19: 3 Dollar PBRs, 3 Dollar PBRs 5, None