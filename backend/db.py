import statistics
from bson import ObjectId
from pymongo import MongoClient
import asyncio
import threading
import time
from pytz import timezone
from datetime import datetime
import logging
from dotenv import load_dotenv
import os
import hashlib
import json
# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to MongoDB Atlas using environment variables
uri = os.getenv('MONGODB_URI')
if not uri:
    raise ValueError("MONGODB_URI environment variable is not set")

client = MongoClient(uri)
db9 = client[os.getenv('MONGODB_DB_CLASS9', 'student_database')]
db10 = client[os.getenv('MONGODB_DB_CLASS10', 'student_database_class10')]

data_store = {
    9: {
        "collections": [
            {"Users": []},
            {
                "DivA": {"Stats": {}, "Subjects": {}},
                "DivB": {"Stats": {}, "Subjects": {}},
                "DivC": {"Stats": {}, "Subjects": {}},
                "DivD": {"Stats": {}, "Subjects": {}},
                "DivE": {"Stats": {}, "Subjects": {}}
            },
            {"ExamHistory": {}},
            {"Exams": {}},
            {"Leaderboard": {}},
            {"Tests": {}},
            {"InactiveTests": {}}
        ]
    },
    10: {
        "collections": [
            {"Users": []},
            {
                "DivA": {"Stats": {}, "Subjects": {}},
                "DivB": {"Stats": {}, "Subjects": {}},
                "DivC": {"Stats": {}, "Subjects": {}},
                "DivD": {"Stats": {}, "Subjects": {}},
                "DivE": {"Stats": {}, "Subjects": {}}
            },
            {"ExamHistory": {}},
            {"Exams": {}},
            {"Leaderboard": {}},
            {"Tests": {}},
            {"InactiveTests": {}}
        ]
    }
}

# Queue for MongoDB updates
update_queue = asyncio.Queue()

def convert_mongo_doc(doc):
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, (dict, list)):
                doc[key] = convert_mongo_doc(value)
    elif isinstance(doc, list):
        for i, item in enumerate(doc):
            doc[i] = convert_mongo_doc(item)
    return doc

def download_data():
    """Downloads all data from MongoDB to RAM for both classes."""
    start_time = time.time()
    logger.info("Starting data download from MongoDB to RAM")

    try:
        for class_num, db in [(9, db9), (10, db10)]:
            # Clear existing data
            data_store[class_num]['collections'][0]['Users'].clear()
            for div in ['A', 'B', 'C', 'D', 'E']:
                data_store[class_num]['collections'][1][f'Div{div}']['Stats'].clear()
                data_store[class_num]['collections'][1][f'Div{div}']['Subjects'].clear()
            data_store[class_num]['collections'][2]['ExamHistory'].clear()
            data_store[class_num]['collections'][3]['Exams'].clear()
            data_store[class_num]['collections'][4]['Leaderboard'].clear()
            data_store[class_num]['collections'][5]['Tests'].clear()
            data_store[class_num]['collections'][6]['InactiveTests'].clear()

            # Download Users
            logger.info(f"Downloading Users for Class {class_num}")
            data_store[class_num]['collections'][0]['Users'] = [
                convert_mongo_doc(user) for user in db['Users'].find()
            ]

            # Download Division data
            for div in ['A', 'B', 'C', 'D', 'E']:
                logger.info(f"Downloading Div{div} data for Class {class_num}")
                div_data = data_store[class_num]['collections'][1][f'Div{div}']
                div_collection = db[f'Div{div}']

                # Stats
                stats_doc = div_collection.find_one({'Stats': {'$exists': True}})
                div_data['Stats'] = convert_mongo_doc(stats_doc['Stats'] if stats_doc else {})

                # Subjects
                subjects_doc = div_collection.find_one({'Subjects': {'$exists': True}})
                div_data['Subjects'] = convert_mongo_doc(subjects_doc['Subjects'] if subjects_doc else {})

            # Download ExamHistory
            logger.info(f"Downloading ExamHistory for Class {class_num}")
            exam_history_doc = db['ExamHistory'].find_one({'_id': 'exam_history'}) or {}
            data_store[class_num]['collections'][2]['ExamHistory'] = convert_mongo_doc(exam_history_doc)

            # Download Exams
            logger.info(f"Downloading Exams for Class {class_num}")
            exams = list(db['Exams'].find())
            data_store[class_num]['collections'][3]['Exams'] = {
                exam['exam-id']: convert_mongo_doc(exam) for exam in exams
            }

            # Download Leaderboard
            logger.info(f"Downloading Leaderboard for Class {class_num}")
            leaderboard_data = list(db['Leaderboard'].find())
            data_store[class_num]['collections'][4]['Leaderboard'] = {
                doc['_id']: convert_mongo_doc(doc) for doc in leaderboard_data
            }

            # Download Tests
            logger.info(f"Downloading Tests for Class {class_num}")
            tests = list(db['Tests'].find())
            data_store[class_num]['collections'][5]['Tests'] = {
                test['test-id']: convert_mongo_doc(test) for test in tests
            }

            # Download InactiveTests
            logger.info(f"Downloading InactiveTests for Class {class_num}")
            inactive_tests = list(db['InactiveTests'].find())
            data_store[class_num]['collections'][6]['InactiveTests'] = {
                test['test-id']: convert_mongo_doc(test) for test in inactive_tests
            }

        end_time = time.time()
        logger.info(f"Data download completed in {end_time - start_time:.2f} seconds")

        # Log statistics about the downloaded data
        for class_num in [9, 10]:
            logger.info(f"Class {class_num} statistics:")
            logger.info(f"Users: {len(data_store[class_num]['collections'][0]['Users'])}")
            for div in ['A', 'B', 'C', 'D', 'E']:
                logger.info(f"Div{div} Stats: {len(data_store[class_num]['collections'][1][f'Div{div}']['Stats'])}")
                logger.info(f"Div{div} Subjects: {len(data_store[class_num]['collections'][1][f'Div{div}']['Subjects'])}")
            logger.info(f"ExamHistory entries: {len(data_store[class_num]['collections'][2]['ExamHistory'])}")
            logger.info(f"Exams: {len(data_store[class_num]['collections'][3]['Exams'])}")
            logger.info(f"Leaderboard entries: {len(data_store[class_num]['collections'][4]['Leaderboard'])}")
            logger.info(f"Tests: {len(data_store[class_num]['collections'][5]['Tests'])}")
            logger.info(f"Inactive Tests: {len(data_store[class_num]['collections'][6]['InactiveTests'])}")

    except Exception as e:
        logger.error(f"Error during data download: {str(e)}")
        raise

    return data_store

