import os
import time
from functools import partial
from parser import (
    bhaktapur_two_votes,
    chitwan_two_votes,
    dadeldura_one_votes,
    get_current_time,
    get_data,
    kathmandu_one_votes,
    kathmandu_four_votes,
    kathmandu_five_votes,
    kathmandu_seven_votes,
    lalitpur_three_votes,
    party_shortform,
    saptari_two_votes,
)

import praw
from dotenv import load_dotenv

USERNAME = "election-bot-2079"
# SUBMISSION_IDS = ["upmnp6"]
SUBMISSION_IDS = ["z0opw6"]

load_dotenv()

FETCH_LIST = [
    "pradesh-7/district-dadeldhura",
    "pradesh-3/district-kathmandu",
    "pradesh-3/district-bhaktapur",
    "pradesh-3/district-lalitpur",
    "pradesh-3/district-chitwan",
    "pradesh-2/district-saptari",
]


def login(username):
    # rnepal-bot -> RNEPALBOT | link_guru -> LINK_GURU
    BOT_NAME = username.replace("-", "").upper()
    reddit = praw.Reddit(
        client_id=os.getenv(f"{BOT_NAME}_ID"),
        client_secret=os.getenv(f"{BOT_NAME}_SECRET"),
        user_agent=os.getenv(f"{BOT_NAME}_USERAGENT"),
        username=username,
        password=os.getenv(f"{BOT_NAME}_PASS"),
    )
    return reddit


def main():
    api_data = get_data(FETCH_LIST)
    election_area_map = {
        "Kathmandu 1": partial(kathmandu_one_votes, api_data),
        "Kathmandu 4": partial(kathmandu_four_votes, api_data),
        "Kathmandu 5": partial(kathmandu_five_votes, api_data),
        "Kathmandu 7": partial(kathmandu_seven_votes, api_data),
        "Lalitpur 3": partial(lalitpur_three_votes, api_data),
        "Saptari 2": partial(saptari_two_votes, api_data),
        "Bhaktapur 2": partial(bhaktapur_two_votes, api_data),
        "Dadeldhura 1": partial(dadeldura_one_votes, api_data),
        "Chitwan 2": partial(chitwan_two_votes, api_data),
    }

    source = (
        "**Election Data Source**: https://election.ekantipur.com?lng=eng\n\n"
        "**All Party/Candidates PowerBi Visualization by u/authorsuraj**: [PowerBi Link](https://app.powerbi.com/view?r=eyJrIjoiNTU4NDY2YTYtMDU0MS00M2I5LWJjMTAtZGY5MGE5M2IyNGE3IiwidCI6ImNiNzIwMDNkLWYwMjctNDgwMC1hMWZkLTYwYzVmYjRmYmU0OCJ9&pageName=ReportSection)\n\n"
        "**Official And Detailed Election Data**: [Official ECN website](https://result.election.gov.np/ElectionResultCentral2079.aspx)\n\n"
        f"**Last updated**: {get_current_time()} (UTC: {get_current_time(utc=True)})"
    )
    news = (
        "# News of Interest\n"
        "- [Setopati Analysis of Core kathmandu Votes: Game Over, Sthapit and Singh will fight for second spot]"
        "(https://en.setopati.com/political/158516)"
        "\n\n\n\n"
    )
    footer = (
        "*contribute*: "
        "[Bot code](https://github.com/pykancha/reddit-bots) |"
        "[API code](https://github.com/hemanta212/nepal-election-api) |"
        "[API url for your personal automation](https://electionapi.osac.org.np)"
    )
    text = ""
    print("Started fetching at: ", get_current_time())
    for city, data in election_area_map.items():
        try:
            text += gen_msg(city, data)
        except Exception as e:
            print("Failed generating text, Skipping this time", e, city)
            return
        time.sleep(1)
    print("Info fetched completed at: ", get_current_time())

    submission_body = f"{text}\n\n\n\n{footer}"
    cached_submission = ""
    try:
        with open("cache.json", "r") as rf:
            cached_submission = rf.read()
    except Exception as e:
        print("Error: Reading cache file failed", e)

    if cached_submission == submission_body:
        print("Cached matched: No new updates")
        return

    print("Cached unmatched: Updating")
    # IMP: Write to cache before inserting timestamp for next time comparision
    with open("cache.json", "w") as wf:
        wf.write(submission_body)

    submission_body = f"{source}\n\n{text}\n\n\n\n{footer}"

    reddit = login(USERNAME)
    submissions = [reddit.submission(i) for i in SUBMISSION_IDS]

    print(submissions)
    for submission in submissions:
        body = (
            submission.selftext if not hasattr(submission, "body") else submission.body
        )
        body_list = body.strip().split("\n")
        text_list = submission_body.strip().split("\n")
        body_list.remove(body_list[2])
        text_list.remove(text_list[2])
        if body_list == text_list:
            print("No new updates")
        else:
            print(submission.author)
            try:
                submission.edit(body=submission_body)
            except Exception as e:
                print("Praw submit error Skipping this time..", e)


def gen_msg(city, data, concat_name=False):
    try:
        data = data()
    except Exception as e:
        print("Scraper error", e)
        time.sleep(5)
        data = data()

    voter_stat = ""
    footer = ""

    if data.get("total_votes", 0) and data.get("percentage", 0):
        voter_stat = f"- **Vote counted**: {data['percentage']}% ({data['vote_counted']:,} of {data['total_votes']:,})"
    elif data.get("vote_counted", 0) <= 1:
        voter_stat += f"- **Vote counting not started yet.**"

    metadata = f"# {city}\n{voter_stat}\n\n"

    # Utils functions
    get_name = lambda x: x["name"] if not concat_name else x["name"].split(" ")[0]
    party = lambda x: party_shortform(x["party"])
    vote_percent = lambda x: round((int(x["votes"]) / data["vote_counted"]) * 100, 1)

    # Mayor format
    header = "Candidate|Party|Votes|Percentage|\n:--:|:--:|:--:|:--:|\n"
    candidates = []
    for index, d in enumerate(data["candidates"]):
        vote_diff = ""
        if index == 0:
            try:
                second_candidate_votes = int(data["candidates"][2]["votes"])
                vote_diff = f"  (+ {(int(d['votes']) - second_candidate_votes):,}) "
            except Exception as e:
                print("Vote diff calc error", e, d["name"])
        candidates.append(
            f"{get_name(d)} | {party(d)} | {int(d['votes']):,}{vote_diff} | {vote_percent(d)}%"
        )

    candidate_info = metadata + header + "\n".join(candidates)
    candidate_text = f"{candidate_info}\n{footer}" if footer else candidate_info

    body = f"{candidate_text}\n\n"
    return body


if __name__ == "__main__":
    while True:
        main()
        time.sleep(30)
