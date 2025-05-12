# tests/test_app.py
from datetime import datetime
from bson import ObjectId
import types

def test_get_latest_registry_id_success(mocker):
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })

    # ✅ Step 2: Now safely import app.py function
    from app.tasks.mongo_tasks import get_latest_registry_id

    # Sample ObjectId and mock document
    mock_registry_id = ObjectId()
    mock_document = {"_id": mock_registry_id, "is_active": True}

    # Patch environment variables
    mocker.patch("app.tasks.mongo_tasks.os.getenv", side_effect=lambda key: {
        "MONGO_CLIENT": "mock-client-uri",
        "MONGO_DB": "mock-db",
        "KMAP_COLLECTION": "kmap"
    }[key])

    # Patch MongoClient
    mock_mongo_client = mocker.patch("app.tasks.mongo_tasks.MongoClient")
    mock_db = mocker.MagicMock()
    mock_collection = mocker.MagicMock()

    mock_mongo_client.return_value.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    mock_collection.find_one.return_value = mock_document

    # Call and assert
    result = get_latest_registry_id()
    assert result == mock_registry_id
    
def test_store_assessment_existing_doc_updated(mocker):
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })
    mock_collection = mocker.MagicMock()
    mock_result = mocker.MagicMock(matched_count=1, upserted_id=None)
    mock_collection.update_one.return_value = mock_result

    user_id = "user123"
    assessments = [{"assessment_id": "A1", "title": "TB Basics"}]
    
    from app.tasks.mongo_tasks import store_assessment
    
    store_assessment(user_id, assessments, mock_collection)

    # ✅ Assert update_one was called with correct filter and update
    mock_collection.update_one.assert_called_once()
    args, kwargs = mock_collection.update_one.call_args

    assert args[0] == {"user_id": user_id}
    assert "$push" in args[1]
    assert "$set" in args[1]
    assert "$setOnInsert" in args[1]
    assert kwargs["upsert"] is True

def test_store_assessment_new_doc_inserted(mocker):
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })
    mock_collection = mocker.MagicMock()
    mock_result = mocker.MagicMock(matched_count=0, upserted_id="newid123")
    mock_collection.update_one.return_value = mock_result

    user_id = "new_user"
    assessments = [{"assessment_id": "A2", "title": "Advanced TB"}]
    from app.tasks.mongo_tasks import store_assessment
    store_assessment(user_id, assessments, mock_collection)

    mock_collection.update_one.assert_called_once()


def test_fetch_excluded_questions(mocker):
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })
    
    mock_collection = mocker.MagicMock()

    # Mock aggregation return value (cursor)
    mock_cursor = [
        {"nid": "Q1"},
        {"nid": "Q2"},
        {"nid": "Q3"}
    ]
    mock_collection.aggregate.return_value = mock_cursor

    user_id = "user123"
    
    from app.tasks.fetch_questions_tasks import fetch_excluded_questions
    
    result = fetch_excluded_questions(user_id, mock_collection)

    # Assertions
    assert result == ["Q1", "Q2", "Q3"]
    mock_collection.aggregate.assert_called_once()

    # Optional: verify the aggregation pipeline starts with correct match
    args, _ = mock_collection.aggregate.call_args
    assert {"$match": {"user_id": user_id}} in args[0]

    
def test_fetch_related_questions_from_api(mocker):
    
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })
    
    mock_collection = mocker.MagicMock()

    def side_effect(query, sort=None, projection=None):
        if query["action"] == "Kbase Course Fetched":
            return {
                "payload": {
                    "readContent": [{"contentId": "C1"}, {"contentId": "C2"}]
                }
            }
        elif query["action"] == "Chat Content Read":
            return {
                "payload": {
                    "readContent": [{"contentId": "C2"}, {"contentId": "C3"}]
                }
            }
        return None

    mock_collection.find_one.side_effect = side_effect
    
    from app.tasks.create_assessments_tasks import fetch_related_questions_from_api
    
    result = fetch_related_questions_from_api(mock_collection)

    # Since C2 is duplicated, final result should have unique items
    assert set(result) == {"C1", "C2", "C3"}
    assert len(result) == 3
    
