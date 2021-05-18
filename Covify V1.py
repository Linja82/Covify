from datetime import *
from dateutil import tz
from dateutil.parser import parse
from dateutil.tz import gettz
from discord.ext import commands, tasks
from dotenv import load_dotenv              # pip install python-dotenv
import asyncio
import discord                              # pip install discord.py
import json
import os                                   # Should already be installed
import re
import requests
import tweepy                               # pip install tweepy
from Twitter_API import get_twitterdata
from Hospital_Finder_V1 import Area_Code_to_Coordinates

########### ISSUES ###################
# Profile data change does not work correctly. Over writes incorrect data

########## FEATURES TO ADD ############
# Logging - "User, command, date, time", "All bot actions, date, time"


prefix='.'
bot = commands.Bot(prefix)
load_dotenv()
FILE = "User_Info.text"
bot.remove_command('help')  

auth = tweepy.OAuthHandler(os.getenv('TWITTER_API_KEY'), os.getenv('TWITTER_API_SECRET_KEY'))
auth.set_access_token(os.getenv('TWITTER_ACCESS_TOKEN'), os.getenv('TWITTER_ACCESS_SECRET_TOKEN'))
api = tweepy.API(auth, wait_on_rate_limit=True)

@bot.event
async def on_ready(): # Startup task
    print(bot.user.name)
    print(bot.user.id)
    print("Ready\n")

def date_time_convertor(incoming): # Change time zone for the footer of the latest command
    from_zone = gettz('UTC+1') # Norway
    to_zone = gettz('America/New York')

    incoming = str(incoming)
    date = incoming.split("T")[0][1:]
    time = incoming.split("T")[1][0:8]
    new_date = parse(date)
    new_time = parse(time).time()

    combined = datetime.combine(new_date, new_time)

    combined = combined.replace(tzinfo=from_zone)
    toronto_combined = combined.astimezone(to_zone)
    toronto_combined = toronto_combined.strftime("%Y-%m-%d, %H:%M:%S")
    return toronto_combined


def replace_line(FILE, line_num, new_text):
    old_lines = open(FILE, 'r').readlines()
    print(old_lines)
    old_lines[line_num] = new_text
    new_lines = open(FILE, 'w')
    new_lines.writelines(old_lines)
    new_lines.close()
    

def find_user_profile(user):
    global FILE
    file = open(FILE, 'r')
    num_users = len(file.readlines())
    file.seek(0)    # Reset seek position to the beginning
    print("number of users: " + str(num_users))
    for x in range(num_users):
        line = file.readline()
        # print("Line = " + line)
        line = line.split(',')
        print("Row " + str(x) + " = " + str(line[0]))
        if user == line[0]:     # User has an existing profile
             user_profile_exists = True
             file.close()
             return line


def profile_checker(user):  # Checks if a user has a profile                               
    # grab users username
    # compare username with all stored values
    # If user has a profile, continue on
    # If user does not have a profile, send them to profile creator
    user_profile_exists = False

    global FILE
    file = open(FILE, 'r')
    num_users = len(file.readlines())
    file.seek(0)
    print("number of users: " + str(num_users))
    for x in range(num_users):
        line = file.readline()
        print("Line = " + line)
        line = line.split(',')
        print("Row " + str(x) + " = " + str(line[0]))
        if user == line[0]:     # User has an existing profile
             user_profile_exists = True
             file.close()
             return user_profile_exists
    
    file.close()
    return user_profile_exists
    

@bot.command(name='ping')   # Check bot latency
async def ping(ctx): 
   await ctx.send(f'Pong! 🏓 `{round(bot.latency * 1000)}ms`')