def get_user(user_id, class10=False):
    """Fetches user data from RAM."""
    class_num = 10 if class10 else 9
    users = data_store[class_num]['collections'][0]['Users']
    return next((user for user in users if user['id'] == user_id), None)
def update_user_tasks(user_id, tasks, class10=False, coins=None):
    """Updates user tasks and optionally coins in RAM and MongoDB."""
    class_num = 10 if class10 else 9
    db = db10 if class10 else db9

    update_set = {'tasks': tasks}
    if coins is not None:
        update_set['coins'] = coins

    # Update RAM
    users = data_store[class_num]['collections'][0]['Users']
    user_index = next((index for (index, d) in enumerate(users) if d["id"] == user_id), None)
    if user_index is not None:
        users[user_index]['tasks'] = tasks
        if coins is not None:
            users[user_index]['coins'] = coins

    # Update MongoDB
    db['Users'].update_one({'id': user_id}, {'$set': update_set})

def get_division(user_id, class10=False):
    """Determines the division of a user."""
    user = get_user(user_id, class10)
    return user['division'] if user else None

def get_user_stats(user_id, class10=False):
    """Fetches user stats from RAM."""
    class_num = 10 if class10 else 9
    division = get_division(user_id, class10)
    if not division:
        return None
    stats = data_store[class_num]['collections'][1][f'Div{division}']['Stats']
    return stats.get(user_id)

def get_user_subjects(user_id, subject=None, class10=False):
    class_num = 10 if class10 else 9
    division = get_division(user_id, class10)
    if not division:
        return None
    subjects = data_store[class_num]['collections'][1][f'Div{division}']['Subjects'].get(user_id, [])
    if subject:
        subject_stats = next((subj for subj in subjects if subj['subject'].lower() == subject.lower()), None)
        if subject_stats:
            subject_stats.pop('_id', None)  # Remove _id if it exists
        return subject_stats
    return [subj for subj in subjects if '_id' not in subj]

def get_user_exam_history(user_id, class10=False):
    """Fetches user exam history from the data store."""
    class_num = 10 if class10 else 9
    user_exam_history = data_store[class_num]['collections'][2]['ExamHistory'].get(user_id, {})
    if user_exam_history:
        overview_stats = user_exam_history.get('overview-stats', [])
        return overview_stats
    else:
        return []

def get_all_lessons_for_subject(subject, class10=False):
    """Fetches all lessons for a given subject from the data files."""

    lessons_file = "lessons10.json" if class10 else "lessons.json"
    data_path = os.path.join(os.path.dirname(__file__), "data")
    with open(os.path.join(data_path, lessons_file)) as f:
        lessons = json.load(f)
    return lessons.get(subject, [])

def update_user_stats(user_id, new_stats, class10=False):
    """Updates user stats in RAM and queues update for MongoDB."""
    class_num = 10 if class10 else 9
    division = get_division(user_id, class10)
    if not division:
        return False

    try:
        # Update RAM
        div_stats = data_store[class_num]['collections'][1][f'Div{division}']['Stats']
        if user_id not in div_stats:
            div_stats[user_id] = {}
        div_stats[user_id].update(new_stats)

        # Queue update for MongoDB
        update_queue.put_nowait(('Stats', f'Div{division}', user_id, new_stats, class_num))

        # Perform immediate update to MongoDB
        db = db10 if class10 else db9
        db[f'Div{division}'].update_one(
            {'Stats': {'$exists': True}},
            {'$set': {f'Stats.{user_id}': div_stats[user_id]}},
            upsert=True
        )

        return True
    except Exception as e:
        print(f"Error updating user stats: {e}")
        return False

def update_user_subjects(user_id, subject, new_data, class10=False):
    """Updates user subject data in RAM and queues update for MongoDB."""
    class_num = 10 if class10 else 9
    division = get_division(user_id, class10)
    if division:
        subjects = data_store[class_num]['collections'][1][f'Div{division}']['Subjects'].get(user_id, [])
        subject_index = next((index for (index, d) in enumerate(subjects) if d["subject"] == subject), None)
        if subject_index is not None:
            subjects[subject_index].update(new_data)
        else:
            subjects.append(new_data)

        # Update RAM
        data_store[class_num]['collections'][1][f'Div{division}']['Subjects'][user_id] = subjects

        # Queue update for MongoDB
        update_queue.put_nowait(('Subjects', f'Div{division}', user_id, subjects, class_num))

        # Perform immediate update to MongoDB
        db = db10 if class10 else db9
        db[f'Div{division}'].update_one(
            {'Subjects': {'$exists': True}},
            {'$set': {f'Subjects.{user_id}': subjects}},
            upsert=True
        )

def add_exam_to_history(user_id, overview_stats, class10=False):
    """Adds an exam to user's exam history in RAM and MongoDB."""
    class_num = 10 if class10 else 9

    # Update RAM
    if user_id not in data_store[class_num]['collections'][2]['ExamHistory']:
        data_store[class_num]['collections'][2]['ExamHistory'][user_id] = {"overview-stats": []}

    data_store[class_num]['collections'][2]['ExamHistory'][user_id]["overview-stats"].append(overview_stats)

    # Update MongoDB directly
    try:
        db = db10 if class10 else db9
        presult = db['ExamHistory'].update_one(
            {'_id': 'exam_history'},
            {'$push': {f'{user_id}.overview-stats': overview_stats}},
            upsert=True
        )
    except Exception as e:
        print(f"Error updating MongoDB: {e}")
    # Still queue the update for any additional processing
    update_queue.put_nowait(('ExamHistory', user_id, overview_stats, class_num))

def initialize_overview_stats(user_id, class10=False):
    """Initialize overview stats for a new user."""
    db = db10 if class10 else db9
    overview_stats = {
        "user_id": user_id,
        "subjects": {
            "Math": {"exams_given": 0, "highest_marks": 0, "average_percentage": 0},
            "SS": {"exams_given": 0, "highest_marks": 0, "average_percentage": 0},
            "English": {"exams_given": 0, "highest_marks": 0, "average_percentage": 0},
            "Science": {"exams_given": 0, "highest_marks": 0, "average_percentage": 0}
        }
    }
    db['overview_stats'].insert_one(overview_stats)
    return overview_stats

def get_overview_stats(user_id, class10=False):
    """Get overview stats for a user, initializing if they don't exist."""
    db = db10 if class10 else db9
    stats = db['overview_stats'].find_one({"user_id": user_id})
    
    if not stats:
        # Initialize stats if they don't exist
        stats = initialize_overview_stats(user_id, class10)
    
    if stats:
        # Remove the _id field as it's not needed in the response
        stats.pop('_id', None)
        return stats
    return None