def test_integrate_interaction_questions(mocker):
      
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })
    
    mocker.patch("app.tasks.fetch_questions_tasks.os.getenv", side_effect=lambda k: {
        "MONGO_CLIENT": "mongodb://testuri",
        "MONGO_DB": "testdb",
        "QUESTIONS_COLLECTION": "questions"
    }[k])
    
    mock_mongo = mocker.patch("app.tasks.fetch_questions_tasks.MongoClient")
    mock_db = mocker.MagicMock()
    mock_questions_coll = mocker.MagicMock()
    
    mock_mongo.return_value.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_questions_coll

    mock_questions_coll.find.return_value = [{
        "nid": "Q123",
        "question": "What is TB?",
        "option1": "A", "option2": "B", "option3": "C", "option4": "D",
        "correctAnswer": "option1",
        "CPage_nid": "INT001",
        "langcode": "en"
    }]
    
    mocker.patch("app.tasks.fetch_questions_tasks.fetch_excluded_questions", return_value=["EX1", "EX2"])
    
    user_interaction_ids = ["INT001"]
    existing_assessments = [{
        "assessment_id": "A1",
        "questions": [
            {"nid": "OLD1"}, {"nid": "OLD2"}
        ]
    }]
    user_id = "user123"
    lang = "en"
    
    from app.tasks.fetch_questions_tasks import integrate_user_interaction_questions
    
    result = integrate_user_interaction_questions(
        user_interaction_ids,
        existing_assessments,
        user_id,
        lang,
        assessments_collection=mocker.MagicMock()
    )
    
    assert result[0]["questions"][0]["nid"] == "Q123"
    assert result[0]["questions"][0]["question"] == "What is TB?"
    assert result[0]["questions"][0]["correct_choice"] == "option1"
    assert result[0]["questions"][0]["correctly_answered"] == "no"
    


# def test_fetch_questions_success(mocker):
    
#     mocker.patch.dict("sys.modules", {
#         "app.update": types.SimpleNamespace(
#             process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
#             send_slack_notification=lambda msg: None
#         )
#     })
#     # Step 1: Patch environment variables
#     mocker.patch("app.tasks.fetch_questions_tasks.os.getenv", side_effect=lambda k, default=None: {
#         "MONGO_CLIENT": "mongodb://test-uri",
#         "MONGO_DB": "test-db",
#         "PRIMARY_CADRE_COLLECTION": "primary_cadres",
#         "CADRE_COLLECTION": "cadres"
#     }.get(k, default))

#     # Step 2: Patch MongoClient
#     mock_mongo = mocker.patch("app.tasks.fetch_questions_tasks.MongoClient")
#     mock_db = mocker.MagicMock()
#     mock_mongo.return_value.__getitem__.return_value = mock_db

#     # Step 3: Patch collections
#     primary_cadre_collection = mocker.MagicMock()
#     cadre_collection = mocker.MagicMock()
#     questions_collection = mocker.MagicMock()

#     mock_db.__getitem__.side_effect = lambda name: {
#         "primary_cadres": primary_cadre_collection,
#         "cadres": cadre_collection
#     }[name]

#     primary_cadre_collection.find.return_value = [{"_id": "P1"}]
#     cadre_collection.find.return_value = [{"_id": "C1"}]

#     # Step 4: Patch external dependencies
#     mocker.patch("app.tasks.fetch_questions_tasks.fetch_excluded_questions", return_value=["E1", "E2"])
#     mocker.patch("app.tasks.mongo_tasks.get_latest_registry_id", return_value="RID123")
#     mocker.patch("app.tasks.fetch_questions_tasks.uuid4", side_effect=[f"uuid-{i}" for i in range(3)])
#     mocker.patch("app.tasks.fetch_questions_tasks.datetime").utcnow.return_value = datetime(2023, 1, 1)

#     # Step 5: Patch questions_collection directly
#     questions_collection.find.return_value.limit.return_value = [
#         {
#             "nid": f"Q{i}",
#             "question": f"Question {i}",
#             "option1": "A", "option2": "B",
#             "option3": "C", "option4": "D",
#             "correctAnswer": "option1"
#         } for i in range(15)  # 3 assessments * 5 questions each
#     ]

#     # Call the function
#     user_id = "user123"
#     lang = "en"
#     num_assessments = 3
#     cadre_id = "cadre99"
#     from app.tasks.fetch_questions_tasks import fetch_questions
#     result = fetch_questions(
#         user_id,
#         lang,
#         num_assessments,
#         assessments_collection=mocker.MagicMock(),
#         questions_collection=questions_collection,
#         cadre_id=cadre_id
#     )

