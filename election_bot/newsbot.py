import os

import praw
from dotenv import load_dotenv

from news import get_ktm_votes, get_lalitpur_votes, get_bharatpur_votes

USERNAME = "election-bot-2079"
load_dotenv()

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
    reddit = login(USERNAME)
    submission = reddit.comment('i8lotdy')
    city_data_map = dict(
        Kathmandu=get_ktm_votes(),
        Bharatpur=get_bharatpur_votes(),
        Lalitpur=get_lalitpur_votes(),
    ) 
    header = "source: https://election.ekantipur.com\n"
    footer = """\n\n\n\n^^contribute:  [Bot code](https://github.com/pykancha/reddit-bots) |  [Api code](https://github.com/pykancha/election-scraper) | [Api url for your personal automation](https://g7te1m.deta.dev/)"""
    footer = ""
    text = ''
    for city, data in city_data_map.items():
        text += gen_msg(city, data) if city!='Kathmandu' else gen_msg(city, data, concat_name=True)
    print(submission.author)
    submission.edit(body=f"{header}\n{text}\n{footer}")

    
def gen_msg(city, data, concat_name=False):
    mayor = f"# {city}\n## Mayor\n"
    get_name = lambda x: x['candidate-name'] if not concat_name else x['candidate-name'].split(' ')[0]
    candidates = [f"- {get_name(i)} {i['vote-numbers']}" for i in data['mayor']]
    mayor += "\n".join(candidates)
    deputy = "## Deputy Mayor\n"
    candidates = [f"- {i['candidate-name'].split(' ')[0]} {i['vote-numbers']}" for i in data['deputy']]
    deputy = deputy + "\n".join(candidates) if candidates else ""
    body = f'{mayor}\n{deputy}\n' if deputy else f'{mayor}\n'
    return body
   
if __name__ == "__main__":
    main()
