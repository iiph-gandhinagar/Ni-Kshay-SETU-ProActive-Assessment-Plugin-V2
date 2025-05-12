
from pymongo import MongoClient

import os
import logging

from pytz import timezone
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='warn.log',level=logging.WARNING)
logging.basicConfig(filename='info.log',level=logging.INFO)
logging.basicConfig(filename='error.log',level=logging.ERROR)
logging.getLogger().setLevel(logging.INFO)



def get_latest_registry_id():
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]
    kmap_collection = db[os.getenv("KMAP_COLLECTION")]

    active_document = kmap_collection.find_one({"is_active": True})

    if active_document:
        logging.info("Active document found: %s",active_document)
        registry_id = active_document['_id']  # Retrieve the registry ID
        print("Registry ID:", registry_id)
        logging.info("Registry ID: %s", registry_id)
        return registry_id  # Return the registry ID if found
    else:
        print("No active document found.")
        logging.info("No active document found.")
        return None
    
    

def store_assessment(user_id, assessments, assessments_collection):
    # Update the user's document with new assessments, adding them to an 'assessments' array
    result = assessments_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {
                "assessments": {
                    "$each": assessments
                }
            },
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)}  # Set creation date if new document
        },
        upsert=True  # Create a new document if none exists for the user
    )
    if result.matched_count:
        print("Existing document updated.")
        logging.info("Existing document updated.")
    elif result.upserted_id:
        print("New document created.")
        logging.info("New document created.")

def log_assessment_attempt(user_id,cadre_id,status,num_assessments, error_message=None):
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]

    error_log_collection = db[os.getenv("ATTEMPT_LOG_COLLECTION")]
    error_log_collection.insert_one({
        "user_id": user_id,
        "cadre_id": cadre_id,
        "status": status,  # 'success' or 'failure'
        "num_assessments": num_assessments,
        "error": error_message,
        "timestamp": datetime.now(timezone.utc)
    })
    print(f"Logged error for user {user_id}")
    logging.info("Logged error for user %s", user_id)


def get_all_user_preferences():
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]

    preferences_collection = db[os.getenv("USER_PREFERNCE_COLLECTION")]
    all_user_prefs = list(preferences_collection.find({}, {"user_id": 1, "weekly_assessment_count": 1, "cadre_id": 1,"lang":1,"_id": 0}))
    return all_user_prefs

