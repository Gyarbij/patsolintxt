import os
import discord
import openai
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_ENGINE_ID = os.getenv('GOOGLE_ENGINE_ID')
TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AZURE_ENDPOINT_URL = os.getenv('AZURE_ENDPOINT_URL')
OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION')

# Setup OpenAI
openai.api_key = OPENAI_API_KEY
openai.api_type = "azure"
openai.api_base = AZURE_ENDPOINT_URL
openai.api_version = OPENAI_API_VERSION

# Setup logging
logging.basicConfig(level=logging.INFO)

# Create a custom search client
service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)

# Setup discord client
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def chat_with_openai(prompt, system_message, role="user"):
    response = openai.ChatCompletion.create(
        engine="gpt-4-32k",
        messages=[
            {"role": "system", "content": system_message},
            {"role": role, "content": prompt}
        ],
        temperature=0.95,
        max_tokens=1024,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return response['choices'][0]['message']['content']

def generate_summary(context, text):
    system_message = "You are a summarizer AI, your task is to condense and summarize the important points in text given to you, convert any imperial units to metric SI units. Windspeed should be indicated in m/s"
    summary = chat_with_openai(f"User asked: {context} As response we got a long text, please provide a brief summary:\n{text}", system_message)
    return summary

@client.event
async def on_ready():
    logging.info(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if client.user in message.mentions:
        logging.info(f"Query: {message.content}")
        try:
            if "!search" in message.content:
                logging.info(f"Search requested: {message.content}")
                # Extract the search query from the message
                query = message.content.split("!search")[1].strip()

                # Call the Google Custom Search API and retrieve the first result
                result = service.cse().list(
                    q=query,
                    cx=GOOGLE_ENGINE_ID,
                    num=1
                ).execute()

                # Extract the URL and title of the first search result
                if "items" in result:
                    url = result["items"][0]["link"]
                    resp = requests.get(url)
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    summary = generate_summary(query, soup.get_text())
                    logging.info(f"Bot: {summary}\n{url}")
                    await message.channel.send(summary)
                else:
                    await message.channel.send("Sorry, I couldn't find anything.")
            else:
                system_message = "You are a witty and creative AI assistant named Aino. You should always be brief and to the point but provide enough information."
                response = chat_with_openai(message.content, system_message)
                logging.info(f"Bot: {response}")
                await message.channel.send(response)

        except Exception as e:
Here's the continuation of the code:

```python
            logging.error(f"An error occurred: {str(e)}")
            await message.channel.send("An error occurred while processing your request.")

client.run(TOKEN)