def update_overview_stats(user_id, subject, exam_marks, total_marks, class10=False):
    """Update overview stats for a user after an exam."""
    db = db10 if class10 else db9
    stats = get_overview_stats(user_id, class10)
    if stats:
        subject_stats = stats['subjects'][subject]
        subject_stats['exams_given'] += 1
        subject_stats['highest_marks'] = max(
            subject_stats['highest_marks'], exam_marks)

        # Calculate new average percentage
        old_average = subject_stats['average_percentage']
        old_total = old_average * (subject_stats['exams_given'] - 1)
        new_percentage = (exam_marks / total_marks) * 100
        new_average = (old_total + new_percentage) / \
            subject_stats['exams_given']
        subject_stats['average_percentage'] = round(new_average, 2)

        db['overview_stats'].update_one(
            {'user_id': user_id},
            {'$set': {f'subjects.{subject}': subject_stats}}
        )

def add_exam(exam_data, class10=False):
    """Adds a new exam to the Exams collection in both RAM and MongoDB."""
    class_num = 10 if class10 else 9
    exam_id = exam_data['exam-id']

    # Add to RAM
    data_store[class_num]['collections'][3]['Exams'][exam_id] = exam_data

    # Add to MongoDB
    try:
        db = db10 if class10 else db9
        result = db['Exams'].insert_one(exam_data)
        return exam_data
    except Exception as e:
        print(f"Error adding exam to MongoDB: {e}")
        return None

def get_exam(exam_id, class10=False):
    """Retrieves an exam by exam-id from RAM or MongoDB."""
    class_num = 10 if class10 else 9

    # Check in RAM
    exam = data_store[class_num]['collections'][3]['Exams'].get(exam_id)
    if exam:
        return convert_mongo_doc(exam)

    print("Exam not found in RAM, checking MongoDB...")

    # If not in RAM, try to fetch from MongoDB
    db = db10 if class10 else db9
    exam = db['Exams'].find_one({"exam-id": exam_id})
    if exam:
        # Convert to JSON-serializable format
        exam = convert_mongo_doc(exam)
        # Add to RAM for future use
        data_store[class_num]['collections'][3]['Exams'][exam_id] = exam
        return exam

    print(f"Exam with id {exam_id} not found in RAM or MongoDB")
    return None

def add_test(test_data, class10=False):
    """Adds a new test to the Tests collection in both RAM and MongoDB."""
    if not test_data.get('expiration_date'):
        raise ValueError("Test data must include an expiration date.")
    class_num = 10 if class10 else 9
    test_id = test_data['test-id']

   # Add to RAM
    data_store[class_num]['collections'][5]['Tests'][test_id] = test_data

   # Add to MongoDB
    try:
       db = db10 if class10 else db9
       result = db['Tests'].insert_one(test_data)
       return test_data
    except Exception as e:
       print(f"Error adding test to MongoDB: {e}")
       return None

def get_test(test_id, class10=False):
   """Retrieves a test by test-id from RAM or MongoDB."""
   class_num = 10 if class10 else 9

   # Check in RAM
   test = data_store[class_num]['collections'][5]['Tests'].get(test_id)
   if test:
       return convert_mongo_doc(test)

   # If not in RAM, try to fetch from MongoDB
   db = db10 if class10 else db9
   test = db['Tests'].find_one({"test-id": test_id})
   if test:
       test = convert_mongo_doc(test)
       data_store[class_num]['collections'][5]['Tests'][test_id] = test
       return test

   return None

def get_all_tests(class10=False):
   """Retrieves all tests from RAM."""
   class_num = 10 if class10 else 9
   return list(data_store[class_num]['collections'][5]['Tests'].values())

def update_test(test_id, updated_data, class10=False):
   """Updates an existing test in both RAM and MongoDB."""
   class_num = 10 if class10 else 9

   # Update in RAM
   if test_id in data_store[class_num]['collections'][5]['Tests']:
       data_store[class_num]['collections'][5]['Tests'][test_id].update(updated_data)

   # Update in MongoDB
   db = db10 if class10 else db9
   result = db['Tests'].update_one({'test-id': test_id}, {'$set': updated_data})

   return result.modified_count > 0

def delete_test(test_id, class10=False):
   """Deletes a test from active tests in both RAM and MongoDB."""
   class_num = 10 if class10 else 9
   
   # Delete from RAM
   if test_id in data_store[class_num]['collections'][5]['Tests']:
       del data_store[class_num]['collections'][5]['Tests'][test_id]
       
   # Delete from MongoDB
   db = db10 if class10 else db9
   result = db['Tests'].delete_one({'test-id': test_id})
   
   return result.deleted_count > 0


def update_exam(exam_id, updated_data, class10=False):
    """Updates an existing exam in both RAM and MongoDB."""
    class_num = 10 if class10 else 9

    # Update in RAM
    if exam_id in data_store[class_num]['collections'][3]['Exams']:
        data_store[class_num]['collections'][3]['Exams'][exam_id].update(updated_data)

    # Update in MongoDB
    db = db10 if class10 else db9
    result = db['Exams'].update_one({'exam-id': exam_id}, {'$set': updated_data})

    if result.modified_count > 0:
        print(f"Exam {exam_id} updated successfully")
        return True
    else:
        print(f"No exam found with id {exam_id}")
        return False

def update_exam_solution(exam_id, question_index, solution, class10=False):
    """
    Updates a specific question's solution in an exam.
    
    Args:
        exam_id: The ID of the exam
        question_index: The index of the question in the results array
        solution: The solution text to add
        class10: Whether this is for class 10
        
    Returns:
        bool: True if the update was successful, False otherwise
    """
    class_num = 10 if class10 else 9
    db = db10 if class10 else db9
    
    # Get the exam first to ensure it exists and has results
    exam = get_exam(exam_id, class10)
    if not exam or 'results' not in exam or question_index >= len(exam['results']):
        print(f"Exam {exam_id} not found or question index {question_index} out of range")
        return False
    
    # Update the solution in the results array
    update_field = f'results.{question_index}.solution'
    result = db['Exams'].update_one(
        {'exam-id': exam_id}, 
        {'$set': {update_field: solution}}
    )
    
    # Also update in RAM if available
    if exam_id in data_store[class_num]['collections'][3]['Exams']:
        if 'results' in data_store[class_num]['collections'][3]['Exams'][exam_id]:
            if question_index < len(data_store[class_num]['collections'][3]['Exams'][exam_id]['results']):
                data_store[class_num]['collections'][3]['Exams'][exam_id]['results'][question_index]['solution'] = solution
    
    if result.modified_count > 0:
        return True
    else:
        print(f"Failed to update solution for question {question_index} in exam {exam_id}")
        return False

