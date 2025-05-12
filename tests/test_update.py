# tests/test_update.py

from bson import ObjectId
from datetime import datetime
from flask import Response
import json


def test_process_assessment_submission_success(mocker):
    # Fake inputs
    mock_user_id = str(ObjectId())
    mock_assessment_id = "A1"
    mock_user_responses = [
        {"nid": "q1", "user_answer": "a"},
        {"nid": "q2", "user_answer": "b"}
    ]

    # Fake assessment document from Mongo
    mock_doc = {
        "_id": ObjectId(mock_user_id),
        "assessments": [
            {
                "assessment_id": mock_assessment_id,
                "title": "TB Knowledge",
                "pending": "yes",
                "questions": [
                    {"nid": "q1", "correct_choice": "a", "a": "Yes", "b": "No","correctly_answered":"no"},
                    {"nid": "q2", "correct_choice": "a", "a": "Yes", "b": "No", "correctly_answered":"no"}
                ]
            }
        ]
    }

    # Patch os.getenv
    mocker.patch("app.update.os.getenv", side_effect=lambda key: {
        "MONGO_CLIENT": "mock-client-uri",
        "MONGO_DB": "mock-db",
        "ASSESSMENTS_COLLECTION": "assessments",
        "PROASSESSMENT_RESPONSES_COLLECTION": "assessment_responses",
        "APP_ENV": "test"
    }[key])

    # Patch MongoClient
    mock_mongo_client = mocker.patch("app.update.MongoClient")
    mock_db = mocker.MagicMock()
    mock_assessments_coll = mocker.MagicMock()
    mock_response_coll = mocker.MagicMock()

    mock_mongo_client.return_value.__getitem__.return_value = mock_db
    mock_db.__getitem__.side_effect = lambda name: {
        "assessments": mock_assessments_coll,
        "assessment_responses": mock_response_coll
    }[name]

    mock_assessments_coll.find_one.return_value = mock_doc
    mock_assessments_coll.update_one.return_value = None
    mock_response_coll.insert_one.return_value = None

    # Patch datetime
    mocker.patch("app.update.datetime").utcnow.return_value = datetime(2023, 1, 1)

    # Patch jsonify
    mocker.patch("app.update.jsonify", side_effect=lambda d: Response(json.dumps(d), mimetype="application/json"))

    # Patch Slack notification
    mocker.patch("app.update.send_slack_notification")

    from app.update import process_assessment_submission
    # Run
    response, status_code = process_assessment_submission(mock_user_id, mock_assessment_id, mock_user_responses)

    # Assert
    assert status_code == 200
    body = json.loads(response.data)
    assert body["message"] == "Assessment submitted successfully"
