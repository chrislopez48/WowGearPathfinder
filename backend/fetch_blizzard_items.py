import os
import json

import requests                                        
                                                            #lets python reach web APIs over HTTP
from dotenv import load_dotenv                          
                                                        #actually reads our env file and gets the values
from datetime import datetime, timezone
from pathlib import Path

load_dotenv()                                              #searches for env file

def get_access_token():
    client_id = os.getenv("Blizzclient")
    client_secret = os.getenv("Blizzsecret")

    if not client_id or not client_secret:
        raise ValueError("Blizzard API credentials were not found in the .env file.")

    token_url = "https://oauth.battle.net/token"

    response = requests.post(token_url, auth = (client_id, client_secret),
        data={"grant_type": "client_credentials"}, timeout = 30,)

    response.raise_for_status()

    token_data = response.json()

    print("Authentication successful")
    print("Access token received:", bool(token_data.get("access_token")))
    print("Token expires in:", token_data.get("expires_in"), "seconds")

    return token_data["access_token"]

def load_item_ids():                        #calls json with item ids instead of hard code
    item_ids_file = Path(__file__).parent / "item_ids.json"
    try:
        with open(item_ids_file, "r") as item_file:
            raw_item_ids = json.load(item_file)

    except FileNotFoundError:
            print(f"Item ID file was not found: {item_ids_file}")
            return []

    except json.JSONDecodeError as error:
            print(f"Item ID file contains invalid JSON: {error}")
            return []
    
    valid_item_ids = []

    for item_id in raw_item_ids:
        if isinstance(item_id, int) and item_id > 0:
            if item_id not in valid_item_ids:
                valid_item_ids.append(item_id)

    return valid_item_ids

def extract_stats(preview_item):
                                                    #clean up blizz api to dictionary form
    stats = {}

    
    for stat in preview_item.get("stats", []):
        stat_type = stat.get("type", {}).get("type")
        stat_value = stat.get("value")

        if stat_type and stat_value is not None:
           
            stat_name = stat_type.lower()
            stats[stat_name] = stat_value

    return stats

def extract_weapon_data(preview_item):
    # Blizzard only includes this section for weapons.
    weapon = preview_item.get("weapon", {})

    if not weapon:
        return None

    damage = weapon.get("damage", {})
    attack_speed = weapon.get("attack_speed", {})
    dps = weapon.get("dps", {})

    return {
        "minimum_damage": damage.get("min_value"),
        "maximum_damage": damage.get("max_value"),
        "damage_type": damage.get("damage_class", {}).get("name"),
        "attack_speed": 
        (attack_speed.get("value") / 1000 
        if attack_speed.get("value") is not None
        else None), 
        "dps": dps.get("value"),
    }

def extract_armor_data(preview_item):
    armor = preview_item.get("armor", {})

    if not armor:
        return None

    return {
        "value": armor.get("value"),
        "display": armor.get("display", {}).get("display_string"),
    }

def extract_requirements(preview_item):
    requirements = preview_item.get("requirements", {})
    level_requirement = requirements.get("level", {})

    return {
        "required_level": level_requirement.get("value"),
        "display": level_requirement.get("display_string"),
    }

def extract_spells(preview_item):
    spells = []

    for spell_entry in preview_item.get("spells", []):
        spell = spell_entry.get("spell", {})

        spells.append({
            "id": spell.get("id"),
            "name": spell.get("name"),
            "description": spell_entry.get("description"),
        })

    return spells


def extract_item_details(preview_item):
    binding = preview_item.get("binding", {})
    durability = preview_item.get("durability", {})

    return {
        "binding": binding.get("name"),
        "unique": preview_item.get("unique_equipped"),
        "durability": durability.get("value"),
    }

def fetch_item(item_id, access_token):
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

    preview_item = item_data.get("preview_item", {})

    stats = extract_stats(preview_item)
    weapon_data = extract_weapon_data(preview_item)

    armor_data = extract_armor_data(preview_item)

    requirements = extract_requirements(preview_item)
    spells = extract_spells(preview_item)
    item_details = extract_item_details(preview_item)
    

    print("\nAvailable Blizzard fields:")
    print(item_data.keys())

    raw_output_file = Path(__file__).parent / f"raw_item_{item_id}.json"

    with open(raw_output_file, "w") as raw_file:
        json.dump(item_data, raw_file, indent=4)

    return {
    "id": item_data.get("id"),
    "name": item_data.get("name"),
    "slot": item_data.get("inventory_type", {}).get("name"),
    "item_type": item_data.get("item_subclass", {}).get("name"),
    "item_class": item_data.get("item_class", {}).get("name"),
    "required_level": requirements.get("required_level"),
    "item_level": item_data.get("level"),
    "quality": item_data.get("quality", {}).get("name"),
    "binding": item_details.get("binding"),
    "unique": item_details.get("unique"),
    "durability": item_details.get("durability"),
    "is_equippable": item_data.get("is_equippable"),
    "stats": stats,
    "weapon": weapon_data,
    "armor": armor_data,
    "spells": spells,
    }

    
def save_items(items):
    output_file = Path(__file__).parent / "blizzard_items.json"

    with open(output_file, "w") as item_file:
        json.dump(items, item_file, indent = 4)

    return output_file

def save_failed_item_ids(failed_item_ids):
    failed_items_file = Path(__file__).parent / "failed_item_ids.json"

    with open(failed_items_file, "w") as failed_file:
        json.dump(failed_item_ids, failed_file, indent = 4)

    return failed_items_file



def main():
    # Authenticate with Blizzard and receive an access token.
    access_token = get_access_token()
    item_ids = load_item_ids()              #replaces hard coding with json call

    if not item_ids:
        print("No valid item IDs were found. Nothing to fetch.")
        return

    items = []
    failed_item_ids = []


    for item_id in item_ids:
        try:
            trimmed_item = fetch_item(item_id, access_token)
            items.append(trimmed_item)

            print("Fetched item:", trimmed_item.get("name"))

        except requests.RequestException as error:
            failed_item_ids.append(item_id)
            print(f"Failed to fetch item {item_id}: {error}")

    output_file = save_items(items)
    failed_items_file = save_failed_item_ids(failed_item_ids)
    
    print("\nFetch summary")
    print("Items requested:", len(item_ids))
    print("Items fetched:", len(items))
    print("Items failed:", len(failed_item_ids))
    print("Items saved to:", output_file)
    print("Failed item IDs saved to:", failed_items_file)    


if __name__ == "__main__":
    main()