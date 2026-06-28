#code --disable-extensions .
#docker build -t wow-gear-api .         build the image(packaged app)
#docker run -p 8000:8000 wow-gear-api   starts a container(the runnning app)
#docker start/stop wow-api-container
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path

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
@app.get("/gear-path")                                                          #when user types into url, this is where it goes
def get_gear_path(character_class: str, spec: str, level: int, slot: str | None = None, source_type: str | None = None, top_n_per_slot: int = 3):
    return build_gear_path(
        character_class=character_class,
        spec=spec,
        level=level,
        slot=slot,
        source_type=source_type,
        top_n=top_n_per_slot                                                                        #how many items user wants in search 
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