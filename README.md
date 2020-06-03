This tool uses historical match results at KQ invitationals to calculate estimated skills for players, according to the TrueSkill algorithm. Goals include: 
- create a scrubbed, usable, complete historical dataset for tournament play
- calculate relative rankings of KQ players at current and historical times, including a numerical skill estimate and a confidence level
- inform discussions on team balance, player skills, and game analysis


Currently includes: 

KQtrueskill.py - Python object that builds a complete history from canonical player and match datasets, does some simple data validation, and runs trueskill on the matches

/datasets - scrubbed, canonical player and match results files for different tournaments.  

/ingest_tools: 
- challengeingest.py - builds a match results files from challong with 'XXX' for errors that need scrubbing  
- players.py - builds a player file for a tournmaent from a sanitized version of the team sheet 

PlayerSkill.csv - Trueskill by player for the current set of tournaments

### Currently tracked tournaments
    2016: ['KQXV']
    2017: ['KQXX']
    2018: ['CC1', 'GDC3', 'MCS-MPLS', 'MCS-CHI', 'KQXXV', 'MGF1', 'HH1', 'MCS-CBUS', 'BB3']
    2019: ['CC2', 'KQC3', 'GDC4', 'KQ30', 'MGF2', 'BB4', 'HH2']
    2020: ['CC3']
    
If you'd like to see a tournament added to the list, send dshupp@gmail.com links to the teamsheet and challonge

***
## Known Data Issues

### Tournaments where we can't find the Challonge
    Challonge for MCS KC

### Matches with missing data
    CC2,GroupC,I DIED AND I'M SORRY,Fifth Wheel,XXX,XXX,2019-01-26T17:30:46-0500 # currently logged as 2-0 Fifth Wheel
    
### Teams with missing players

    GDC3: Better than bots, Better than bots 5, 
    BB3: Warp World, Warp World 5, 
    BB3: BeeDeeOhNo, BeeDeeOhNo 5, 
    BB3: Show Me Your Boops, Show Me Your Boops 4, 
    BB3: Show Me Your Boops, Show Me Your Boops 5, 
    KQXX: Blood HoNYC, George, 
    KQXX: Kogan's Heroes, Dj, 
    KQXX: Kogan's Heroes, Melissa G., 
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