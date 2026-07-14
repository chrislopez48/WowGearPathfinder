import os

import requests                                        
                                                            #lets python reach web APIs over HTTP
from dotenv import load_dotenv                          
                                                        #actually reads our env file and gets the values


load_dotenv()                                              #searches for env file

client_id = os.getenv("Blizzclient")                 #copying env files onto vars here
client_secret = os.getenv("Blizzsecret")

if not client_id or not client_secret:
    raise ValueError("Blizzard API credentials were not found in the .env file.")

token_url = "https://oauth.battle.net/token"

response = requests.post(
    token_url,
    auth=(client_id, client_secret),
    data={"grant_type": "client_credentials"},
    timeout=30,
)                                                           #http post request sending auth to blizz

response.raise_for_status()

token_data = response.json()

print("Authentication successful!")
print("Access token received:", bool(token_data.get("access_token")))
print("Token expires in:", token_data.get("expires_in"), "seconds")

access_token = token_data["access_token"]

item_id = 24044  # Hellreaver

item_url = f"https://us.api.blizzard.com/data/wow/item/{item_id}"

item_response = requests.get(
    item_url,
    headers={
        "Authorization": f"Bearer {access_token}"
    },
    params={
        "namespace": "static-classic-us",
        "locale": "en_US",
    },
    timeout=30,
)

item_response.raise_for_status()

item_data = item_response.json()

print("\nItem request successful!")
print("Item ID:", item_data.get("id"))
print("Item name:", item_data.get("name"))
print("Required level:", item_data.get("required_level"))
print("Item level:", item_data.get("level"))