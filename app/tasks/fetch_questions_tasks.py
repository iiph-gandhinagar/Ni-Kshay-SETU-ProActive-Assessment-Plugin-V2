from pymongo import MongoClient

import os
import logging

from pytz import timezone
from datetime import datetime, timezone
from uuid import uuid4  # To generate unique IDs

from app.tasks.mongo_tasks import get_latest_registry_id

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename='warn.log',level=logging.WARNING)
logging.basicConfig(filename='info.log',level=logging.INFO)
logging.basicConfig(filename='error.log',level=logging.ERROR)
logging.getLogger().setLevel(logging.INFO)


def fetch_excluded_questions(user_id, assessments_collection):
    print(f"Fetching excluded questions for user_id: {user_id}")
    logging.info("Fetching excluded questions for user_id: %s" , user_id)
    correctly_answered_questions = assessments_collection.aggregate([
        {"$match": {"user_id": user_id}},
        {"$unwind": "$assessments"},
        {"$unwind": "$assessments.questions"},
        {"$match": {"assessments.questions.correctly_answered": "yes"}},
        {"$project": {
            "nid": "$assessments.questions.nid"
        }}
    ])
    
    correctly_answered = list(correctly_answered_questions)  # Convert cursor to list
    excluded_nids = [q['nid'] for q in correctly_answered]
    print(f"Excluded questions: {excluded_nids}")
    logging.info("Excluded questions: %s" , excluded_nids)
    
    return excluded_nids


