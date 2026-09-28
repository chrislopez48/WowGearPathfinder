#code --disable-extensions .
#docker build -t wow-gear-api .         build the image(packaged app)
#docker run -p 8000:8000 wow-gear-api   starts a container(the runnning app)
#docker start/stop wow-api-container
#python3 backend/....
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from fastapi import Query

import json

import csv

DATA_DIR = Path(__file__).parent / "data"               #points to our backend/data
GEAR_ITEMS_FILE = DATA_DIR / "gear_items.csv"          

API_NAME = "Wow TBC Gear Path Finder"
API_VERSION = "0.2.0"

app = FastAPI(title = API_NAME, version = API_VERSION)


class GearItem(BaseModel):                  #pydantic model; strict typing, thingsMUST be certrain var types
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


STAT_COLUMNS = [
    "strength",
    "stamina",
    "crit",
    "agility",
    "intellect",
    "spirit",
    "spell_power",
    "spell_hit",
    "spell_crit",
    "healing_power",
    "mp5",
    "hit",
    "defense",
    "dodge",
    "parry",
    "block_value"
]


def load_item_stats(row: dict) -> dict[str, int]:
    stats = {}

    for stat_name in STAT_COLUMNS:
        stat_value = row.get(stat_name, "")                 #stat value = whatever stat name we pull

        if stat_value != "":
            stats[stat_name] = int(stat_value)               #'23' conveted to 23

    return stats

