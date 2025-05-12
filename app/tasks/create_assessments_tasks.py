from pymongo import MongoClient

import os
import logging

from app.tasks.mongo_tasks import store_assessment
from app.tasks.fetch_questions_tasks import fetch_questions, integrate_user_interaction_questions

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='warn.log',level=logging.WARNING)
logging.basicConfig(filename='info.log',level=logging.INFO)
logging.basicConfig(filename='error.log',level=logging.ERROR)
logging.getLogger().setLevel(logging.INFO)

def fetch_related_questions_from_api(subscriberactivities_collection):
    print("enter the fetch function")
    logging.info("enter the fetch function")
    actions = ['Kbase Course Fetched', 'Chat Content Read']
    
    content_ids = []
    for action in actions:
        print(action)
        latest_entry = subscriberactivities_collection.find_one({"action": action},
                                                            sort=[("updated_at", -1)],
                                                            projection={"_id": 0, "payload": 1})
        if latest_entry:
            payload= latest_entry.get('payload').get('readContent')
            content_ids.extend([item['contentId'] for item in payload if 'contentId' in item])

    unique_content_ids = list(set(content_ids))

    return unique_content_ids

def create_assessments(user_id, lang,num_assessments, cadre_id):
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]

    questions_collection = db[os.getenv("QUESTIONS_COLLECTION")]
    assessments_collection = db[os.getenv("ASSESSMENTS_COLLECTION")]
    
    if num_assessments is None:
        num_assessments = 1
    subscriberactivities_collection = db[os.getenv("SUBSCRIBER_ACTIVITY_COLLECTION")]

    assessments = []  # To store the assessments

    # Fetch user activities to determine if special question handling is needed
    activities = list(subscriberactivities_collection.find(
        {'action': {'$in': ['Kbase Course Fetched', 'Chat Content Read']}}
    ))
    # print(activities)

    # # Determine if we need to fetch questions from an external API based on activities
    if activities:
        print("Fetching related questions from API")
        logging.info("Fetching related questions from API")
        # Assuming there's an API to fetch related questions based on user's recent interactions
        user_interaction_ids = fetch_related_questions_from_api(subscriberactivities_collection)

    
    # Fetch standard questions, initially not excluding any (this logic may need refinement)
    fetched_questions = fetch_questions(user_id,lang, num_assessments,assessments_collection,questions_collection,cadre_id)
    if isinstance(fetched_questions, dict) and 'error' in fetched_questions:
        print("Error fetching questions:", fetched_questions['error'])
        logging.info("Error fetching questions: %s",fetched_questions['error'])
        return fetched_questions
        

    if activities:
        print("Fetching related questions from API  2")
        logging.info("Fetching related questions from API 2")
        # Replace or append related questions from API into the fetched questions
        fetched_questions = integrate_user_interaction_questions(user_interaction_ids, fetched_questions, user_id,lang,assessments_collection)
        print("Fetched related questions from API",fetched_questions)
        logging.info("Fetched related questions from API: %s", fetched_questions)

    
   
    store_assessment(user_id, fetched_questions,assessments_collection)
    return fetched_questions