def get_user_exams(user_id, class10=False):
    """Retrieves all exams for a given user."""
    class_num = 10 if class10 else 9
    user_exams = []
    for exam in data_store[class_num]['collections'][3]['Exams'].values():
        if exam.get('userId') == user_id:
            user_exams.append(exam)

    if not user_exams:
        # If not found in RAM, check MongoDB
        db = db10 if class10 else db9
        user_exams = list(db['Exams'].find({"userId": user_id}))
        # Add to RAM for future use
        for exam in user_exams:
            exam_id = exam['exam-id']
            data_store[class_num]['collections'][3]['Exams'][exam_id] = exam

    return [convert_mongo_doc(exam) for exam in user_exams]

async def update_mongodb():
    """Asynchronously updates MongoDB with queued changes."""
    while True:
        update = await update_queue.get()
        try:
            if update[0] == 'Stats':
                _, div, user_id, new_stats, class_num = update
                db = db10 if class_num == 10 else db9
                await db[div].update_one(
                    {'Stats': {'$exists': True}},
                    {'$set': {f'Stats.{user_id}': new_stats}},
                    upsert=True
                )
            elif update[0] == 'Subjects':
                _, div, user_id, subject, new_data, class_num = update
                db = db10 if class_num == 10 else db9
                await db[div].update_one(
                    {'Subjects': {'$exists': True}},
                    {'$set': {f'Subjects.{user_id}': new_data}},
                    upsert=True
                )
            elif update[0] == 'ExamHistory':
                _, user_id, overview_stats, class_num = update
                db = db10 if class_num == 10 else db9
                await db['ExamHistory'].update_one(
                    {'_id': 'exam_history'},
                    {'$push': {f'{user_id}.overview-stats': overview_stats}},
                    upsert=True
                )
            elif update[0] == 'Exams':
                _, operation = update[:2]
                if operation == 'insert':
                    exam_data, class_num = update[2:]
                    db = db10 if class_num == 10 else db9
                    await db['Exams'].insert_one(exam_data)
                elif operation == 'update':
                    exam_id, updated_data, class_num = update[2:]
                    db = db10 if class_num == 10 else db9
                    await db['Exams'].update_one(
                        {'exam-id': exam_id},
                        {'$set': updated_data}
                    )
                elif operation == 'delete':
                    exam_id, class_num = update[2:]
                    db = db10 if class_num == 10 else db9
                    await db['Exams'].delete_one({'exam-id': exam_id})
            update_queue.task_done()
        except Exception as e:
            print(f"Error in update_mongodb: {e}")
            update_queue.task_done()  # Ensure the task is marked as done even if an error occurs

