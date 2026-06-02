#docker build -t wow-gear-api .         build the image(packaged app)
#docker run -p 8000:8000 wow-gear-api   starts a container(the runnning app)
#docker start/stop wow-api-container
from fastapi import FastAPI
from pydantic import BaseModel

import csv

app = FastAPI(title="WoW TBC Gear Path Finder")


class GearItem(BaseModel):                  #pydantic model; strict typing
    id: int
    name: str
    slot: str
    item_type: str
    required_level: int
    source_type: str
    source_name: str
    zone: str
    classes: list[str]
    stats: dict[str, int]

STAT_WEIGHTS = {
    "Warrior": {
        "strength": 1.5,
        "stamina": 1.0,
        "crit": 1.2,
        "agility": 0.8,
        "intellect": 0.1,
        "spell_power": 0.0,
    },
    "Paladin": {
        "strength": 1.3,
        "stamina": 1.0,
        "crit": 1.1,
        "intellect": 0.7,
        "spell_power": 0.8,
        "agility": 0.3,
    },
    "Hunter": {
        "agility": 1.5,
        "stamina": 1.0,
        "crit": 1.2,
        "strength": 0.4,
        "intellect": 0.6,
    },
    "Mage": {
        "intellect": 1.5,
        "stamina": 0.8,
        "spell_power": 1.6,
        "crit": 1.1,
        "strength": 0.0,
        "agility": 0.0,
    },
}

def calculate_item_score(item: dict, character_class: str) -> float:
    stats = item.get("stats", {})

    class_name = character_class.title()
    weights = STAT_WEIGHTS.get(class_name, {})

    item_score = 0

    for stat_name, stat_value in stats.items():
        stat_weight = weights.get(stat_name, 1.0)
        item_score += stat_value * stat_weight

    return round(item_score, 2)