@bot.command(name='help')
async def help(ctx):
    embed = discord.Embed(title="Covify Commands", colour=0xe67e22)
    embed.add_field(name="Command", value="**`.cb`**\n\n**`.ping`**\n**`.symptoms`**\n**`.latest`**\n**`.location [province]`**", inline = True)
    embed.add_field(name="Description", value="- Create a profile of your location/age for better health recommendations\n- Get the current server latency\n\
                    - Provides a list of Covid symptoms and recommendations\n- Displays world wide data\n- Displays data for searched province", inline = True)
    embed.set_footer(text=f"Stay Safe 😷")
    await ctx.send(embed=embed)


@bot.command(name='cp') # Create a user profile
async def profile_creator(ctx):
#    # ask a user for their location and age
#    # Store it in the data file
    global FILE

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    if profile_checker(str(ctx.message.author)): # Profile already exists
        await ctx.send("You already have a profile. Do you wish to change your information? [y, n]")
        msg = await bot.wait_for('message', check=check)
        msg = msg.clean_content.lower()
        if msg == 'y':
            await ctx.send(f"What are the first 3 characters of your postal code?")
            msg = await bot.wait_for('message', check=check)
            location = msg.clean_content.lower()  
            location = location[:3]

            await ctx.send(f"How old are you?")
            msg = await bot.wait_for('message', check=check)
            age = msg.clean_content.lower()

            new_text = str(ctx.message.author) + ',' + str(location) + ',' + str(age) + "\n"
            
            file = open(FILE, 'r')
            num_users = len(file.readlines())

            for x in range(num_users):
                line = file.readline()
                line = line.split(',')
                if str(ctx.author) == line[0]:    
                    location = x
                    break
            replace_line(FILE, x, new_text)
            file.close()
    else:
        await ctx.send(f"Hey there {ctx.message.author.mention} it seems that you're a new user. Please answer the follow 2 questions so that I can better help you!)")
    
        file = open(FILE, 'a')

        await ctx.send(f"What are the first 3 characters of your postal code?")
        msg = await bot.wait_for('message', check=check)
        location = msg.clean_content.lower()  
        location = location[:3]

        await ctx.send(f"How old are you?")
        msg = await bot.wait_for('message', check=check)
        age = msg.clean_content.lower()
    
        file.write(str(ctx.message.author) + ',' + str(location) + ',' + str(age) + "\n")
        file.close()


def worldwide_data(data):   # Fetch latest world wide data and embed
    totalCases = data['latest']['confirmed']
    totalDeaths = data['latest']['deaths']
    recovered = data['latest']['recovered']
    date = [{x['last_updated']} for x in data['locations']]
        
    embed=discord.Embed(title="Worldwide Covid Statistics:", colour=0x2ecc71)
    embed.add_field(name="Total Cases", value=totalCases, inline=True)
    embed.add_field(name="Total Deaths", value=totalDeaths, inline=True)
    embed.add_field(name="Total Recovered", value=recovered, inline=True)
    current = date_time_convertor(date[0])
    embed.set_footer(text=f"last updated: " + str(current))
    
    return embed


@bot.command(name='latest') # sends total cases, deaths and recovered of the world
async def latest(ctx): 
    url_US = 'https://covid-tracker-us.herokuapp.com/#v2/locations'
    url_NOR = 'https://coronavirus-tracker-api.herokuapp.com/v2/locations'
    try:
        data = requests.get(url_NOR).json()
        embed = worldwide_data(data)
        await ctx.send(embed=embed)
    except:
        try: 
            data = requests.get(url_US).json()
            embed = worldwide_data(data)
            await ctx.send(embed=embed)
        except:
            embedErr=discord.Embed(description="External Covid API is currently unavailable! Please try again later.", colour=0xe74c3c)
            embedErr.set_author(name="Error!")
            await ctx.send(embed=embedErr)


