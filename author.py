#!/usr/bin/env python3

import sys
from urllib.request import urlopen
import json

response = urlopen(f"https://api.github.com/repos/OI-wiki/OI-WIki/commits?path={sys.argv[1]}")

commits = json.loads(response.read())

for commit in commits:
    if commit["author"]["login"].startswith("24OI"):
        continue

    print(commit["author"]["login"], commit["commit"]["author"]["name"], commit["commit"]["author"]["email"])
