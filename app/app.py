from pymongo import MongoClient

from pytz import timezone
from datetime import datetime

import logging
import os

from flask import Flask, request, jsonify
from flask_cors import cross_origin, CORS

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.tasks.mongo_tasks import get_all_user_preferences, log_assessment_attempt
from app.tasks.create_assessments_tasks import create_assessments
from app.update import process_assessment_submission
from app.slack_alert import send_slack_notification


from dotenv import load_dotenv


app= Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

load_dotenv()


logging.basicConfig(filename='warn.log',level=logging.WARNING)
logging.basicConfig(filename='info.log',level=logging.INFO)
logging.basicConfig(filename='error.log',level=logging.ERROR)
logging.getLogger().setLevel(logging.INFO)


@app.route('/update_user_preferences', methods=['POST'])
@cross_origin()
def update_user_preferences():
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]
    environment = os.getenv('APP_ENV')
    data=request.get_json()
    user_id = data.get('user_id')
    lang = data.get('lang','en')
     
    num_assessments = data.get('assessment_count', 1)
    cadre_id=data.get('cadre_id')
    # num_assessments = min(num_assessments, 7)  
    if num_assessments > int(os.getenv('ASSESSMENT_COUNT')):
        return jsonify({"error": "Maximum assessment count is 7"}), 400
    
    preferences_collection = db[os.getenv("USER_PREFERNCE_COLLECTION")]
    result=preferences_collection.update_one(
        {"user_id": user_id},
  
  
        {"$set": {"cadre_id": cadre_id,"weekly_assessment_count": num_assessments,"lang":lang, "last_updated": datetime.now(timezone.utc)},
         "$setOnInsert": {
            "created_at": datetime.now(timezone.utc)
        }
         },
        upsert=True
    )
    if result.upserted_id is not None:
        print("New user preferences set, creating initial assessments.")
        logging.info("New user preferences set, creating initial assessments.")
        # Fetch user interaction ids or other relevant data needed to create assessments
        # Create assessments immediately for the new user
        assessments = create_assessments(user_id, lang, num_assessments, cadre_id)
        # print(assessments)
        
        if isinstance(assessments, dict) and 'error' in assessments:
            print("Error creating assessments:", assessments['error'])
            logging.info("Error creating assessments: %s ", assessments['error'])
            log_assessment_attempt(user_id,cadre_id,"failed",num_assessments, assessments['error'])
            error_msg  = (
                f"Application: Ni-kshay SETU v3-Pro-Active assessment\n"
                f"ENV: {environment}\n"
                f"file:app.py\n"
                f"Error: {assessments['error']}\n"
                f"Status: failed\n"

            )
            send_slack_notification(error_msg)
            # return jsonify(assessments), 400
        else:
            log_assessment_attempt(user_id,cadre_id,"successful",num_assessments)
        return {"user_id":user_id,"cadre_id":cadre_id,"assessments":assessments}
    return jsonify({"message": "User preferences updated successfully"}), 200

@app.route('/update_assessment_submission', methods=['POST'])
@cross_origin()
def update_assessement_submission():
    data= request.get_json()
    user_id = data.get('user_id')
    assessment_id = data.get('assessment_id')
    user_responses = data.get('user_responses')
    
    result = process_assessment_submission(user_id, assessment_id, user_responses)
    return result

def automate_weekly_assessments():
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]
    environment = os.getenv('APP_ENV') 
    assessments_collection = db[os.getenv("ASSESSMENTS_COLLECTION")]
    print("Running weekly assessments...")
    logging.info("Running weekly assessments...")
    user_prefs = get_all_user_preferences()
    
    for user_pref in user_prefs:
        user_id = user_pref['user_id']
        cadre_id = user_pref['cadre_id']
        num_assessments = user_pref.get('weekly_assessment_count', 1)  # Default to 1 if not specified
        # lang = "English"
        lang = user_pref.get('lang', 'en')
        # Aggregation pipeline to count pending assessments
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$unwind": "$assessments"},
            {"$match": {"assessments.pending": "yes"}},
            {"$count": "pending_assessments_count"}
        ]
        
        result = assessments_collection.aggregate(pipeline)
        pending_assessments_count = int(os.getenv('PENDING_ASSESSMENTS_COUNT'))
        for res in result:
            pending_assessments_count = res.get('pending_assessments_count', 0)
        
        print(f"User {user_id} has {pending_assessments_count} pending assessments.")
        logging.info("User %s has %s pending assessments.", user_id, pending_assessments_count)

        print("pending assessment----", pending_assessments_count)
        logging.info("Pending assessment---- %s", pending_assessments_count)
        if pending_assessments_count >= 14:
            print(f"Skipping user {user_id} - already has 14 or more pending assessments.")
            logging.info("Skipping user %s - already has 14 or more pending assessments.", user_id)
            continue  # Skip this user and move to the next one
   
        available_space = 14 - pending_assessments_count
        num_assessments_to_add = min(num_assessments, available_space)
        
        if num_assessments_to_add > 0:
            print(f"Creating {num_assessments_to_add} assessments for user {user_id} based on interactions and preferences.")
            logging.info("Creating %s assessments for user %s based on interactions and preferences.", num_assessments_to_add, user_id)
            assessments = create_assessments(user_id, lang, num_assessments_to_add, cadre_id)
            if isinstance(assessments, dict) and 'error' in assessments:
                log_assessment_attempt(user_id, cadre_id, "failed", num_assessments_to_add, assessments['error'])
                error_message = (
                    f"Application: Ni-kshay SETU v3-Pro-Active assessment\n"
                    f"ENV: {environment}\n"
                    f"file:app.py\n"
                    f"Error: {assessments['error']}\n"
                    f"Status: failed\n"

                )
                send_slack_notification(error_message)
                continue
            log_assessment_attempt(user_id, cadre_id, "successful", num_assessments_to_add)
        else:
            print(f"No assessments added for user {user_id} as they have reached the limit.")
            logging.info("No assessments added for user %s as they have reached the limit.", user_id)


# Set up logging
logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

dayOfWeek = os.getenv('DAY_OF_WEEK', '*').strip()  # Default to '*' (every day) if missing
hourForScheduling = os.getenv('HOUR')
minutesForScheduling = os.getenv('MINUTES')

environment = os.getenv('APP_ENV') 
# Ensure hour and minutes are not None or empty
if not hourForScheduling or not minutesForScheduling:
    error_msg=(
        f"Application: Ni-kshay SETU v3-Pro-Active assessment\n"
        f"ENV: {environment}\n"
        f"file:app.py\n"
        f"Error: HOUR or MINUTES environment variable is missing or empty. Scheduler will not start.\n"
        f"Status: failed\n"

    )
    send_slack_notification(error_msg)
    raise ValueError("HOUR or MINUTES environment variable is missing or empty. Scheduler will not start.")


scheduler = BackgroundScheduler()
trigger = CronTrigger(day_of_week=dayOfWeek, hour=hourForScheduling, minute=minutesForScheduling, timezone=timezone('Asia/Kolkata'))
scheduler.add_job(
    automate_weekly_assessments,
    trigger,
    id='automate_weekly_assessments',
    replace_existing=True  # Ensures job doesn't duplicate
)
scheduler.start()
        

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000,debug=True, use_reloader=False) #change to 5001