def start_update_thread():
    """Starts the asynchronous update thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_mongodb())

def update_user_stats_after_exam(user_id, subject, score, total_questions, exam_data, exam_id, class10=False):
    logger.info(f"Starting update_user_stats_after_exam with params: user_id={user_id}, subject={subject}, score={score}, total_questions={total_questions}")
    class_num = 10 if class10 else 9
    db = db10 if class10 else db9

    try:
        # Get user division
        user = get_user(user_id, class10)
        if not user:
            raise ValueError(f"User {user_id} not found")
        division = user['division']
        
        # Update user stats
        div_stats = data_store[class_num]['collections'][1][f'Div{division}']['Stats']
        user_stats = div_stats.get(user_id, {})
        
        # Update basic stats with type checking
        current_avgpercentage = float(user_stats.get('avgpercentage', 0))
        current_attempted = int(user_stats.get('attempted', 0))
        exam_percentage = float(exam_data['percentage'])
        
        # Update basic stats
        user_stats['attempted'] = current_attempted + 1
        user_stats['correct'] = user_stats.get('correct', 0) + score
        user_stats['questions'] = user_stats.get('questions', 0) + total_questions
        
        # Calculate new average
        if current_attempted == 0:
            user_stats['avgpercentage'] = exam_percentage
        else:
            user_stats['avgpercentage'] = (current_avgpercentage * current_attempted + exam_percentage) / (current_attempted + 1)

        # Get subjects data structure
        div_subjects = data_store[class_num]['collections'][1][f'Div{division}']['Subjects']
        subjects_list = div_subjects.get(user_id, [])

        # Handle both list and dictionary formats
        if isinstance(subjects_list, dict):
            if subjects_list.get('subject') == subject:
                subject_stats = subjects_list
            else:
                subject_stats = None
            subjects_list = [subjects_list]
        else:
            subject_stats = next((s for s in subjects_list if s['subject'] == subject), None)

        if subject_stats is None:
            subject_stats = {
                'subject': subject,
                'attempted': 0,
                'avgPercentage': 0,
                'marksGained': 0,
                'marksAttempted': 0,
                'highestMark': 0
            }
            subjects_list.append(subject_stats)

        # Update subject stats with type checking
        current_subject_attempted = int(subject_stats.get('attempted', 0))
        current_subject_avgPercentage = float(subject_stats.get('avgPercentage', 0))
        
        # Update subject stats
        subject_stats['attempted'] = current_subject_attempted + 1
        subject_stats['marksGained'] = subject_stats.get('marksGained', 0) + score
        subject_stats['marksAttempted'] = subject_stats.get('marksAttempted', 0) + total_questions
        
        # Calculate new subject average
        if current_subject_attempted == 0:
            subject_stats['avgPercentage'] = exam_percentage
        else:
            subject_stats['avgPercentage'] = (current_subject_avgPercentage * current_subject_attempted + exam_percentage) / (current_subject_attempted + 1)
            
        subject_stats['highestMark'] = max(float(subject_stats.get('highestMark', 0)), exam_percentage)

        # Store back in list format
        div_subjects[user_id] = subjects_list

        # Get or create overview stats
        overview_stats = get_overview_stats(user_id, class10)
        if not overview_stats:
            overview_stats = initialize_overview_stats(user_id, class10)

        # Update overview stats for the subject
        percentage = float(exam_data['percentage'])
        if subject not in overview_stats['subjects']:
            overview_stats['subjects'][subject] = {"exams_given": 0, "highest_marks": 0, "average_percentage": 0}
        subject_overview = overview_stats['subjects'][subject]
        
        current_exams_given = int(subject_overview['exams_given'])
        current_average = float(subject_overview['average_percentage'])
        
        subject_overview['exams_given'] = current_exams_given + 1
        subject_overview['highest_marks'] = max(float(subject_overview['highest_marks']), percentage)
        
        # Calculate new overview average
        if current_exams_given == 0:
            subject_overview['average_percentage'] = percentage
        else:
            subject_overview['average_percentage'] = (current_average * current_exams_given + percentage) / (current_exams_given + 1)

        # Create overview stats object
        overview_stats = {
            "exam-id": exam_id,
            "subject": subject,
            "score": score,
            "totalQuestions": total_questions,
            "percentage": exam_data['percentage'],
            "lessons": exam_data.get('lessons', []),
            "date": datetime.now(timezone("Asia/Kolkata")).strftime("%d-%m-%Y"),
            "test": exam_data.get("test", False),
        }
        if overview_stats["test"]:
            overview_stats["test_name"] = exam_data.get("test_name")

        # Update exam history
        exam_history = data_store[class_num]['collections'][2]['ExamHistory']
        if user_id not in exam_history:
            exam_history[user_id] = {"overview-stats": []}
        exam_history[user_id]["overview-stats"].append(overview_stats)

        # Update MongoDB
        try:
            # Update exam history
            db['ExamHistory'].update_one(
                {'_id': 'exam_history'},
                {'$push': {f'{user_id}.overview-stats': overview_stats}},
                upsert=True
            )

            # Update user stats
            db[f'Div{division}'].update_one(
                {'Stats': {'$exists': True}},
                {'$set': {f'Stats.{user_id}': user_stats}},
                upsert=True
            )

            # Update user subjects
            db[f'Div{division}'].update_one(
                {'Subjects': {'$exists': True}},
                {'$set': {f'Subjects.{user_id}': subjects_list}},
                upsert=True
            )

            logger.info(f"Successfully updated stats for user {user_id} in subject {subject}")

        except Exception as e:
            logger.error(f"MongoDB update error: {e}")
            raise

        # Update leaderboard
        lessons = exam_data.get('lessons', [])
        if isinstance(lessons, list):
            num_lessons = len(lessons)
            update_leaderboard(user_id, score, total_questions, subject, num_lessons, class10)

        return user_stats, subject_stats

    except Exception as e:
        logger.error(f"Error in update_user_stats_after_exam: {str(e)}")
        raise

def create_user_data(user_id, password, name, roll_no, div, class10=False, teacher=False):
    """Creates user data and inserts it into appropriate MongoDB collections."""
    class_num = 10 if class10 else 9
    db = db10 if class10 else db9

    # Insert into Users collection
    users_collection = db['Users']
    user_data = {
        "id": user_id,
        "name": name,
        "password": password,
        "rollno": roll_no,
        "division": div,
        "class": class_num,
        "teacher": teacher,
        "coins": 0,
        "tasks": {
            "generated_at": None,
            "tasks_list": []
        }
    }
    users_collection.insert_one(user_data)
    data_store[class_num]['collections'][0]['Users'].append(user_data)

    # Update Division collection (using upsert=True for Stats and Subjects)
    div_data = data_store[class_num]['collections'][1][f'Div{div}']
    div_collection = db[f'Div{div}']

    # Stats
    stats_data = {
        "attempted": 0,
        "correct": 0,
        "avgpercentage": 0,
        "questions": 0
    }
    div_data['Stats'][user_id] = stats_data
    div_collection.update_one(
        {"Stats": {"$exists": True}},
        {"$set": {f"Stats.{user_id}": stats_data}},
        upsert=True)

    # Subjects
    subjects_data = [
        {"subject": subj, "attempted": 0, "avgPercentage": 0,
         "marksGained": 0, "marksAttempted": 0, "highestMark": 0}
        for subj in ["Math", "SS", "English", "Science"]
    ]
    div_data['Subjects'][user_id] = subjects_data
    div_collection.update_one(
        {"Subjects": {"$exists": True}},
        {"$set": {f"Subjects.{user_id}": subjects_data}},
        upsert=True)

    # Initialize ExamHistory for the user
    data_store[class_num]['collections'][2]['ExamHistory'][user_id] = {"overview-stats": []}
    db['ExamHistory'].update_one(
        {'_id': 'exam_history'},
        {'$set': {user_id: {"overview-stats": []}}},
        upsert=True
    )

    # Initialize overview stats
    initialize_overview_stats(user_id, class10)

    # Create Leaderboard collection if it doesn't exist
    if teacher:
        pass
    else:
        if 'Leaderboard' not in db.list_collection_names():
            db.create_collection('Leaderboard')
            data_store[class_num]['collections'][4]['Leaderboard'] = {}
            print("Leaderboard collection created")

    print(f"User data added successfully for user ID: {user_id}")

def calculate_elo_change(score_percentage, num_lessons, subject):
    """Calculates ELO score change based on test performance and subject."""
    # Base ELO change multiplier
    base_multiplier = 32
    
    # Subject weights
    subject_weights = {
        "Mathematics": 1.5,  # Highest weight
        "Science": 1.2,     # Medium weight
        "Social Studies": 1.0  # Lowest weight
    }
    
    # Get subject weight (default to 1.0 if subject not found)
    subject_weight = subject_weights.get(subject, 1.0)
    
    # Calculate lesson multiplier (more lessons = more ELO)
    lesson_multiplier = 1 + (num_lessons * 0.1)  # Each lesson adds 10% more ELO
    
    # Calculate performance multiplier (better score = more ELO)
    performance_multiplier = score_percentage / 100
    
    # Calculate final ELO change
    elo_change = base_multiplier * subject_weight * lesson_multiplier * performance_multiplier
    
    return round(elo_change)

def update_leaderboard(user_id, score, total_questions, subject, num_lessons, class10=False):
    """Updates the leaderboard with new exam data."""
    class_num = 10 if class10 else 9
    current_date = datetime.now(timezone("Asia/Kolkata"))
    month_key = current_date.strftime('%Y-%m')
    leaderboard_id = hashlib.sha256(f"{month_key}-{current_date.timestamp()}".encode()).hexdigest()[:8]

    # Get user details
    user = get_user(user_id, class10)
    if not user:
        return

    # Update RAM
    if month_key not in data_store[class_num]['collections'][4]['Leaderboard']:
        data_store[class_num]['collections'][4]['Leaderboard'][month_key] = {}

    data_store[class_num]['collections'][4]['Leaderboard'][month_key]["version"]=leaderboard_id 

    # Initialize user data if not exists
    if user_id not in data_store[class_num]['collections'][4]['Leaderboard'][month_key]:
        data_store[class_num]['collections'][4]['Leaderboard'][month_key][user_id] = {
            "name": user['name'],
            "total_exams": 0,
            "total_score": 0,
            "total_questions": 0,
            "average_percentage": 0,
            "elo_score": 0  # Initial ELO score starts from 0
        }

    user_data = data_store[class_num]['collections'][4]['Leaderboard'][month_key][user_id]
    
    # Calculate score percentage for this exam
    score_percentage = (score / total_questions) * 100
    
    # Calculate ELO change
    elo_change = calculate_elo_change(score_percentage, num_lessons, subject)
    
    # Update user data
    user_data["total_exams"] += 1
    user_data["total_score"] += score
    user_data["total_questions"] += total_questions
    user_data["average_percentage"] = (user_data["total_score"] / user_data["total_questions"]) * 100
    user_data["elo_score"] += elo_change

    # Update MongoDB
    db = db10 if class10 else db9
    db['Leaderboard'].update_one(
        {'_id': month_key},
        {'$set': {user_id: user_data}},
        upsert=True
    )

def delete_unsubmitted_exams():
    """Deletes all exams with is_submitted=False from both class 9 and 10 databases."""
    try:
        # Delete from Class 9
        result9 = db9['Exams'].delete_many({'is_submitted': False})
        
        # Delete from Class 10
        result10 = db10['Exams'].delete_many({'is_submitted': False})
        
        # Clear from RAM storage
        for class_num in [9, 10]:
            exams = data_store[class_num]['collections'][3]['Exams']
            exam_ids_to_delete = [
                exam_id for exam_id, exam in exams.items() 
                if not exam.get('is_submitted', False)
            ]
            for exam_id in exam_ids_to_delete:
                del exams[exam_id]
        
        total_deleted = result9.deleted_count + result10.deleted_count
        logger.info(f"Deleted {total_deleted} unsubmitted exams ({result9.deleted_count} from Class 9, {result10.deleted_count} from Class 10)")
        
        return total_deleted
        
    except Exception as e:
        logger.error(f"Error deleting unsubmitted exams: {str(e)}")
        raise

update_thread = threading.Thread(target=start_update_thread, daemon=True)
update_thread.start()

# Download initial data
st = time.time()
download_data()
end = (time.time() - st)
print(end)

def get_standard_stats(class10=False):
    class_num = 10 if class10 else 9
    stats = {
        'total_students': 0,
        'mean_score': 0,
        'subjects': {
            'Math': {'total_score': 0, 'count': 0, 'mean': 0},
            'Science': {'total_score': 0, 'count': 0, 'mean': 0},
            'SS': {'total_score': 0, 'count': 0, 'mean': 0}
        }
    }

    users = data_store[class_num]['collections'][0]['Users']
    stats['total_students'] = len(users)

    exams = data_store[class_num]['collections'][3]['Exams']
    total_score = 0
    total_count = 0

    for exam in exams.values():
        if not exam["is_submitted"] or exam['subject'] == 'English':
            continue

        subject = exam['subject']
        score = exam['score']
        total_questions = len(exam['questions'])
        percentage = (score / total_questions) * 100 if total_questions > 0 else 0

        stats['subjects'][subject]['total_score'] += percentage
        stats['subjects'][subject]['count'] += 1
        total_score += percentage
        total_count += 1

    # Calculate mean for each subject
    for subject in stats['subjects']:
        if stats['subjects'][subject]['count'] > 0:
            stats['subjects'][subject]['mean'] = stats['subjects'][subject]['total_score'] / stats['subjects'][subject]['count']
        del stats['subjects'][subject]['total_score']
        del stats['subjects'][subject]['count']

    # Calculate overall mean score
    if total_count > 0:
        stats['mean_score'] = total_score / total_count

    return stats

def get_subject_stats_by_division(class10=False):
    class_num = 10 if class10 else 9

    stats = {
        'A': {'Math': {'total': 0, 'count': 0}, 'Science': {'total': 0, 'count': 0}, 'SS': {'total': 0, 'count': 0}},
        'B': {'Math': {'total': 0, 'count': 0}, 'Science': {'total': 0, 'count': 0}, 'SS': {'total': 0, 'count': 0}},
        'C': {'Math': {'total': 0, 'count': 0}, 'Science': {'total': 0, 'count': 0}, 'SS': {'total': 0, 'count': 0}},
        'D': {'Math': {'total': 0, 'count': 0}, 'Science': {'total': 0, 'count': 0}, 'SS': {'total': 0, 'count': 0}},
        'E': {'Math': {'total': 0, 'count': 0}, 'Science': {'total': 0, 'count': 0}, 'SS': {'total': 0, 'count': 0}}
    }

    exams = data_store[class_num]['collections'][3]['Exams']
    for exam in exams.values():
        if not exam["is_submitted"] or exam['subject'] == 'English':
            continue
        user_id = exam['userId']
        user = get_user(user_id, class10)
        if user:
            division = user['division']
            subject = exam['subject']
            score = exam['score']
            total_questions = len(exam['questions'])
            percentage = (score / total_questions) * 100 if total_questions > 0 else 0

            stats[division][subject]['total'] += percentage
            stats[division][subject]['count'] += 1

    result = {
        'A': {'Math': 0, 'Science': 0, 'SS': 0, 'TotalAvg': 0},
        'B': {'Math': 0, 'Science': 0, 'SS': 0, 'TotalAvg': 0},
        'C': {'Math': 0, 'Science': 0, 'SS': 0, 'TotalAvg': 0},
        'D': {'Math': 0, 'Science': 0, 'SS': 0, 'TotalAvg': 0},
        'E': {'Math': 0, 'Science': 0, 'SS': 0, 'TotalAvg': 0}
    }

    for division in stats:
        total_scores = 0
        total_count = 0
        for subject in stats[division]:
            if stats[division][subject]['count'] > 0:
                result[division][subject] = stats[division][subject]['total'] / stats[division][subject]['count']
                total_scores += stats[division][subject]['total']
                total_count += stats[division][subject]['count']
            else:
                result[division][subject] = 0

        if total_count > 0:
            result[division]['TotalAvg'] = total_scores / total_count
        else:
            result[division]['TotalAvg'] = 0

    return result

def get_student_detailed_stats(user_id, class10=False):
    class_num = 10 if class10 else 9
    user = get_user(user_id, class10)
    if not user:
        return None

    division = user['division']
    user_stats = data_store[class_num]['collections'][1][f'Div{division}']['Stats']
    user_subjects = data_store[class_num]['collections'][1][f'Div{division}']['Subjects'].get(user_id, [])

    return {
        'user_id': user_id,
        'name': user['name'],
        'class': class_num,
        'division': division,
        'overall_stats': user_stats,
        'subject_stats': user_subjects
    }

def get_student_exams(user_id, class10=False):
    exams  = get_user_exam_history(user_id, class10)
    return exams
def get_total_exams():
    total_exams = len(data_store[9]['collections'][3]['Exams']) + len(data_store[10]['collections'][3]['Exams'])
    return total_exams

# Function to get total number of students
def get_total_students():
    total_students = len(data_store[9]['collections'][0]['Users']) + len(data_store[10]['collections'][0]['Users'])
    return total_students

# Function to get average percentage across all exams
def get_average_percentage():
    percentages = []
    i = 0
    for class_num in [9, 10]:
        for exam in data_store[class_num]['collections'][3]['Exams'].values():
            i += 1
            if exam.get('is_submitted', False):
                try:
                    percentages.append(exam['percentage'])
                except:  # noqa: E722
                    pass
    if percentages:
        return statistics.median(percentages)
    return 0

# Function to get average scores across all exams
def get_average_scores():
    scores = []
    for class_num in [9, 10]:
        for exam in data_store[class_num]['collections'][3]['Exams'].values():
            if exam.get('is_submitted', False):
                scores.append(exam['score'])
    if scores:
        return statistics.median(scores)
    return 0
def get_total_exams_by_class(class10=False):
    class_num = 10 if class10 else 9
    total_exams = len(data_store[class_num]['collections'][3]['Exams'])
    return total_exams

def get_total_students_by_class(class10=False):
    class_num = 10 if class10 else 9
    total_students = len(data_store[class_num]['collections'][0]['Users'])
    return total_students
def get_students_by_division(class_num, division):
    students = []
    for student in data_store[class_num]['collections'][0]['Users']:
        if student['division'] == division:
            students.append({
                'name': student['name'],
                'roll': student['rollno'],
                'gr_number': student['id']
            })
    return sorted(students, key=lambda x: x['roll'])

def get_all_students_by_class(class10=False):
    """Retrieves all students for a given class from RAM."""
    class_num = 10 if class10 else 9
    users = data_store[class_num]['collections'][0]['Users']
    
    # Filter out teachers
    students = [user for user in users if not user.get('teacher', False)]
    
    return [
        {
            "id": student["id"],
            "name": student["name"],
            "division": student["division"],
            "roll": student["rollno"],
        }
        for student in students
    ]

def set_user_password(user_id, new_password, class10=False):
    """Sets the password for a user."""
    class_num = 10 if class10 else 9
    db = db10 if class10 else db9

    # Update in RAM
    users = data_store[class_num]['collections'][0]['Users']
    for user in users:
        if user['id'] == user_id:
            user['password'] = new_password
            break

    # Update in MongoDB
    result = db['Users'].update_one({'id': user_id}, {'$set': {'password': new_password}})
    return result.modified_count > 0

# delete_unsubmitted_exams()

def move_expired_tests_to_inactive():
   """
   Moves expired tests from the active Tests collection to the InactiveTests collection.
   """
   logger.info("Checking for expired tests...")
   now = datetime.now(timezone("UTC"))
   total_moved = 0

   for class_num in [9, 10]:
       db = db10 if class_num == 10 else db9
       active_tests_collection = db['Tests']
       inactive_tests_collection = db['InactiveTests']
       
       test_ids = list(data_store[class_num]['collections'][5]['Tests'].keys())
       
       for test_id in test_ids:
           test = data_store[class_num]['collections'][5]['Tests'].get(test_id)
           if test and 'expiration_date' in test and test.get('expiration_date'):
               try:
                   expiration_date = datetime.fromisoformat(test['expiration_date'].replace('Z', '+00:00'))
                   
                   if expiration_date.tzinfo is None:
                       expiration_date = timezone('UTC').localize(expiration_date)

                   if expiration_date < now:
                       logger.info(f"Test {test_id} has expired. Moving to inactive tests.")
                       
                       inactive_tests_collection.insert_one(test)
                       active_tests_collection.delete_one({'test-id': test_id})

                       data_store[class_num]['collections'][6]['InactiveTests'][test_id] = test
                       del data_store[class_num]['collections'][5]['Tests'][test_id]
                       
                       total_moved += 1
               except (ValueError, TypeError) as e:
                   logger.error(f"Could not parse expiration date for test {test_id}: {test['expiration_date']}. Error: {e}")
   
   if total_moved > 0:
       logger.info(f"Successfully moved {total_moved} expired tests to inactive collection.")
   else:
       logger.info("No expired tests found.")
   
   return total_moved

def fix_missing_lowest_marks():
    """Add lowest_marks field for users who don't have it in their overview stats"""
    for class_num in [9, 10]:
        db = db10 if class_num == 10 else db9
        
        # Get all users' overview stats
        overview_stats = db['overview_stats'].find({})
        
        for user_stats in overview_stats:
            user_id = user_stats['user_id']
            subjects = user_stats.get('subjects', {})
            
            updates = {}
            for subject, stats in subjects.items():
                if 'lowest_marks' not in stats:
                    # Get all exam scores for this subject from exam history
                    exam_history = db['ExamHistory'].find_one({'_id': 'exam_history'})
                    if not exam_history or user_id not in exam_history:
                        continue
                        
                    subject_scores = [
                        exam['score'] 
                        for exam in exam_history[user_id]['overview-stats']
                        if exam['subject'] == subject
                    ]
                    
                    if subject_scores:
                        lowest_mark = min(subject_scores)
                        updates[f'subjects.{subject}.lowest_marks'] = lowest_mark
            
            if updates:
                db['overview_stats'].update_one(
                    {'user_id': user_id},
                    {'$set': updates}
                )

