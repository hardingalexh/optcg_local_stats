# OPTCG Local Stats
This repo contains a python script for pulling matches from a user's history, aggregating them, and generating rankings.

## Rankings
Note that the ranking is based on your *average winrate* not your *historical total winrate*. IE: who is most frequently successful, not who is overall the most successful in aggregate.

## Usage
Install the required dependencies from the `requirements.txt` file and run `python main.py`.

You can run the following to start:

```sh
python3 -m venv ./.venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Authentication
You will need your auth key from Bandai TCG+. To get this, log in to BTCG+ on the web, open the dev tools of the browser of your choosing, go to the JavaScript console, and type `localStorage.userToken` then copy the result to the `AUTH_KEY` variable in `main.py`. Also ensure you don't commit that key if you're using this repository.

## Outputs
* `events.csv` A log of all events that the data contains
* `matches.csv` The raw data, where each row is a user's performance in an event gathered by this app
* `rankings_<date>.csv` The current rankings based on the aggregated data