def fetch_questions(user_id, lang, num_assessments,assessments_collection,questions_collection, cadre_id):
    questions_per_assessment = int(os.getenv('QUESTIONS_PER_ASSESSMENT'))
    total_questions_needed = num_assessments * questions_per_assessment
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]

    query = {
        'audienceId':cadre_id,
    }
    projection = {
        '_id': 1
    }
    cadre_collection = db[os.getenv("PRIMARY_CADRE_COLLECTION")]
    final_cadres = list(cadre_collection.find(query, projection=projection))
    print('final_cadres', final_cadres)
    logging.info('final_cadres: %s ', final_cadres)
    object_ids = [item['_id'] for item in final_cadres]

    query_2 ={
        "cadreGroup": {'$in': object_ids},
    }
    projection_2 = {
        '_id': 1,
       
    }
    cadre_collection_2 = db[os.getenv("CADRE_COLLECTION")]

    final_cadres_2 = list(cadre_collection_2.find(query_2, projection=projection_2))
    cadre_ids = [item['_id'] for item in final_cadres_2]
    print("cadre_ids", cadre_ids)
    logging.info('cadre_ids: %s ', cadre_ids)
    final_target_audience = [str(obj_id) for obj_id in cadre_ids]

    # Define difficulty levels in the order you want to fetch questions
    difficulty_levels = os.getenv("DIFFICULTY_LEVELS")

    processed_questions = []
    excluded_questions = fetch_excluded_questions(user_id, assessments_collection)
    print(excluded_questions)
    # Adjust the limit to fetch the total questions needed across all assessments
    latest_registry_id = get_latest_registry_id()
    questions_fetched = 0
    for level in difficulty_levels:
        print(level)
        
        if questions_fetched >= total_questions_needed:
            print("Fetching questions")
            break
        print("questions_fetched:1 ", questions_fetched)
        logging.info("questions_fetched: %s", questions_fetched)
        remaining_questions = total_questions_needed - questions_fetched
        print("total_questions_needed:1 ", total_questions_needed)
        logging.info("total_questions_needed: %s", total_questions_needed)
        print("remaining_questions1", remaining_questions)
        logging.info("remaining_questions: %s", remaining_questions)
        print("language1",lang)
        logging.info("language: %s", lang)
        query = {
            "registry_id": latest_registry_id,
            "nid": {"$nin": excluded_questions},
            "language": lang,
            "category": "Pro active questions",
            "level": level,
            "$or": [
                # Case 1: is_allowed_cadre is false, match with cadre_id
                {
                    "isAllCadre": False,
                    "cadreId": {"$in": final_target_audience}
                },
                # Case 2: is_allowed_cadre is true, cadre_id is an empty array
                {
                    "isAllCadre": True,
                    "cadreId": []
                }
            ]
        }
        
        projection = {
            "_id": 0, "nid": 1, "question": 1, "option1": 1,"option2": 1,"option3": 1,"option4": 1, "correctAnswer": 1
        }
        print('remaining question1',remaining_questions)
        logging.info("remaining question: %s", remaining_questions)
        available_questions = list(questions_collection.find(query, projection=projection).limit(remaining_questions))
        print("Available questions1", available_questions)
        logging.info("Available questions: %s", available_questions)
        for question in available_questions:
            
            processed_question = {
                'nid': question['nid'],
                'question': question['question'],
                'option1': question['option1'],
                'option2': question['option2'],
                'option3': question['option3'],
                'option4': question['option4'],
                'correct_choice': question['correctAnswer'],  # Adjust index for zero-based
                'correctly_answered': 'no'
            }
            processed_questions.append(processed_question)
            questions_fetched += 1
        # Update excluded_questions list to avoid repeats
        excluded_questions.extend([q['nid'] for q in available_questions])
   
    if questions_fetched < total_questions_needed:
        # Not enough questions to create the required number of assessments
        return {'error': f'Insufficient questions available for user {user_id} with cadre {cadre_id} to create {num_assessments} assessments in {lang} language.'}


    # Divide the fetched questions into the required number of assessments
    assessments = []
    for i in range(num_assessments):
        start_index = i * questions_per_assessment
        end_index = start_index + questions_per_assessment
        assessment_questions = processed_questions[start_index:end_index]
        assessments.append({
            'assessment_id': str(uuid4()),  # Generate a unique identifier for each assessment
            'title': f"Pro-Active-{i + 1}",
            'questions': assessment_questions,
            'pending':'yes',
            'created_at': datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
    return assessments

def integrate_user_interaction_questions(user_interaction_ids, existing_assessments, user_id,lang,assessments_collection):
    client = MongoClient(os.getenv('MONGO_CLIENT'))
    db = client[os.getenv('MONGO_DB')]

    questions_collection = db[os.getenv("QUESTIONS_COLLECTION")]
    
    excluded_nids = fetch_excluded_questions(user_id, assessments_collection)
    assessment_q_ids = [q_id for assessment in existing_assessments for q in assessment['questions'] for q_id in [q['nid']]]
    excluded_ids = assessment_q_ids + excluded_nids
    print("langcode" ,lang)
    logging.info("langcode: %s", lang)
    # Fetch questions that match the user interaction IDs
    matched_questions = list(questions_collection.find({
        "CPage_nid": {"$in": user_interaction_ids},
        "langcode": lang,
        "nid": {"$nin": excluded_ids}  # Exclude questions that are in the excluded list
    }))
    used_question_indices = []  # Track indices of used questions to avoid repetition

    # Iterate over the matched questions and place each in the first available assessment slot
    for matched_question in matched_questions:
        placed = False
        for assessment in existing_assessments:
            if not placed:
                for i, question in enumerate(assessment['questions']):
                    # Replace the first non-replaced question in the assessment
                    if i not in used_question_indices:
                      
                        assessment['questions'][i] = {
                            'nid': matched_question['nid'],
                            'question': matched_question['question'],
                            'option1': matched_question['option1'],
                            'option2': matched_question['option2'],
                            'option3': matched_question['option3'],
                            'option4': matched_question['option4'],
                            'correct_choice': matched_question['correctAnswer'],  # Adjust index for zero-based
                            'correctly_answered': 'no'
                        }
                        used_question_indices.append(i)  # Mark this index as used
                        placed = True
                        break

    return existing_assessments
   