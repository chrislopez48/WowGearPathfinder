import os
import json

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

response.raise_for_status()                                 #show error if request fails

token_data = response.json()                                #json turns into python dictionary

print("Authentication successful!")
print("Access token received:", bool(token_data.get("access_token")))
print("Token expires in:", token_data.get("expires_in"), "seconds")

access_token = token_data["access_token"]

#item_id = 24044  # Hellreaver

item_ids = [
    24044,  # Hellreaver
    19019,  # Thunderfury
]

def fetch_item(item_id, access_token):
    # Build the Blizzard API URL for the selected item.
    item_url = f"https://us.api.blizzard.com/data/wow/item/{item_id}"

    # Request the item's data from Blizzard.
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

    return {
        "id": item_data.get("id"),
        "name": item_data.get("name"),
        "slot": item_data.get("inventory_type", {}).get("name"),
        "item_type": item_data.get("item_subclass", {}).get("name"),
        "required_level": item_data.get("required_level"),
        "item_level": item_data.get("level"),
    }

items = []

for item_id in item_ids:
    try:
        trimmed_item = fetch_item(item_id, access_token)
        items.append(trimmed_item)
        print("Fetched item:", trimmed_item.get("name"))
    
    except requests.RequestException as error:
        print(f"Failed to fetch item {item_id}: {error}")

with open("backend/blizzard_items.json", "w") as item_file:
    json.dump(items, item_file, indent=4)


print("\nItems saved:", len(items))
print("Items saved to backend/blizzard_items.json")