def recalculate_subject_stats():
    """Reset and recalculate all subject statistics for all users in both classes."""
    logger.info("Starting subject statistics recalculation")
    
    for class_num in [9, 10]:
        db = db10 if class_num == 10 else db9
        
        # Get all users
        users = data_store[class_num]['collections'][0]['Users']
        
        for user in users:
            user_id = user['id']
            division = user['division']
            
            # Get all exams for this user
            exams = list(db['Exams'].find({"userId": user_id, "is_submitted": True}))
            
            # Initialize subject stats
            subject_stats = {
                "Math": {"subject": "Math", "attempted": 0, "avgPercentage": 0, "marksGained": 0, "marksAttempted": 0, "highestMark": 0, "lowestMark": float('inf')},
                "Science": {"subject": "Science", "attempted": 0, "avgPercentage": 0, "marksGained": 0, "marksAttempted": 0, "highestMark": 0, "lowestMark": float('inf')},
                "SS": {"subject": "SS", "attempted": 0, "avgPercentage": 0, "marksGained": 0, "marksAttempted": 0, "highestMark": 0, "lowestMark": float('inf')},
                "English": {"subject": "English", "attempted": 0, "avgPercentage": 0, "marksGained": 0, "marksAttempted": 0, "highestMark": 0, "lowestMark": float('inf')}
            }
            
            # Calculate stats from exams
            for exam in exams:
                subject = exam['subject']
                if subject not in subject_stats:
                    continue
                
                score = exam['score']
                total_questions = len(exam['questions'])
                percentage = (score / total_questions) * 100 if total_questions > 0 else 0
                
                stats = subject_stats[subject]
                stats['attempted'] += 1
                stats['marksGained'] += score
                stats['marksAttempted'] += total_questions
                stats['highestMark'] = max(stats['highestMark'], percentage)
                stats['lowestMark'] = min(stats['lowestMark'], percentage)
                
                # Recalculate average percentage
                if stats['attempted'] > 0:
                    stats['avgPercentage'] = (stats['marksGained'] / stats['marksAttempted']) * 100
            
            # Convert to list and remove subjects with no attempts
            subject_stats_list = [
                stats for stats in subject_stats.values()
                if stats['attempted'] > 0
            ]
            
            # Set lowestMark to 0 if no attempts
            for stats in subject_stats_list:
                if stats['lowestMark'] == float('inf'):
                    stats['lowestMark'] = 0
            
            # Update in RAM
            data_store[class_num]['collections'][1][f'Div{division}']['Subjects'][user_id] = subject_stats_list
            
            # Update in MongoDB
            db[f'Div{division}'].update_one(
                {'Subjects': {'$exists': True}},
                {'$set': {f'Subjects.{user_id}': subject_stats_list}},
                upsert=True
            )
            
            logger.info(f"Recalculated stats for user {user_id} in class {class_num}")
    
    logger.info("Subject statistics recalculation completed")