def load_gear_items():
    items = []
    seen_ids = set()

    with open(GEAR_ITEMS_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            item_id = int(row["id"])

            if item_id in seen_ids:
                continue

            seen_ids.add(item_id)
            
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
                "stats": load_item_stats(row)
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

def load_blizzard_items():
                            #convert json into python objects
    blizzard_items_file = Path(__file__).parent / "blizzard_items.json"

    try:
        with open(blizzard_items_file, "r") as item_file:
            items = json.load(item_file)

    except FileNotFoundError:
        print(f"Blizzard item file was not found: {blizzard_items_file}")
        return []

    except json.JSONDecodeError as error:
        print(f"Blizzard item file contains invalid JSON: {error}")
        return []

    if not isinstance(items, list):
        print("blizzard_items.json must contain a JSON list.")
        return []

    return items

def score_blizzard_item(item, character_class, spec):
    stats = item.get("stats", {})
    weapon = item.get("weapon") or {}

    if character_class.lower() == "paladin" and spec.lower() == "ret":
        weights = {
            "strength": 2.0,
            "stamina": 1.0,
            "crit_rating": 1.5,
            "agility": 0.5,
        }
        weapon_dps_weight = 1.0
    else:
        weights = {}
        weapon_dps_weight = 0

    item_score = 0

    for stat_name, stat_value in stats.items():
        stat_weight = weights.get(stat_name, 0)
        item_score += stat_value * stat_weight

    weapon_dps = weapon.get("dps") or 0             #if not a wep, will be 0 regarldess
    item_score += weapon_dps * weapon_dps_weight

    return round(item_score, 2)

def group_blizzard_items_by_slot(items, top_n_per_slot=3):
    grouped_items = {}

    for item in items:
        slot = item.get("slot", "Unknown")

        if slot not in grouped_items:
            grouped_items[slot] = []

        if len(grouped_items[slot]) < top_n_per_slot:
            grouped_items[slot].append(item)

    return grouped_items

CLASS_EQUIPMENT_RULES = {
    "paladin": {
        "armor": {
            "cloth",
            "leather",
            "mail",
            "plate",
            "shield",
        },
        "weapons": {
            "axe",
            "mace",
            "sword",
            "polearm",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
        },
    },

    "warrior": {
        "armor": {
            "cloth",
            "leather",
            "mail",
            "plate",
            "shield",
        },
        "weapons": {
            "axe",
            "mace",
            "sword",
            "polearm",
            "dagger",
            "fist weapon",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
        },
    },

    "druid": {
        "armor": {
            "cloth",
            "leather",
        },
        "weapons": {
            "mace",
            "dagger",
            "staff",
            "polearm",
            "fist weapon",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
        },
    },

    "hunter": {
        "armor": {
            "cloth",
            "leather",
            "mail",
        },
        "weapons": {
            "axe",
            "sword",
            "dagger",
            "staff",
            "polearm",
            "fist weapon",
            "bow",
            "crossbow",
            "gun",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
            "ranged",
        },
    },

    "mage": {
        "armor": {
            "cloth",
        },
        "weapons": {
            "sword",
            "dagger",
            "staff",
            "wand",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
            "ranged",
        },
    },

    "priest": {
        "armor": {
            "cloth",
        },
        "weapons": {
            "mace",
            "dagger",
            "staff",
            "wand",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
            "ranged",
        },
    },

    "rogue": {
        "armor": {
            "cloth",
            "leather",
        },
        "weapons": {
            "sword",
            "mace",
            "dagger",
            "fist weapon",
            "bow",
            "crossbow",
            "gun",
        },
        "weapon_slots": {
            "one-hand",
            "main hand",
            "off hand",
            "ranged",
        },
    },

    "shaman": {
        "armor": {
            "cloth",
            "leather",
            "mail",
            "shield",
        },
        "weapons": {
            "axe",
            "mace",
            "dagger",
            "staff",
            "fist weapon",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
        },
    },

    "warlock": {
        "armor": {
            "cloth",
        },
        "weapons": {
            "sword",
            "dagger",
            "staff",
            "wand",
        },
        "weapon_slots": {
            "one-hand",
            "two-hand",
            "main hand",
            "off hand",
            "ranged",
        },
    },
}

def can_equip(item, character_class):
    item_class = (item.get("item_class") or "").lower()
    item_type = (item.get("item_type") or "").lower()
    item_slot = (item.get("slot") or "").lower()
    character_class = character_class.lower()

    universal_slots = {
        "neck",
        "back",
        "finger",
        "trinket",
    }

    if item_slot in universal_slots:
        return True

    class_rules = CLASS_EQUIPMENT_RULES.get(character_class)

    if not class_rules:
        return False

    if item_class == "armor":
        return item_type in class_rules["armor"]

    if item_class == "weapon":
        return (
            item_type in class_rules["weapons"]
            and item_slot in class_rules["weapon_slots"]
        )

    return False

def explain_item_eligibility(item, character_class, spec):
    reasons = []

    if not item.get("is_equippable", False):
        reasons.append("Item is not equippable.")
        return {
            "allowed": False,
            "reasons": reasons,
        }

    if not can_equip(item, character_class):
        reasons.append("Class cannot equip this item.")
        return {
            "allowed": False,
            "reasons": reasons,
        }

    if not fits_spec(item, character_class, spec):
        reasons.append("Item does not fit this spec.")
        return {
            "allowed": False,
            "reasons": reasons,
        }

    reasons.append("Item passed all equipment checks.")

    return {
        "allowed": True,
        "reasons": reasons,
    }
SPEC_EQUIPMENT_RULES = {
    "paladin": {
        "ret": {
            "blocked_slots": {
                "off hand",
            },
            "required_weapon_slot": "two-hand",
        },

        "prot": {
            "blocked_weapon_slots": {
                "two-hand",
            },
        },

        "holy": {
            "blocked_weapon_slots": {
                "two-hand",
            },
        },
    },

    "warrior": {
        "arms": {
            "blocked_slots": {
                "off hand",
            },
            "required_weapon_slot": "two-hand",
        },

        "prot": {
            "blocked_weapon_slots": {
                "two-hand",
            },
        },
    },
    "mage": {
        "fire": {},
        "frost": {},
    },

    "priest": {
        "holy": {},
        "shadow": {},
    },
}

def fits_spec(item, character_class, spec):
    item_slot = (item.get("slot") or "").lower()
    item_class = (item.get("item_class") or "").lower()

    character_class = character_class.lower()
    spec = spec.lower()

    class_rules = SPEC_EQUIPMENT_RULES.get(character_class)
    
    if not class_rules:
        return True

    spec_rules = class_rules.get(spec)

    if not spec_rules:
        return True

    blocked_slots = spec_rules.get("blocked_slots", set())

    if item_slot in blocked_slots:
        return False

    blocked_weapon_slots = spec_rules.get("blocked_weapon_slots", set(),)

    if (
        item_class == "weapon"
        and item_slot in blocked_weapon_slots
    ):
        return False

    required_weapon_slot = spec_rules.get(
        "required_weapon_slot"
    )

    if (
        item_class == "weapon"
        and required_weapon_slot
        and item_slot != required_weapon_slot
    ):
        return False

    return True
    
    
def can_character_use_item(item, character_class, spec):
    if not can_equip(item, character_class):
        return False

    if not fits_spec(item, character_class, spec):
        return False

    return True

def build_blizzard_gear_path(
    character_class,
    spec,
    level,
    slot=None,
    top_n_per_slot=3,
):
    # Load the Blizzard items saved in blizzard_items.json.
    items = load_blizzard_items()

    scored_items = []

    for item in items:
        # Skip anything that cannot be equipped.
        if not item.get("is_equippable", False):
            continue

        if not can_character_use_item(item, character_class, spec):
            continue

        required_level = item.get("required_level") or 0
        item_slot = item.get("slot") or ""

        # Skip items above the character's level.
        if required_level > level:
            continue

        # Apply the optional slot filter.
        if slot and item_slot.lower() != slot.lower():
            continue

        # Copy the item so we do not modify the original data.
        scored_item = item.copy()

        scored_item["item_score"] = score_blizzard_item(
            item,
            character_class,
            spec,
        )

        scored_items.append(scored_item)

    # Rank the matching items from highest to lowest score.
    scored_items.sort(
        key=lambda item: item["item_score"],
        reverse=True,
    )

    best_item = scored_items[0] if scored_items else None

    gear_by_slot = group_blizzard_items_by_slot(
        scored_items,
        top_n_per_slot,
    )

    return {
        "character": {
            "class": character_class,
            "spec": spec,
            "level": level,
        },
        "filters": {
            "slot": slot,
            "top_n_per_slot": top_n_per_slot,
        },
        "summary": {
            "best_item_overall": best_item,
        },
        "total_matching_items": len(scored_items),
        "slots_returned": len(gear_by_slot),
        "gear_by_slot": gear_by_slot,
    }

@app.get("/blizzard-items")
def get_blizzard_items():
    items = load_blizzard_items()

    return {
        "count": len(items),
        "items": items,
    }

@app.get("/blizzard-item-values")
def get_blizzard_item_values():
    items = load_blizzard_items()

    item_classes = set()
    item_types = set()
    slots = set()

    for item in items:
        item_classes.add(item.get("item_class"))
        item_types.add(item.get("item_type"))
        slots.add(item.get("slot"))

    return {
        "item_classes": sorted(item_classes),
        "item_types": sorted(item_types),
        "slots": sorted(slots),
    }

@app.get("/blizzard-item-eligibility")
def get_blizzard_item_eligibility(
    character_class: str,
    spec: str,
):
    items = load_blizzard_items()
    results = []

    for item in items:
        eligibility = explain_item_eligibility(
            item,
            character_class,
            spec,
        )

        results.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "slot": item.get("slot"),
            "item_type": item.get("item_type"),
            "allowed": eligibility["allowed"],
            "reasons": eligibility["reasons"],
        })

    return {
        "character_class": character_class,
        "spec": spec,
        "count": len(results),
        "items": results,
    }

