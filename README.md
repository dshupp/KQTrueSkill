This tool uses historical match results at KQ invitationals to calculate estimated skills for players, according to the TrueSkill algorithm. Goals include: 
- create a scrubbed, usable, complete historical dataset for tournament play
- calculate relative rankings of KQ players at current and historical times, including a numerical skill estimate and a confidence level
- inform discussions on team balance, player skills, and game analysis


Currently includes: 
KQtrueskill.py - Python object that builds a complete history from canonical player and match datasets, does some simple data validation, and runs trueskill on the matches
/datasets - scrubbed, canonical player and match results files for different tournaments.  
/ingest_tools: 
- challengeingest.py - builds a match results files from challong with 'XXX' for errors that need scrubbing  
- smashingest.py (future, if needed)
- players.py - builds a player file for a tournmaent from a sanitized version of the team sheet 

PlayerSkill.csv - Trueskill by player for the current set of tournaments

    2018: ['GDC3', 'HH1', 'BB3']
    2019: ['KQC3', 'GDC4', 'KQ30', 'MGF2', 'BB4', 'HH2']

If you'd like to see a tournament added to the list, send dshupp@gmail.com links to the teamsheet, the challonge, and the Challonge API key for the account that created the challonge. 