def load_gear_items():
    items = []

    with open("data/gear_items.csv", mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            item = {
                "id": int(row["id"]),                                           #1 from csv is not an int, convert it to int here
                "name": row["name"],
                "slot": row["slot"],
                "item_type": row["item_type"],
                "required_level": int(row["required_level"]),
                "source_type": row["source_type"],
                "source_name": row["source_name"],
                "zone": row["zone"],
                "classes": row["classes"].split("|"),
                "stats": {
                    "strength": int(row["strength"]),
                    "stamina": int(row["stamina"]),
                    "crit": int(row["crit"])
                }
            }
            items.append(item)
    return items

gear_items = load_gear_items()                                                      #when api startss, load gear from csv

SPEC_STAT_WEIGHTS = {
    "Paladin": {
        "Ret": {
            "strength": 2,
            "stamina": 1,
            "crit": 2,
            "hit": 2,
            "intellect": 0.25,
        },
        "Holy": {
            "intellect": 2,
            "stamina": 1,
            "healing_power": 3,
            "spell_crit": 1.5,
            "mp5": 2,
            "spirit": 0.5,
        },
        "Prot": {
            "stamina": 2,
            "defense": 3,
            "strength": 1.5,
            "block_value": 2,
            "dodge": 2,
            "parry": 2,
        },
    },
    "Mage": {
        "Fire": {
            "intellect": 2,
            "stamina": 1,
            "spell_power": 3,
            "spell_crit": 2,
            "spell_hit": 2,
            "spirit": 0.5,
        },
        "Frost": {
            "intellect": 2,
            "stamina": 1,
            "spell_power": 3,
            "spell_crit": 1.5,
            "spell_hit": 2,
            "spirit": 0.5,
        },
    },
    "Priest": {
        "Holy": {
            "intellect": 2,
            "spirit": 2,
            "stamina": 1,
            "healing_power": 3,
            "mp5": 2,
        },
        "Shadow": {
            "intellect": 2,
            "stamina": 1,
            "spirit": 1,
            "spell_power": 3,
            "spell_hit": 2,
            "spell_crit": 1.5,
        },
    },
    "Warrior": {
        "Arms": {
            "strength": 2,
            "stamina": 1.25,
            "crit": 2,
            "hit": 2,
        },
        "Prot": {
            "stamina": 2,
            "defense": 3,
            "strength": 1.5,
            "block_value": 2,
            "dodge": 2,
            "parry": 2,
        },
    },
}

@app.get("/health")
def health():
    return {"status": "ok"}                        #http://127.0.0.1:8000/health


@app.get("/items")
def get_items():
    return {
        "count": len(gear_items),
        "items": gear_items
    }

    
@app.get("/search")
def search_items(
    character_class: str | None = None,
    slot: str | None = None,
    source_type: str | None = None,
    min_level: int | None = None,
    max_level: int | None = None
):
    results = []

    for item in gear_items:
        if character_class is not None:
            if character_class.title() not in item["classes"]:
                continue

        if slot is not None:
            if item["slot"].lower() != slot.lower():
                continue

        if source_type is not None:
            if item["source_type"].lower() != source_type.lower():
                continue

        if min_level is not None:
            if item["required_level"] < min_level:
                continue

        if max_level is not None:
            if item["required_level"] > max_level:
                continue

        results.append(item)

    return {
        "count": len(results),
        "items": results
    }
    matching_items = []

    for item in gear_items:
        # Start by assuming the item matches
        matches = True

        # If the user gave a class, check if the item works for that class
        if character_class is not None:
            if character_class.title() not in item["classes"]:
                matches = False

        # If the user gave a level, check if the item is usable at that level
        if level is not None:
            if item["required_level"] > level:
                matches = False

        # If the user gave a slot, check if the item belongs in that gear slot
        if slot is not None:
            if slot.lower() not in item["slot"].lower():
                matches = False

        # If the user gave a source, check where the item comes from
        if source is not None:
            if item["source"].lower() != source.lower():
                matches = False

        # Only add the item if it passed all filters
        if matches:
            matching_items.append(item)

    return {
        "count": len(matching_items),
        "items": matching_items
    }



@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in gear_items:
        if item["id"] == item_id:
            return item

    return {"error": "Item not found"}


def score_item(item: dict, character_class: str, spec: str) -> float:
    stats = item["stats"]

    class_name = character_class.title()
    spec_name = spec.title()

    class_specs = SPEC_STAT_WEIGHTS.get(class_name, {})
    stat_weights = class_specs.get(spec_name, {})

    score = 0

    for stat_name, stat_value in stats.items():
        weight = stat_weights.get(stat_name, 0)
        score += stat_value * weight

    return round(score, 2)

@app.get("/gear-path")
def get_gear_path(character_class: str, spec: str, level: int):
    matching_items = []

    for item in gear_items:
        class_matches = character_class.title() in item["classes"]
        level_matches = item["required_level"] <= level

        if class_matches and level_matches:
            item_with_score = {**item, "item_score": score_item(item, character_class, spec)}

            matching_items.append(item_with_score)

            matching_items.sort(key=lambda item: item["item_score"], reverse=True)     #people.sort(key=lambda: person["age"]) 

    return {
        "character_class": character_class.title(),
        "spec": spec,
        "level": level,
        "count": len(matching_items),
        "recommended_items": matching_items
    }

@app.get("/recommend-gear")
def recommend_gear(
    character_class: str,
    level: int,
    slot: str | None=None
):
    matching_items = []

    for item in gear_items:
        class_matches = character_class.title() in item["classes"]
        level_matches = item["required_level"] <= level

        if slot is not None:
            slot_matches = item["slot"].lower() == slot.lower()
        else:
            slot_matches = True

        if class_matches and level_matches and slot_matches:
            
            item_score = calculate_item_score(item, character_class)

            item_with_score = {
                **item,
                "item_score": item_score
            }

            matching_items.append(item_with_score)

    matching_items.sort(
        key=lambda item: item["item_score"],                                #sorts to find highest scoring gear first
        reverse=True
    )

    return {
        "character_class": character_class.title(),
        "level": level,
        "slot": slot,
        "count": len(matching_items),
        "recommended_items": matching_items
    }

@app.get("/best-per-slot")
def best_per_slot(character_class: str, level: int):
    best_items = {}

    for item in gear_items:
        class_matches = character_class.title() in item["classes"]
        level_matches = item["required_level"] <= level

        if class_matches and level_matches:
            item_score = calculate_item_score(item, character_class)
            slot = item["slot"]

            item_with_score = {
                **item,
                "item_score": item_score
            }

            if slot not in best_items:
                best_items[slot] = item_with_score
            else:
                current_best_score = best_items[slot]["item_score"]

                if item_score > current_best_score:
                    best_items[slot] = item_with_score

    return {
        "character_class": character_class.title(),
        "level": level,
        "count": len(best_items),
        "best_gear": best_items
    }
    


   