#     # ✅ Assertions
#     assert isinstance(result, list)
#     assert len(result) == 3
#     for i, assessment in enumerate(result):
#         assert assessment["assessment_id"] == f"uuid-{i}"
#         assert assessment["title"] == f"Pro-Active-{i + 1}"
#         assert len(assessment["questions"]) == 5
#         assert assessment["pending"] == "yes"


# def test_create_assessments(mocker):
#     mocker.patch.dict("sys.modules", {
#         "app.update": types.SimpleNamespace(
#             process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
#             send_slack_notification=lambda msg: None
#         )
#     })
    
#     mocker.patch("app.tasks.create_assessments_tasks.os.getenv", side_effect=lambda k: {
#         "MONGO_CLIENT": "mongodb://test-uri",
#         "MONGO_DB": "test-db",
#         "QUESTIONS_COLLECTION": "questions",
#         "ASSESSMENTS_COLLECTION": "assessments",
#         "SUBSCRIBER_ACTIVITY_COLLECTION": "subscriber_activity"
#     }[k])
    
#     # Step 2: Patch MongoClient
#     mock_mongo = mocker.patch("app.tasks.create_assessments_tasks.MongoClient")
#     mock_db = mocker.MagicMock()
#     mock_collections = {
#         "questions": mocker.MagicMock(),
#         "assessments": mocker.MagicMock(),
#         "subscriber_activity": mocker.MagicMock()
#     }
#     mock_mongo.return_value.__getitem__.return_value = mock_db
#     mock_db.__getitem__.side_effect = lambda name: mock_collections [name]
    
#     mock_collections['subscriber_activity'].find.return_value = [
#         {"action": "Kbase Cource Fetched"}, {"action": "Chat Content Read"}
#     ]
    
#     mocker.patch("app.tasks.create_assessments_tasks.fetch_related_questions_from_api", return_value=["INT1","INT2"])
    
#     mocker.patch("app.tasks.fetch_questions_tasks.fetch_questions", return_value=[
#         {"assessment_id": "uuid1", "title": "Assessment 1", "questions": [{"nid": "Q1"}]}
#     ])
    
#     mocker.patch("app.tasks.create_assessments_tasks.integrate_user_interaction_questions", return_value=[
#         {"assessment_id": "uuid1", "title": "Assessment 1", "questions": [{"nid": "Q1"}, {"nid": "QX"}]}
#     ])

#     mock_store = mocker.patch("app.tasks.mongo_tasks.store_assessment")
#     from app.tasks.create_assessments_tasks import create_assessments
#     # Step 5: Call the function
#     result = create_assessments("user123", "en", 1, "cadre1")

#     # Step 6: Assertions
#     assert isinstance(result, list)
#     assert len(result) == 1
#     assert result[0]["questions"][1]["nid"] == "QX"
#     mock_store.assert_called_once()
    
    
def test_log_assessment_attempt(mocker):
    mocker.patch.dict("sys.modules", {
        "app.update": types.SimpleNamespace(
            process_assessment_submission=lambda *args, **kwargs: ("mocked", 200),
            send_slack_notification=lambda msg: None
        )
    })
    
    mocker.patch("app.tasks.mongo_tasks.os.getenv", side_effect=lambda k: {
        "MONGO_CLIENT": "mongodb://test-uri",
        "MONGO_DB": "test-db",
        "ATTEMPT_LOG_COLLECTION": "attempt_log"
    }[k])
    
    mock_mongo = mocker.patch("app.tasks.mongo_tasks.MongoClient")
    mock_db = mocker.MagicMock()
    mock_collection = mocker.MagicMock()
    mock_mongo.return_value.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    
    
    from app.tasks.mongo_tasks import log_assessment_attempt
    
    # Patch datetime
    mock_time = datetime(2023, 1, 1)
    mocker.patch("app.tasks.mongo_tasks.datetime").now.return_value = mock_time

    # Call function
    log_assessment_attempt(
        user_id="user123",
        cadre_id="cadreA",
        status="success",
        num_assessments=2,
        error_message=None
    )

    # Assert insert_one called with expected document
    mock_collection.insert_one.assert_called_once_with({
        "user_id": "user123",
        "cadre_id": "cadreA",
        "status": "success",
        "num_assessments": 2,
        "error": None,
        "timestamp": mock_time
    })