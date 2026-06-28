# WoW Gear Pathfinder

WoW Gear Pathfinder is a FastAPI backend project that recommends gear upgrades for World of Warcraft: The Burning Crusade characters based on class, specialization, level, item stats, and item source.

The goal of this project is to build a useful backend API while practicing real-world development skills like API design, CSV data handling, GitHub version control, Docker, and eventually AWS deployment.

## Project Goal

The app helps a player find gear upgrades based on their current character level.

For example, a level 60 Retribution Paladin can request gear options and filter them by source type, such as quest rewards, dungeon drops, or crafted items.

Example request:

```text
/gear-path?character_class=paladin&spec=ret&level=60
```

The API returns matching gear grouped by equipment slot and sorted by item score.

## Tech Stack

* Python
* FastAPI
* Uvicorn
* CSV data storage
* Docker
* GitHub

Planned future tools:

* AWS
* API Gateway or EC2
* CI/CD pipeline
* Cloud monitoring/logging

## Current Features

* Health check endpoint
* View all gear items
* View one gear item by ID
* Recommend gear by class, spec, and level
* Filter gear by equipment slot
* Filter gear by source type
* Score items based on useful stats
* Group top gear options by slot
* Show item source information such as quest, dungeon, crafting, zone, and source name

## API Endpoints

### Health Check

```http
GET /health
```

Returns a simple status response to confirm the API is running.

Example response:

```json
{
  "status": "ok"
}
```

### Get All Items

```http
GET /items
```

Returns all gear items loaded from the CSV file.

### Get Item by ID

```http
GET /items/{item_id}
```

Returns one specific item by its ID.

Example:

```http
GET /items/1
```

### Get Gear Path

```http
GET /gear-path
```

Main endpoint for gear recommendations.

Required query parameters:

```text
character_class
spec
level
```

Optional query parameters:

```text
slot
source_type
top_n_per_slot
```

Example:

```http
GET /gear-path?character_class=paladin&spec=ret&level=60
```

Quest-only example:

```http
GET /gear-path?character_class=paladin&spec=ret&level=60&source_type=Quest
```

Slot-specific example:

```http
GET /gear-path?character_class=paladin&spec=ret&level=60&slot=Waist
```

## Example Response Structure

```json
{
  "character": {
    "class": "Paladin",
    "spec": "Ret",
    "level": 60
  },
  "filters": {
    "slot": null,
    "source_type": null,
    "top_n_per_slot": 3
  },
  "summary": {
    "source_type_counts": {
      "Dungeon": 3,
      "Quest": 7,
      "Crafting": 2
    }
  },
  "total_matching_items": 12,
  "slots_returned": 10,
  "gear_by_slot": {
    "Two-Hand": [
      {
        "id": 1,
        "name": "Hellreaver",
        "slot": "Two-Hand",
        "item_type": "Polearm",
        "required_level": 60,
        "source_type": "Dungeon",
        "source_name": "Hellfire Ramparts",
        "zone": "Hellfire Peninsula",
        "classes": ["Warrior", "Paladin", "Hunter"],
        "stats": {
          "strength": 23,
          "stamina": 33,
          "crit": 21
        },
        "item_score": 121
      }
    ]
  }
}
```

## Project Structure

```text
WowGearPathfinder/
  backend/
    app.py
    requirements.txt
    Dockerfile
    data/
      gear_items.csv
  README.md
  .gitignore
```

## Running Locally

From the backend folder:

```bash
uvicorn app:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

The `/docs` page opens the FastAPI Swagger UI, where the API endpoints can be tested in the browser.

## Running with Docker

Build the Docker image:

```bash
docker build -t wow-gear-api .
```

Run the container:

```bash
docker run -p 8000:8000 wow-gear-api
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Roadmap

### Phase 1: Local Backend

* Build FastAPI app
* Load gear data from CSV
* Create gear recommendation endpoint
* Add class/spec/level filtering
* Add slot and source type filters

### Phase 2: Better Gear Data

* Add more Burning Crusade quest rewards
* Add better level-based gear progression
* Add more class/spec stat weights
* Focus on realistic upgrades for the player's current level

### Phase 3: Docker

* Containerize the backend
* Run the API locally through Docker
* Prepare the project for deployment

### Phase 4: AWS Deployment

* Deploy the backend to AWS
* Explore EC2, ECS, Lambda, or API Gateway options
* Add cloud-based logging and monitoring

### Phase 5: Portfolio Improvements

* Add screenshots of API tests
* Add architecture diagram
* Add deployment notes
* Add GitHub project board or issue list

## Purpose

This project is being built as a portfolio project to practice backend API development, Docker, GitHub, and AWS deployment while using a topic that is interesting and practical for World of Warcraft players.