def print_database_statistics():
    """
    Prints comprehensive statistics for both Class 9 and Class 10 databases.
    Includes number of students, exams, division-wise distribution, and performance metrics.
    """
    print("\n=== Database Statistics ===\n")
    
    # Overall statistics
    total_students = get_total_students()
    total_exams = get_total_exams()
    avg_percentage = get_average_percentage()
    
    print(f"Total Students (All Classes): {total_students}")
    print(f"Total Exams (All Classes): {total_exams}")
    print(f"Overall Average Percentage: {avg_percentage:.2f}%\n")
    
    # Class-wise statistics
    for class_num, is_class10 in [(9, False), (10, True)]:
        print(f"\n=== Class {class_num} Statistics ===")
        
        # Students and exams count
        students = get_total_students_by_class(is_class10)
        exams = get_total_exams_by_class(is_class10)
        print(f"Total Students: {students}")
        print(f"Total Exams: {exams}")
        
        # Division-wise distribution
        print("\nDivision-wise Student Distribution:")
        for div in ['A', 'B', 'C', 'D', 'E']:
            div_students = get_students_by_division(class_num, div)
            print(f"Division {div}: {len(div_students)} students")
        
        # Get subject statistics by division
        subject_stats = get_subject_stats_by_division(is_class10)
        if subject_stats:
            print("\nSubject-wise Performance:")
            for subject, stats in subject_stats.items():
                avg_score = stats.get('average_score', 0)
                print(f"{subject}: Average Score = {avg_score:.2f}%")

