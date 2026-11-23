"""Parts shared by every kind of data (weather is one of them).

config   where the public API is (given at run time, never in the code)
http     GET requests to the public API and its errors
doi      versioned and unversioned DOIs
periods  months in a range of dates
versions choosing one DOI per month (current, canonical, as_of, or by month)
monthly  data published as one file per month (weather, and later others)
cite     citations through doi.org content negotiation
"""
