from pymongo import MongoClient

from flask import jsonify 

from datetime import datetime
from bson import ObjectId
import logging
import os

from app.slack_alert import send_slack_notification

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='warn.log',level=logging.WARNING)
logging.basicConfig(filename='info.log',level=logging.INFO)
logging.basicConfig(filename='error.log',level=logging.ERROR)
logging.getLogger().setLevel(logging.INFO)


def process_assessment_submission(user_id, assessment_id, user_responses):
    logging.info("user id: %s", user_id)
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]
    environment = os.getenv('APP_ENV') 


    assessments_collection = db[os.getenv("ASSESSMENTS_COLLECTION")]
    assessments_count_collection = db[os.getenv("PROASSESSMENT_RESPONSES_COLLECTION")] #assessment collection

    try:
        # Fetch the document containing the assessments
        doc = assessments_collection.find_one({"user_id": user_id, "assessments.assessment_id": assessment_id})
        history =[]
        if doc:
            assessments = doc['assessments']
            # Find the specific assessment
            assessment = next((a for a in assessments if a['assessment_id'] == assessment_id), None)
            assessment_title = assessment['title']
            if assessment:
                logging.info("assessment present")
                questions = assessment['questions']
                all_answered_correctly = True  # Track if all questions are answered correctly
                total_count = len(questions)
                correctly_answered_count = 0 
                skipped_count = 0
                for response in user_responses:  # Assume user_responses is a list of dicts with 'nid' and 'user_answer'
                    question = next((q for q in questions if q['nid'] == response['nid']), None)
                    if question:
                        if response['user_answer'] == '' or response['user_answer'] is None:
                            skipped_count += 1
                            is_correct = 'skipped'  # You can use 'skipped' or any appropriate marker in your database
                        else:
                            # Check if the user's answer is correct
                            is_correct = 'yes' if question['correct_choice'] == response['user_answer'] else 'no'
                            if is_correct == 'no':
                                all_answered_correctly = False
                            else:
                                correctly_answered_count += 1  # Increment counter if answer is correct

                            user_answer_key = response['user_answer']
                            user_answer_text = question.get(user_answer_key, "Unknown") if user_answer_key else None  

                            if response['user_answer']: 
                                history.append({
                                    "questionId": response['nid'],  
                                    "answer": user_answer_text,  
                                    "isCorrect": "true" if is_correct== "yes" else "false",
                                    "selectedOption": response['user_answer'],
                                })
                                    # Update the 'correctly_answered' field for the specific question
                            update_path = f"assessments.$[assess].questions.$[ques].correctly_answered"
                            assessments_collection.update_one(
                                {"_id": doc['_id']},
                                {"$set": {update_path: is_correct}},
                                array_filters=[{"assess.assessment_id": assessment_id}, {"ques.nid": response['nid']}]
                            )
                    else:
                        print(f"No question found with nid: {response['nid']}")
                        logging.info("No question found with nid: %s", response['nid'])
                        all_answered_correctly = False  # If a question is missing, we assume it's not fully answered
                        
                not_correctly_answered_count = total_count - (correctly_answered_count + skipped_count)
                attempted = total_count - skipped_count
                logging.info("attempted %s",attempted)
                logging.info("questions %s",questions)
                # Check if all questions have been answered (correct or not) and update the 'pending' field
                pending_questions = [q for q in questions if 'correctly_answered' not in q]
                logging.info("pending questions %s",pending_questions)
                if not pending_questions:
                    # All questions have been processed, update 'pending' to 'no'
                    assessments_collection.update_one(
                        {"_id": doc['_id']},
                        {"$set": {"assessments.$[assess].pending": "no","assessments.$[assess].correct": correctly_answered_count, "assessments.$[assess].incorrect": not_correctly_answered_count, "assessments.$[assess].skipped": skipped_count,"updated_at": datetime.utcnow()}},
                        array_filters=[{"assess.assessment_id": assessment_id}]
                    )
                    
                    assessments_count_collection.insert_one(
                        { "assessmentId": assessment_id, "assessmentTitle":assessment_title,"userId": ObjectId(user_id), "totalMarks":total_count,"obtainedMarks": correctly_answered_count,"attempted":attempted,"rightAnswer":correctly_answered_count, "wrongAnswer": not_correctly_answered_count, "skip": skipped_count, "history":history, "createdAt":datetime.utcnow(), "updatedAt":datetime.utcnow()})
                    #return a statement with 200ok
                    logging.info('"message": "Assessment submitted successfully"')
                    return jsonify({"message": "Assessment submitted successfully"}), 200
            else:
                print(f"No assessment found with assessment_id: {assessment_id}")
                logging.info("No assessment found with assessment_id: %s", assessment_id )
                return jsonify({"message": f"No assessment found with assessment_id: {assessment_id}"}),400
        else:
            print(f"No document found with user_id: {user_id} and assessment_id: {assessment_id}")
            logging.info("No document found with user_id: %s and assessment_id: %s", user_id, assessment_id)
            return jsonify({"message": f"No document found with user_id: {user_id} and assessment_id: {assessment_id}"}),400
    except Exception as e:
        print(f"An error occurred while processing the assessment: {e}")
        error_msg=(
            f"Application: Ni-kshay SETU v3-Pro-Active assessment\n"
            f"ENV: {environment}\n"
            f"file:update.py\n"
            f"Error: {e}\n"
            f"Status: failed\n"
        )
        send_slack_notification(error_msg)

        return jsonify({"message": "An error occurred while processing the assessment"}), 500