@bot.command(name='location') # sends total cases, deaths of provinces of Canada
async def location(ctx, *, province = None):
    try:
        if location is None:
            embedErr1 = discord.Embed(title="You did not specify a province! Please try again.", colour=0xe74c3c)
            embedErr1.set_author(name="Error!")
            await ctx.send(embed=embedErr1)
        else:
            url = f'https://coronavirus-tracker-api.herokuapp.com/v2/locations?province={province}&timelines=false'
            data = requests.get(url).json()
            cases = data['latest']['confirmed']
            deaths = data['latest']['deaths']
            date = [{x['last_updated']} for x in data['locations']]
            
            province = province[0].upper() + province[1:]
            embed3=discord.Embed(title=f"{province} Covid Statistics:", colour=0x2ecc71)
            embed3.add_field(name="Total Cases", value=cases, inline=True)
            embed3.add_field(name="Total Deaths", value=deaths, inline=True)
            current = date_time_convertor(date[0])
            embed3.set_footer(text=f"last updated: " + str(current))
            await ctx.send(embed=embed3)
    except:
        embedErr2 = discord.Embed(title="Invalid Country Name Or API Error! Please try again.", colour=0xe74c3c)
        embedErr2.set_author(name="Error!")
        await ctx.send(embed=embedErr2)


@bot.command(name='updates')    # checks twitter for updates on hotspots, Ontario Covid19 updates etc.
async def update(ctx):
    updates = get_twitterdata()
    string = ' '.join(map(str,updates))
    await ctx.send(string)     
    

@bot.command(name='symptoms')
async def symptoms(ctx):
    if not (profile_checker(str(ctx.message.author))):
        await ctx.send(f"Oh no :weary:! It seems that you are a new user! Please use the **`.cp`** command to create a profile so that I can better help you.")
    else:
        embed=discord.Embed(title="Covid Symptoms:", colour=0x2ecc71)
        embed.add_field(name="Common Symptoms:", value="- Fever\n- Dry cough\n - Tiredness", inline=True)
        embed.add_field(name="Less Common Symptoms:", value="- Aches & pains\n- Sore throat\n- Diarrhoea\n- Conjunctivitis\n- Headache\n- loss of taste/smell\n- Rash on skin\n- Discolouration of fingers/toes", inline=True)
        embed.add_field(name="Severe Symptoms:", value="- Difficulty breathing /shortness of breath\n- Chest pain/pressure\n - Loss of speech/movement", inline=True)
        embed.set_footer(text=f"Stay Safe 😷")
        await ctx.send(embed=embed)
    
        await ctx.send(f"Are you experiencing any severe symptoms? [y, n]")
        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in ["y", "n"]

        msg = await bot.wait_for("message", check=check)
        if msg.content.lower() == "y":
            await ctx.send(f"You said yes, seek immediate medical attention! Make sure you call before visiting a doctor or health facility.")

            user_prof = find_user_profile(str(ctx.message.author))
            area_code = str(user_prof[1])
            print(area_code)
            Three_Closest_Hospitals = Area_Code_to_Coordinates(area_code)
            name1 = Three_Closest_Hospitals[0].split(' ')[1].replace('_', ' ')
            name2 = Three_Closest_Hospitals[1].split(' ')[1].replace('_', ' ')
            name3 = Three_Closest_Hospitals[2].split(' ')[1].replace('_', ' ')
            distance1 = round(float(Three_Closest_Hospitals[0].split(' ')[0]), 2)
            distance2 = round(float(Three_Closest_Hospitals[1].split(' ')[0]), 2)
            distance3 = round(float(Three_Closest_Hospitals[2].split(' ')[0]), 2)
            embed=discord.Embed(title="Nearby Hospitals:", colour=0x2ecc71)
            embed.add_field(name="Hospital:", value =str(name1) + '\n' + str(name2) + '\n' + str(name3) , inline=True)
            embed.add_field(name="Distance:", value=str(distance1) + ' Km\n' + str(distance2) + ' Km\n' + str(distance3) + ' Km', inline=True)
            embed.set_footer(text=f"Stay Safe 😷")
            await ctx.send(embed=embed)

        else:
            await ctx.send(f"You said no, if you have mild symptoms stay at home and manage your symptoms there.")

bot.run(os.getenv('DISCORD_TOKEN'))