import requests
import csv
import polars as pl
from datetime import date

BASE_URL = ""
AUTH_KEY = "<YOUR_AUTH_KEY>"


def get_initial_data():
    with open("matches.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        matches = [row for row in reader]
    with open("events.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        events = [row for row in reader]
    return matches, events


def get_all_events():
    """
    Get all historical events from the Bandai TCG+ API.
    """
    events_total = 99999
    events_gathered = []
    while len(events_gathered) < events_total:
        url = f"https://api.bandai-tcg-plus.com/api/user/my/event?country_code[]=US&pref_code[]=&limit=100&past_event_display_flg=1&selected_tab=3&favorite=0&game_title_id=&offset={len(events_gathered)}&start_date=2021-01-01"
        headers = {"x-accept-version": "v1", "X-Authentication": AUTH_KEY}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break
        events = response.json().get("success")
        events_total = int(events.get("total"))

        def format_event(event):
            return {
                "id": event.get("id"),
                "start_datetime": event.get("start_datetime"),
                "event_series_title": event.get("event_series_title"),
                "is_area_championship": event.get("is_area_championship"),
                "online_flag": event.get("online_flag"),
            }

        event_ids = [format_event(event) for event in events.get("events")]
        events_gathered = [*events_gathered, *event_ids]
        print(f"Gathered {len(events_gathered)} events out of {events_total}")
    return events_gathered


def get_matches(event):
    url = f"https://api.bandai-tcg-plus.com/api/user/my/event/{event.get('id')}"
    headers = {"x-accept-version": "v1", "X-Authentication": AUTH_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    rankings = (
        response.json().get("success", {}).get("rankings", {}).get("rankings", False)
    )
    ret = []
    if rankings:
        for ranking in rankings:
            r = {
                "win_count": int(ranking.get("win_count")),
                "lose_count": int(ranking.get("lose_count")),
                "draw_count": int(ranking.get("draw_count")),
                "game_win_percentage": float(
                    ranking.get("game_win_percentage").replace("%", "")
                ),
                "membership_number": str(
                    ranking.get("users")[0].get("membership_number")
                ),
                "player_name": str(ranking.get("users")[0].get("player_name")),
                "event_id": str(event.get("id")),
                "start_datetime": str(event.get("start_datetime")),
                "event_series_title": str(event.get("event_series_title")),
                "is_area_championship": str(event.get("is_area_championship")),
                "online_flag": str(event.get("online_flag")),
            }
            ret.append(r)
    else:
        print(f"No rankings found for event {event.get('event_series_title')}")
        print(response.json())
    return ret


def write_raw_data(data_file, name):
    with open(f"{name}.csv", "w", newline="") as csvfile:
        fieldnames = data_file[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ranking in data_file:
            writer.writerow(ranking)


def generate_rankings(rankings):
    df = pl.DataFrame(rankings)
    today = date.today().strftime("%Y_%m_%d")
    agg = (
        df.group_by("membership_number")
        .agg(
            pl.col("player_name").implode().alias("player_names"),
            pl.col("game_win_percentage").mean().alias("game_win_percentage"),
            pl.col("win_count").sum().alias("win_count"),
            pl.col("lose_count").sum().alias("lose_count"),
            pl.col("draw_count").sum().alias("draw_count"),
            pl.len().alias("events_played"),
        )
        .with_columns(pl.col("player_names").list.unique().list.join(" | "))
        .sort("game_win_percentage", descending=True)
    )
    agg.write_csv(f"rankings_{today}.csv")


def deduplicate(data, columns):
    """
    Deduplicate the data based on the specified column.
    """
    df = pl.DataFrame(data)
    deduped_df = df.unique(subset=columns)
    return deduped_df.to_dicts()


def main():
    """
    Main function to run the script.
    """
    # Get all events

    new_events = get_all_events()
    new_matches = []
    for event in new_events:
        event_matches = get_matches(event)
        new_matches = [*new_matches, *event_matches]

    init_matches, init_events = get_initial_data()
    print(f"Initial events: {len(init_events)}")
    print(f"New events: {len(new_events)}")
    events = deduplicate([*new_events, *init_events], ["id"])
    print(f"Merged Events: {len(events)}")
    print(f"Initial matches: {len(init_matches)}")
    print(f"New matches: {len(new_matches)}")
    matches = deduplicate(
        [*new_matches, *init_matches], ["event_id", "membership_number"]
    )
    print(f"Merged Matches: {len(matches)}")
    generate_rankings(matches)
    write_raw_data(matches, "matches")
    write_raw_data(events, "events")


if __name__ == "__main__":
    main()
