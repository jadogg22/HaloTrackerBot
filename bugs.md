# bugs

this is just a mental note of buts and things to fix for now.

## match_cache

[] - get_recent_match_data - need to update the sql to only get todays data and yesterdays
data just incase we started before midnight and ended after midnight. right now
its getching all data, thats going to start getting slow as the db get bigger.