@app.get("/blizzard-items/scored")
def get_scored_blizzard_items(
    character_class: str,
    spec: str,
    level: int,
    slot: str | None = None,
    top_n_per_slot: int = 3,
):
    return build_blizzard_gear_path(
        character_class=character_class,
        spec=spec,
        level=level,
        slot=slot,
        top_n_per_slot=top_n_per_slot,
    )

@app.get("/")
def root():
    return {
        "message": "WoW TBC Gear Path Finder API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "gear_path": "/gear-path"
    }

@app.get("/version")
def version():
    return {
        "api_name": API_NAME,
        "api_version": API_VERSION
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_name": API_NAME,
        "api_version": API_VERSION,
        "gear_items_loaded": len(gear_items),
        "data_file": GEAR_ITEMS_FILE.name
    }                        #http://127.0.0.1:8000/health


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
    
@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in gear_items:
        if item["id"] == item_id:
            return item

    return {"error": "Item not found"}

@app.get("/filters")
def get_filters():
    
    return {
        "slots": get_available_slots(),
        "source_types": get_available_source_types(),
        "classes": get_available_classes(),
        "stats": get_available_stats(),
        "specs_by_class": get_available_specs_by_class()
    }

def score_item(item: dict, character_class: str, spec: str) -> float:               #5th stop. item actually gets scored here
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

