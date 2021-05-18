import os
import sys 
import csv
import re
import tweepy
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from datetime import datetime, timedelta
from dateutil.parser import parse
import discord
from dateutil import tz


load_dotenv()
auth = tweepy.OAuthHandler(os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET_KEY'))
auth.set_access_token(os.getenv('TWITTER_ACCESS_TOKEN'), os.getenv('TWITTER_ACCESS_SECRET_TOKEN'))
api = tweepy.API(auth, wait_on_rate_limit=True)

keyword = "[ON]"

def deEmojify(text):
    emoj_pattern = re.compile(pattern="["
                                u"\U0001F600-\U0001F64F"  # emoticons
                                u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                "]+", flags=re.UNICODE)
    return emoj_pattern.sub(r'', text)

def get_twitterdata():
    data = api.user_timeline("VaxHuntersCan", count=200, tweet_mode="extended", exclude_replies=True, include_rts=False)

    with open('Covid_Data.csv', mode='a', encoding='utf-8', newline='') as csv_file:
        fieldnames=['created_at', 'text']
        writer = csv.DictWriter(csv_file, fieldnames)
        writer.writeheader()
        
        for tweetObject in data:
            writer.writerow({'text': deEmojify(tweetObject.full_text), 'created_at': tweetObject.created_at})

    print("Done updating the csv file")

    date = []
    text = []
    feed = []
    final = []

    with open('Covid_Data.csv', mode='r', encoding='utf-8', newline='', errors='ignore') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        for row in reader:
            if row[1].startswith(keyword):
                date.append(row[0])
                text.append(row[1])

    csv_file.close()
    
    now = datetime.now()
    last_minutes = datetime.now(tz.gettz('America/New York')) - timedelta(minutes=30)
    feed = np.c_[date, text]

    for x in range(len(date)-1):
        bruh= str(date[x])
        bruh = parse(bruh)
        if bruh < now and bruh > last_minutes:
            final.append(feed[x])

    return (np.unique(final))