def get_exam_submission_stats():
    """
    Gets statistics about exam submissions from both Class 9 and 10 databases.
    Returns counts of total exams and submitted exams for each class.
    Also shows size of data_store in RAM.
    """
    print("\n=== Exam Submission Statistics ===\n")

    # Get data_store size
    import sys
    data_store_size = sys.getsizeof(data_store)
    print(f"Data Store Size in RAM: {data_store_size / (1024*1024):.2f} MB")

    for class_num, db in [(9, db9), (10, db10)]:
        print(f"\nClass {class_num}:")
        
        try:
            # Get total exams count
            total_exams = db.Exams.count_documents({})
            
            # Get submitted exams count
            submitted_exams = db.Exams.count_documents({"is_submitted": True})
            
            print(f"Total Exams: {total_exams}")
            print(f"Submitted Exams: {submitted_exams}")
            print(f"Submission Rate: {(submitted_exams/total_exams*100):.1f}%" if total_exams > 0 else 0)
            
        except Exception as e:
            print(f"Error getting exam stats for Class {class_num}: {str(e)}")
            continue

def recalculate_current_month_leaderboard(class10=False):
    """Recalculates the current month's leaderboard using the new ELO system."""
    class_num = 10 if class10 else 9
    current_date = datetime.now(timezone("Asia/Kolkata"))
    month_key = current_date.strftime('%Y-%m')

    # Clear current month's leaderboard
    data_store[class_num]['collections'][4]['Leaderboard'][month_key] = {}

    # Get all users
    users = data_store[class_num]['collections'][0]['Users']
    
    # Initialize all users with base ELO
    for user in users:
        user_id = user['id']
        data_store[class_num]['collections'][4]['Leaderboard'][month_key][user_id] = {
            "name": user['name'],
            "total_exams": 0,
            "total_score": 0,
            "total_questions": 0,
            "average_percentage": 0,
            "elo_score": 0  # Initial ELO score starts from 0
        }

    # Get exam history for the current month
    exam_history = data_store[class_num]['collections'][2]['ExamHistory']
    
    # Process each user's exams
    for user_id, history in exam_history.items():
        if 'overview-stats' not in history:
            continue
            
        for exam in history['overview-stats']:
            exam_date = datetime.strptime(exam['date'], '%d-%m-%Y')
            exam_month_key = exam_date.strftime('%Y-%m')
            
            # Only process exams from current month
            if exam_month_key == month_key:
                score = exam['score']
                total_questions = exam['totalQuestions']
                subject = exam['subject']
                num_lessons = len(exam.get('lessons', []))
                
                # Calculate score percentage
                score_percentage = (score / total_questions) * 100
                
                # Calculate ELO change
                elo_change = calculate_elo_change(score_percentage, num_lessons, subject)
                
                # Update user's leaderboard entry
                user_data = data_store[class_num]['collections'][4]['Leaderboard'][month_key][user_id]
                user_data["total_exams"] += 1
                user_data["total_score"] += score
                user_data["total_questions"] += total_questions
                user_data["average_percentage"] = (user_data["total_score"] / user_data["total_questions"]) * 100
                user_data["elo_score"] += elo_change

    # Update MongoDB
    db = db10 if class10 else db9
    db['Leaderboard'].update_one(
        {'_id': month_key},
        {'$set': data_store[class_num]['collections'][4]['Leaderboard'][month_key]},
        upsert=True
    )

get_exam_submission_stats()

__all__ = [
    "data_store",
    "download_data",
    "db9",
    "db10",
    "get_user",
    "get_user_stats",
    "update_user_stats",
    "add_exam",
    "get_exam",
    "update_exam",
    "get_user_exam_history",
    "get_overview_stats",
    "get_user_subjects",
    "update_user_stats_after_exam",
    "set_user_password",
    "print_database_statistics",
    "get_all_students_by_class",
]