def count_items_by_source_type(items: list[dict]) -> dict:
    source_counts = {}

    for item in items:
        source_type = item["source_type"]

        if source_type not in source_counts:
            source_counts[source_type] = 0

        source_counts[source_type] += 1

    return source_counts

                                                                        #third function we visit. just goes down check list of item and user url
def item_matches_filters(item: dict, character_class: str, level: int, slot: str | None=None, source_type: str | None=None):
    class_matches = character_class.title() in item["classes"]
    level_matches = item["required_level"] <= level
    slot_matches = slot is None or item["slot"].lower() ==slot.lower()
    source_matches = source_type is None or item["source_type"].lower() == source_type.lower()

    return class_matches and level_matches and slot_matches and source_matches      #returns just a singular item that passes all checks

def group_top_items_by_slot(items: list[dict], top_n: int):
    gear_by_slot = {}

    for item in items:
        item_slot = item["slot"]

        if item_slot not in gear_by_slot:
            gear_by_slot[item_slot] = []

        if len(gear_by_slot[item_slot]) < top_n:
            gear_by_slot[item_slot].append(item)

    return gear_by_slot

def sort_items_by_score(items: list[dict]) -> list[dict]:
    items.sort( key=lambda item: item["item_score"], reverse=True)

    return items

def add_item_score(item: dict, character_class: str, spec: str) -> dict:       
    return {
        **item,
        "item_score": score_item(item, character_class, spec)
    }
                                                                                #second funtion to start up

def build_slot_summary(gear_by_slot: dict) -> dict:
    slot_summary = {}

    for slot, items in gear_by_slot.items():
        best_item = items[0]

        slot_summary[slot] = {
            "items_found": len(items),
            "best_item": best_item["name"],
            "best_score": best_item["item_score"]
        }

    return slot_summary

def build_gear_path(character_class: str, spec: str, level: int, slot: str | None=None, source_type: str | None = None, top_n: int = 3):                     #values turn into paladin, ret, 60
    matching_items = []                                                        #fill empty list with csv

    for item in gear_items:
        if item_matches_filters(item, character_class, level, slot, source_type):
            item_with_score = add_item_score(item, character_class, spec)       #fourth stop. wnt from this func->filters func-> back here
            matching_items.append(item_with_score)
            
    matching_items = sort_items_by_score(matching_items)
    #matching_items.sort(key=lambda item: item["item_score"], reverse=True)     #people.sort(key=lambda: person["age"]) sort gear by score. reverse=true highest score comes first

    gear_by_slot = group_top_items_by_slot(matching_items, top_n)
    slot_summary = build_slot_summary(gear_by_slot)
    source_type_counts = count_items_by_source_type(matching_items)
    best_item_overall = matching_items[0] if matching_items else None


    return {
    "character": {"class": character_class.title(), "spec": spec.title(),"level": level},
    "filters": { "slot": slot,"source_type": source_type,"top_n_per_slot": top_n},
    "summary": {"source_type_counts": source_type_counts, "best_item_overall": best_item_overall, "slot_summary": slot_summary},
    "total_matching_items": len(matching_items),
    "slots_returned": len(gear_by_slot),
    "gear_by_slot": gear_by_slot
}


                                                                                #function below "starting point" of project
@app.get("/gear-path")
def get_gear_path(
    character_class: str,
    spec: str,
    level: int = Query(ge=1, le=70),
    slot: str | None = None,
    top_n_per_slot: int = Query(default=3, ge=1, le=10)
):
    return build_blizzard_gear_path(
        character_class=character_class,
        spec=spec,
        level=level,
        slot=slot,
        top_n_per_slot=top_n_per_slot,
    )

def get_available_slots():
    return sorted(set(item["slot"] for item in gear_items))


def get_available_source_types():
    return sorted(set(item["source_type"] for item in gear_items))


def get_available_classes():
    classes = set()

    for item in gear_items:
        for character_class in item["classes"]:
            classes.add(character_class)

    return sorted(classes)


def get_available_stats():
    stats = set()

    for item in gear_items:
        for stat_name in item["stats"]:
            stats.add(stat_name)

    return sorted(stats) 

def get_available_specs_by_class():
    specs_by_class = {}

    for class_name, class_specs in SPEC_STAT_WEIGHTS.items():
        specs_by_class[class_name] = sorted(class_specs.keys())

    return specs_by_class

@app.get("/specs")
def get_specs():
    specs_by_class = get_available_specs_by_class()

    return {
        "count": len(specs_by_class),
        "specs_by_class": specs_by_class
    }

@app.get("/slots")
def get_slots():
    slots = get_available_slots()
    #slots = sorted(set(item["slot"] for item in gear_items))                                #loops thru every item and grabs slot;use "set" to clean dupes
                                                                                            #hellreaver=two hander
    return {
        "count": len(slots),
        "slots": slots
    }   

@app.get("/source-types")                                                                       #same thing as function above, organize func liek dungeon/etc
def get_source_types():                                                                         #hellreaver=dungeon
    source_types = get_available_source_types()

    return {
        "count": len(source_types),
        "source_types": source_types
    }

@app.get("/classes")
def get_classes():
    classes = get_available_classes()

    return {
        "count": len(classes),
        "classes": sorted(classes)
    }

@app.get("/stats")
def get_stats():
    stats = get_available_stats()

    return {
        "count": len(stats),
        "stats": sorted(stats)
    }

#@app.get("/best-per-slot")
#def best_per_slot(character_class: str, level: int):
#    best_items = {}
#
 #   for item in gear_items:
  #      class_matches = character_class.title() in item["classes"]
   #     level_matches = item["required_level"] <= level
#
 #       if class_matches and level_matches:
  #          item_score = calculate_item_score(item, character_class)
   #         slot = item["slot"]
#
 #           item_with_score = {
  #              **item,
   #        }
#
 #           if slot not in best_items:
  #              best_items[slot] = item_with_score
   #         else:
    #            current_best_score = best_items[slot]["item_score"]
#
 #               if item_score > current_best_score:
  #                  best_items[slot] = item_with_score
#
 #   return {
  #      "character_class": character_class.title(),
   #     "level": level,
    #    "count": len(best_items),
     #   "best_gear": best_items
    #}
    

#class_matches = character_class.title() in item["classes"]                  #title makes first letter cap, rest lowercase. Paladin=paladin
        #level_matches = item["required_level"] <= level                             #these two lines create booleans/ stores true if class matches above
        #slot_matches = slot is None or item["slot"].lower() == slot.lower()
        #source_matches = source_type is None or item['source_type'].lower == source_type.lower()
        #/if class_matches and level_matches:
           # item_with_score = {**item, "item_score": score_item(item, character_class, spec)}    #**item copies whole hellreaver dictionary over
   
#for item in matching_items:
     #   item_slot = item["slot"]
#
 #       if item_slot not in gear_by_slot:
  #          gear_by_slot[item_slot] = []
#
 #       if len(gear_by_slot[item_slot]) < top_n:
  #          gear_by_slot[item_slot].append(item)

  #@app.get("/recommend-gear")
#def recommend_gear(
#    character_class: str,
#    level: int,
#    slot: str | None=None
#):