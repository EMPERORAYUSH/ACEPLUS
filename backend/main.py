try:
    import logging
    import copy
    import json
    import os
    import random
    import time
    import hashlib
    import traceback
    from datetime import datetime
    import generate
    from bson.json_util import dumps
    from werkzeug.utils import secure_filename
    from flask import Flask, jsonify, request, send_from_directory, Response
    from flask_cors import CORS
    from flask_jwt_extended import (
        JWTManager,
        create_access_token,
        jwt_required,
    )
    from dotenv import load_dotenv
    from db import (
        add_exam,
        add_test,
        create_user_data,
        download_data,
        get_all_tests,
        get_average_percentage,
        get_average_scores,
        get_exam,
        get_overview_stats,
        get_standard_stats,
        get_student_detailed_stats,
        data_store,
        get_students_by_division,
        get_subject_stats_by_division,
        get_test,
        get_total_exams,
        get_total_exams_by_class,
        get_total_students,
        get_total_students_by_class,
        get_all_students_by_class,
        get_user,
        get_user_exam_history,
        set_user_password,
        get_user_stats,
        get_user_subjects,
        get_all_lessons_for_subject,
        update_user_tasks,
        update_exam,
        update_exam_solution,
        update_test,
        update_user_stats_after_exam,
        db9,
        db10,
        recalculate_current_month_leaderboard,
        move_expired_tests_to_inactive,
    )
    import threading
    from utils.lesson_utils import lesson2filepath
    from utils.data_utils import load_json_file, calculate_lesson_analytics, decode_unicode
    from utils.name_utils import generate_memorable_name
    from utils.auth_utils import get_student_class, get_current_user_info
    from utils.job_utils import allowed_file, cleanup_old_files
    from datetime import timedelta
    from utils.parse_files import render_pdf_previews, render_pptx_previews

except ImportError as e:
    print(f"Import Error: {str(e)}")
    print("Did you run npm run setup?")
    raise

# Load environment variables
load_dotenv()

VERSION = "1.0.1"


# Setup
logging_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.log")
logging.basicConfig(filename=logging_file, level=logging.DEBUG)
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "data")
base_path = os.path.join(data_path, "lessons")

# Configure upload settings from environment variables
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                            os.getenv('UPLOAD_FOLDER', 'uploads'))
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg').split(','))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization", "Cache-Control", "X-Accel-Buffering"],
        "allow_credentials": True
    }
})

# Configure Flask from environment variables
app.config["JWT_SECRET_KEY"] = os.getenv('FLASK_SECRET_KEY', 'boombakabambam')
jwt = JWTManager(app)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # Default 16MB

# Load student information
student_info = json.loads(open(os.path.join(data_path, "students.json")).read())
class10_student_info = json.loads(
    open(os.path.join(data_path, "class10_students.json")).read()
)

UPDATE_LOGS = json.loads(open(os.path.join(data_path, "Update.json")).read())

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = data.get("userId")
    password = data.get("password")

    if not user_id or not password:
        return jsonify({"message": "User ID and password are required"}), 400

    # Check if user is a teacher
    teachers_data = load_json_file("teachers.json")
    if teachers_data and user_id in teachers_data:
        teacher_info = teachers_data[user_id]
        student_data = {
            "name": teacher_info.get("name", "Teacher"),
            "roll": 0,
            "div": teacher_info.get("division", "A"),
            "standard": teacher_info.get(
                "current_standard"
            ),  # Use first standard as default
        }
        is_class10 = teacher_info.get("current_standard") == 10
    else:
        # Regular student login flow
        student_data, is_class10 = get_student_class(user_id, student_info, class10_student_info)
        if student_data is None:
            return jsonify({"message": "Invalid User ID"}), 400

    # Check if user exists in database
    user = get_user(user_id, class10=is_class10)

    if user is None:
        try:
            name = student_data["name"]
            roll = student_data["roll"]
            division = student_data["div"]
            if teachers_data and user_id in teachers_data:
                user = create_user_data(user_id, password, name, roll, division, is_class10, teacher=True)
            else:
                user = create_user_data(user_id, password, name, roll, division, is_class10, teacher=False)

            # Include class10 status in JWT token
            access_token = create_access_token(
                identity={"user_id": user_id, "class10": is_class10},
                expires_delta=False,
            )

            response = {
                "message": "Login successful",
                "token": access_token,
                "user_id": user_id,
                "class10": is_class10,
                "version": VERSION,
            }
            return jsonify(response), 200

        except Exception as e:
            return jsonify({"message": f"Error creating new user: {str(e)}"}), 500

    if user["password"] is None:
        return jsonify({"message": "User not registered. Please register."}), 401

    if user["password"] == password:
        # Include class10 status in JWT token
        access_token = create_access_token(
            identity={"user_id": user_id, "class10": is_class10}, expires_delta=False
        )
        response = {
            "message": "Login successful",
            "token": access_token,
            "user_id": user_id,
            "class10": is_class10,
            "version": VERSION,
        }
        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    user_id = data.get("userId")
    registration_code = data.get("registrationCode")
    new_password = data.get("newPassword")

    if not all([user_id, registration_code, new_password]):
        return jsonify({"message": "User ID, registration code, and new password are required"}), 400

    student_data, is_class10 = get_student_class(user_id, student_info, class10_student_info)
    if student_data is None:
        return jsonify({"message": "Invalid User ID"}), 400

    user = get_user(user_id, class10=is_class10)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    if user.get("password"):
        return jsonify({"message": "User is already registered. Please login."}), 400

    if user.get("registration_code") != registration_code:
        return jsonify({"message": "Invalid registration code"}), 401

    if set_user_password(user_id, new_password, is_class10):
        access_token = create_access_token(
            identity={"user_id": user_id, "class10": is_class10}, expires_delta=False
        )
        response = {
            "message": "Registration successful, logged in",
            "token": access_token,
            "user_id": user_id,
            "class10": is_class10,
            "version": VERSION,
        }
        return jsonify(response), 200
    else:
        return jsonify({"message": "Failed to update password"}), 500


@app.route("/api/lessons", methods=["GET"])
@jwt_required()
def get_lessons():
    current_user, is_class10 = get_current_user_info()

    # Check if user is a teacher
    teachers_data = load_json_file("teachers.json")
    if teachers_data and current_user in teachers_data:
        # For teachers, get class10 from query param
        class10_param = request.args.get("class10")
        if class10_param is not None:
            is_class10 = class10_param.lower() == "true"

    subject = request.args.get("subject")
    if not subject:
        return jsonify({"message": "Subject parameter is required"}), 400

    lessons_file = "lessons10.json" if is_class10 else "lessons.json"
    with open(os.path.join(data_path, lessons_file)) as f:
        lessons = json.load(f)

    if subject not in lessons:
        return jsonify({"message": "Invalid subject"}), 400

    return jsonify(lessons[subject]), 200


@app.route("/api/create_exam", methods=["POST"])
@jwt_required()
def create_exam():
    current_user, is_class10 = get_current_user_info()

    data = request.get_json()
    is_test = data.get("test", False)

    if is_test:
        test_id = data.get("test-id")
        if not test_id:
            return jsonify({"message": "Test ID is required"}), 400
        test_data = get_test(test_id, is_class10)
        if not test_data:
            return jsonify({"message": "Test not found or already completed"}), 404
        exam_id = f"{test_id}-{current_user}"
        subject = test_data["subject"]
        lessons = test_data["lessons"]
        questions = test_data["questions"]

    else:
        # Original exam creation logic
        subject = data.get("subject")
        lessons = data.get("lessons")
        if not subject or not lessons:
            return jsonify({"message": "Subject and lessons are required"}), 400

        lesson_paths = [
            lesson2filepath(subject, lesson, class10=is_class10) for lesson in lessons
        ]
        if not lesson_paths:
            return jsonify({"message": "Invalid lessons provided"}), 400

        exam_id = generate_memorable_name()
        try:
            questions = generate.generate_exam_questions(
                subject, lesson_paths, current_user
            )
        except Exception as e:
            print(f"Error generating questions: {e}")
            return jsonify({"message": f"Error generating questions: {str(e)}"}), 500

    exam_data = {
        "exam-id": exam_id,
        "userId": current_user,
        "subject": subject,
        "lessons": lessons,
        "questions": questions,
        "is_submitted": False,
        "selected_answers": [],
        "class10": is_class10,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test": is_test,
    }
    if is_test:
        exam_data["test_name"] = test_data.get("test_name")

    try:
        added_exam = add_exam(exam_data, is_class10)
        if added_exam:
            return jsonify({"exam-id": exam_id}), 201
        else:
            return jsonify({"message": "Error creating exam"}), 500
    except Exception as e:
        print(f"Error adding exam: {e}")
        return jsonify({"message": f"Error creating exam: {str(e)}"}), 500


@app.route("/api/submit_exam/<exam_id>", methods=["POST"])
@jwt_required()
def submit_exam(exam_id):
    current_user, is_class10 = get_current_user_info()
    data = request.get_json()
    selected_answers = data.get("answers")

    exam = get_exam(exam_id, is_class10)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404

    if exam.get("is_submitted", False):
        return jsonify({"message": "Exam already submitted"}), 400

    if exam["userId"] != current_user:
        return jsonify({"message": "Unauthorized"}), 401

    total_questions = len(exam["questions"])
    score = 0

    # Prepare questions that need solutions
    questions_needing_solutions = []
    initial_results = []

    for i, (question, selected_answer) in enumerate(
        zip(exam["questions"], selected_answers), 1
    ):
        correct_answer = question.get("answer")
        is_correct = selected_answer["option"] == correct_answer
        score += 1 if is_correct else 0

        selected_option_value = question["options"][selected_answer["option"]]
        correct_option_value = question["options"][correct_answer]

        result = {
            "question-no": str(i),
            "question": question["question"],
            "is_correct": is_correct,
            "selected_answer": f"{selected_answer['option']}) {selected_option_value}",
            "correct_answer": f"{correct_answer}) {correct_option_value}",
            "solution": None,
        }

        initial_results.append(result)

        # Collect incorrect questions for solution generation
        if not is_correct:
            questions_needing_solutions.append(
                {
                    "question": question["question"],
                    "correct_answer": correct_option_value,
                    "given_answer": selected_option_value,
                    "options": question["options"],
                    "index": i - 1,
                }
            )

    # We no longer generate solutions during submission
    # Solutions will be generated on demand via the new API endpoint
    
    percentage = (score / total_questions) * 100

    # Calculate lesson-wise analytics
    lesson_analytics = calculate_lesson_analytics(exam["questions"], selected_answers)

    # Generate performance analysis
    try:
        performance_analysis = generate.generate_performance_analysis(
            initial_results, exam["lessons"], is_class10
        )
        perf_analysis = performance_analysis
        print("\n\n", perf_analysis, "\n\n")
    except Exception as e:
        print(f"Error generating performance analysis: {e}")
        perf_analysis = None

    updated_data = {
        "is_submitted": True,
        "selected_answers": selected_answers,
        "score": score,
        "percentage": percentage,
        "results": initial_results,
        "lessons": exam["lessons"],
        "lesson_analytics": lesson_analytics,
        "submission_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test": exam.get("test", False),
        "performance_analysis": perf_analysis,
        "questions_needing_solutions": [q["index"] for q in questions_needing_solutions],
    }
    if updated_data.get("test"):
        updated_data["test_name"] = exam.get("test_name")

    # If it's a test submission
    if exam.get("test", False):
        # Extract the test ID from exam ID (e.g., "TS-Math-101" from "TS-Math-101-user123")
        test_id = "-".join(
            exam_id.split("-")[:-1]
        )  # Get everything before the last segment

        try:
               test_data = get_test(test_id, is_class10)
               if test_data:
                   completed_by = test_data.get("completed_by", [])
                   if current_user not in completed_by:
                       completed_by.append(current_user)
                       update_test(test_id, {"completed_by": completed_by}, is_class10)
        except Exception as e:
            print(f"Error updating active_tests.json: {e}")
            # Continue even if update fails

    # Get user data before updating stats
    user_data = get_user(current_user, is_class10)
    if not user_data:
        return jsonify({"message": "User data not found"}), 404
    if update_exam(exam_id, updated_data, is_class10):
        try:
            user_stats, subject_stats = update_user_stats_after_exam(
                current_user,
                exam["subject"],
                score,
                total_questions,
                updated_data,
                exam_id,
                is_class10,
            )
        except Exception as e:
            print(f"Error updating user stats: {e}")
            # Continue even if stats update fails

        # Check for task completion
        completed_tasks = check_and_update_tasks(current_user, is_class10, exam)

        # Award 10 coins for test completion
        if exam.get("test", False):
            # Fetch user again to get latest coin count
            user_data = get_user(current_user, is_class10)
            if user_data:
                new_coins = user_data.get("coins", 0) + 10
                update_user_tasks(current_user, user_data.get("tasks", {}), is_class10, coins=new_coins)
                
                # Append a virtual task to show the popup on the frontend
                completed_tasks.append({
                    "title": "Test Completion Bonus",
                    "reward": 10
                })
        return jsonify(
            {
                "message": "Exam submitted successfully",
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "results": initial_results,
                "questions_needing_solutions": [q["index"] for q in questions_needing_solutions],
                "completed_tasks": completed_tasks
            }
        ), 200
    else:
        return jsonify({"message": "Failed to submit exam"}), 500


def check_and_update_tasks(user_id, is_class10, exam_data):
    user = get_user(user_id, is_class10)
    if not user or "tasks" not in user or "tasks_list" not in user["tasks"]:
        return []

    tasks = user["tasks"]["tasks_list"]
    completed_tasks = []
    coins_earned = 0
    exam_subject = exam_data["subject"]
    exam_lessons = exam_data["lessons"]
    
    for task in tasks:
        if task["completed"]:
            continue

        task_id = task["id"]
        task_action = task["action"]
        
        # Check if the task is completed
        if task_id == 1 and task_action["type"] == "exam":
            task["num_completed"] = task.get("num_completed", 0) + 1
            if task["num_completed"] >= task["details"]["count"]:
                task["completed"] = True
        
        elif task_id == 2 and task_action["type"] == "exam" and task_action["subject"] == exam_subject:
            task["completed"] = True
            
        elif task_id == 3 and task_action["type"] == "exam" and task_action["subject"] == exam_subject and set(task_action["lessons"]) == set(exam_lessons):
            task["completed"] = True

        elif task_id == 4:
            if task_action["type"] == "test" and exam_data["test"]:
                test_id = "-".join(exam_data["exam-id"].split("-")[:-1])
                if task_action["test-id"] == test_id:
                    task["completed"] = True
            elif task_action["type"] == "exam" and task_action["subject"] == exam_subject and set(task_action["lessons"]) == set(exam_lessons):
                task["completed"] = True

        elif task_id == 5 and task_action["type"] == "exam" and task_action["subject"] == exam_subject and set(task_action["lessons"]) == set(exam_lessons):
            task["completed"] = True
        
        if task["completed"]:
            completed_tasks.append(task)
            coins_earned += task["reward"]

    if coins_earned > 0:
        user["coins"] = user.get("coins", 0) + coins_earned
        update_user_tasks(user_id, user["tasks"], is_class10, coins=user.get("coins"))

    return completed_tasks


@app.route("/api/generate_hint", methods=["POST"])
@jwt_required()
def generate_hint_route():
    """Generate a hint for a given question without revealing the answer."""
    data = request.get_json()
    question_text = data.get("question")

    if not question_text:
        return jsonify({"message": "Question text is required"}), 400

    try:
        # Return a streaming response
        return Response(
            generate.generate_hint(question_text),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache'} # Ensure no caching
        )
    except Exception as e:
        print(f"Error generating hint: {e}")
        return jsonify({"message": f"Error generating hint: {str(e)}"}), 500

@app.route("/api/generate_solution", methods=["POST"])
@jwt_required()
def generate_solution_route():
    """Generate a solution for a specific question in an exam and update the database."""
    current_user, is_class10 = get_current_user_info()
    data = request.get_json()
    
    exam_id = data.get("examId")
    question_index = data.get("questionIndex")
    
    if not all([exam_id, question_index is not None]):
        return jsonify({"message": "Exam ID and question index are required"}), 400
    
    # Convert question_index to integer if it's a string
    if isinstance(question_index, str):
        try:
            question_index = int(question_index)
        except ValueError:
            return jsonify({"message": "Question index must be a valid integer"}), 400
    
    # Get the exam data
    exam = get_exam(exam_id, is_class10)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404
    
    # Check if user is authorized to access this exam
    if exam["userId"] != current_user:
        return jsonify({"message": "Unauthorized access to exam"}), 401
    
    # Check if the exam has results
    if not exam.get("results") or question_index >= len(exam["results"]):
        return jsonify({"message": "Invalid question index or exam has no results"}), 400
    
    # Get the question data
    result = exam["results"][question_index]
    question_text = result["question"]
    
    # Extract correct and selected answers (removing the option prefix like "a) ")
    correct_answer = result["correct_answer"]
    selected_answer = result["selected_answer"]
    
    # Extract just the answer text by removing the option prefix
    correct_answer_text = correct_answer.split(") ", 1)[1] if ") " in correct_answer else correct_answer
    selected_answer_text = selected_answer.split(") ", 1)[1] if ") " in selected_answer else selected_answer
    
    # Get the original question to access its options
    original_question = None
    for i, q in enumerate(exam["questions"]):
        if q["question"] == question_text:
            original_question = q
            break
    
    if not original_question:
        return jsonify({"message": "Question not found in exam"}), 404
    
    # Get the options
    options = original_question["options"]
    
    try:
        # Return a streaming response
        def generate_and_save():
            # Collect the full solution
            full_solution = ""
            
            # Stream the solution
            for chunk in generate.generate_solution_stream(
                question_text, 
                correct_answer_text, 
                selected_answer_text, 
                options
            ):
                # Append to the full solution
                full_solution += chunk
                # Yield the chunk for streaming
                yield chunk
            
            # After streaming is complete, save the solution to the database
            try:
                update_exam_solution(exam_id, question_index, full_solution, is_class10)
            except Exception as e:
                print(f"Error saving solution to database: {e}")
                # We don't want to interrupt the stream, so just log the error
        
        return Response(
            generate_and_save(),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache'} # Ensure no caching
        )
    except Exception as e:
        print(f"Error generating solution: {e}")
        return jsonify({"message": f"Error generating solution: {str(e)}"}), 500

@app.route("/api/exam/<exam_id>", methods=["GET"])
@jwt_required()
def get_exam_route(exam_id):
    _, is_class10 = get_current_user_info()
    exam_data = get_exam(exam_id, is_class10)

    if exam_data:
        # Create a copy of the exam data for the response
        response_data = copy.deepcopy(exam_data)
        if not response_data.get("is_submitted", False):
            # Remove answers only for the response, not for the stored data
            for question in response_data["questions"]:
                question.pop("answer", None)

        # Decode Unicode for the response data
        response_data = decode_unicode(response_data)
        return jsonify(response_data), 200
    else:
        return jsonify({"message": "Exam not found"}), 404


@app.route("/api/user_exams", methods=["GET"])
@jwt_required()
def get_user_exams_route():
    current_user, is_class10 = get_current_user_info()
    user_exams = get_user_exam_history(current_user, is_class10)
    return jsonify(user_exams), 200


@app.route("/api/report", methods=["POST"])
@jwt_required()
def report_question():
    current_user, is_class10 = get_current_user_info()
    data = request.get_json()

    exam_id = data.get("examId")
    question_index = data.get("questionIndex")
    reason = data.get("reason")
    description = data.get("description")

    if not all([exam_id, question_index, description]):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Get the exam data
        exam = get_exam(exam_id, is_class10)
        if not exam:
            return jsonify({"message": "Exam not found"}), 404

        # Get the question data
        if question_index >= len(exam["questions"]):
            return jsonify({"message": "Invalid question index"}), 400

        question_data = exam["questions"][question_index]

        # Updated path to use data folder
        reports_file = os.path.join(data_path, "reports", "question_reports.json")
        os.makedirs(os.path.dirname(reports_file), exist_ok=True)

        try:
            with open(reports_file, "r") as f:
                reports = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reports = []

        # Check if question already reported
        for report in reports:
            if (
                report["exam_id"] == exam_id
                and report["question_index"] == question_index
                and report["user_id"] == current_user
            ):
                return jsonify({"message": "Report submitted successfully"}), 200

        # Create new report
        report = {
            "user_id": current_user,
            "class10": is_class10,
            "exam_id": exam_id,
            "question_index": question_index,
            "question_data": question_data,
            "reason": reason,
            "description": description,
            "subject": exam["subject"],
            "lessons": exam["lessons"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        reports.append(report)

        with open(reports_file, "w") as f:
            json.dump(reports, f, indent=2)

        return jsonify({"message": "Report submitted successfully"}), 200

    except Exception as e:
        return jsonify({"message": f"Error submitting report: {str(e)}"}), 500


def get_available_tests_for_user(user_id, is_class10):
    """Helper function to get all available tests for a specific user."""
    all_tests = get_all_tests(is_class10)
    user = get_user(user_id, is_class10)
    
    available_tests = []
    for test in all_tests:
        if user_id in test.get("completed_by", []):
            continue

        assigned_students = test.get("students")
        assigned_division = test.get("division")
        test_standard = test.get("standard")

        # Check if test is for the student's class
        if (test_standard == 10) != is_class10:
            continue

        # Check for assignment
        if assigned_students and user_id in assigned_students:
            available_tests.append(test)
        elif assigned_division and user and user.get("division") == assigned_division:
            available_tests.append(test)
        elif not assigned_students and not assigned_division:
            available_tests.append(test)
            
    return available_tests


@app.route("/api/tests", methods=["GET"])
@jwt_required()
def get_tests():
    current_user, is_class10 = get_current_user_info()
    teachers_data = load_json_file("teachers.json")
    is_teacher = current_user in teachers_data if teachers_data else False
    print(is_teacher)
    if is_teacher:
        all_tests = get_all_tests(is_class10)
        available_tests = [
            test for test in all_tests if test.get("created_by") == current_user
        ]
    else:
        available_tests = get_available_tests_for_user(current_user, is_class10)

    # Filter out completed tests for students more efficiently
    if not is_teacher:
        available_tests = [
            test for test in available_tests
            if current_user not in test.get("completed_by", [])
        ]

    if not available_tests and not is_teacher:
        return jsonify({"message": "No tests available"}), 404

    # Format the response
    formatted_tests = []
    for test in available_tests:
        test_info = {
            "subject": test.get("subject"),
            "test-id": test.get("test-id"),
            "lessons": test.get("lessons", []),
            "questions": len(test.get("questions", [])),
            "test_name": test.get("test_name"),
        }
        formatted_tests.append(test_info)

    response = {"tests": formatted_tests, "teacher": is_teacher}

    # Add teacher-specific information
    if is_teacher:
        teacher_info = teachers_data.get(current_user, {})
        teacher_standards = teacher_info.get("standard", [])

        response_data = {
            "teacher_subject": teacher_info.get("subject"),
            "teacher_standard": teacher_standards,
        }

        if not (9 in teacher_standards and 10 in teacher_standards):
            lessons_file = "lessons10.json" if is_class10 else "lessons.json"
            lessons_data = load_json_file(lessons_file)
            response_data["subject_lessons"] = (
                lessons_data.get(teacher_info.get("subject"), [])
                if lessons_data
                else []
            )

        response.update(response_data)

    return jsonify(response), 200


@app.route("/api/generate_test", methods=["POST"])
@jwt_required()
def generate_test():
    current_user, _ = get_current_user_info()
    # Verify teacher access
    teachers_data = load_json_file("teachers.json")
    if not teachers_data or current_user not in teachers_data:
        return jsonify({"message": "Unauthorized access"}), 401

    data = request.get_json()
    subject = data.get("subject")
    lessons = data.get("lessons")
    class10 = data.get("class10", False)

    if not subject:
        return jsonify({"message": "Subject is required"}), 400

    questions = []
    if lessons:
        lesson_paths = [
            lesson2filepath(subject, lesson, class10=class10) for lesson in lessons
        ]
        
        if None in lesson_paths:
             # This case handles custom subjects where lessons won't be found
             pass
        else:
            try:
                questions = generate.generate_exam_questions(subject, lesson_paths, current_user)
            except Exception as e:
                print(f"Error generating questions: {e}")
                return jsonify({"message": f"Error generating questions: {str(e)}"}), 500
    
    # Format questions without solutions
    formatted_questions = []
    for q in questions:
        formatted_questions.append(
            {
                "question": q["question"],
                "options": q["options"],
                "answer": q["answer"],
            }
        )

    return jsonify(
        {
            "subject": subject,
            "lessons": lessons,
            "questions": formatted_questions,
            "class10": class10,
        }
    ), 200


@app.route("/api/create_test", methods=["POST"])
@jwt_required()
def create_test():
   current_user, _ = get_current_user_info()

   # Verify teacher access
   teachers_data = load_json_file("teachers.json")
   if not teachers_data or current_user not in teachers_data:
       return jsonify({"message": "Unauthorized access"}), 401

   data = request.get_json()
   subject = data.get("subject")
   lessons = data.get("lessons")
   questions = data.get("questions")
   class10 = data.get("class10", False)
   students = data.get("students")  # List of student IDs
   division = data.get("division")  # Specific division
   expiration_date = data.get("expiration_date")
   test_name = data.get("test_name")
 
   if not all([subject, questions, expiration_date]):
        return jsonify({"message": "Subject, questions, and expiration date are required"}), 400

   # Validate question format
   for q in questions:
       if not all(key in q for key in ["question", "options", "answer"]):
           return jsonify({"message": "Invalid question format"}), 400
       if not all(key in q["options"] for key in ["a", "b", "c", "d"]):
           return jsonify({"message": "Invalid options format"}), 400

   random.shuffle(questions)
   test_id = f"TS-{subject}-{str(random.randint(100,999))}"

   test_data = {
       "test-id": test_id,
       "subject": subject,
       "standard": 10 if class10 else 9,
       "lessons": lessons,
       "questions": questions,
       "created_by": current_user,
       "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
       "completed_by": [],
       "expiration_date": expiration_date,
       "test_name": test_name,
   }

   if students:
       test_data["students"] = students
   if division:
       test_data["division"] = division

   try:
       add_test(test_data, class10)
       return jsonify({"test-id": test_id}), 201
   except Exception as e:
       print(f"Error creating test: {e}")
       return jsonify({"message": f"Error creating test: {str(e)}"}), 500


@app.route("/api/user_stats", methods=["GET"])
@jwt_required()
def get_user_stats_route():
    current_user, is_class10 = get_current_user_info()
    stats = get_user_stats(current_user, is_class10)

    if not stats:
        response = {
            "version": VERSION,
            "stats": [
                {"total_exams": 0},
                {"total_marks": 0},
                {"marks_gained": 0},
                {"average_percentage": "0.00%"},
            ],
        }
        return jsonify(response), 200

    formatted_stats = [
        {"total_exams": stats.get("attempted", 0)},
        {"total_marks": stats.get("questions", 0)},
        {"marks_gained": stats.get("correct", 0)},
        {"average_percentage": f"{stats.get('avgpercentage', 0):2.2f}%"},
    ]

    response = {"version": VERSION, "stats": formatted_stats}
    return jsonify(response), 200


@app.route("/api/overview_stats", methods=["GET"])
@jwt_required()
def get_overview_stats_route():
    current_user, is_class10 = get_current_user_info()
    stats = get_overview_stats(current_user, is_class10)
    if not stats:
        return jsonify(
            {
                "total_exams": 0,
                "total_questions": 0,
                "correct_answers": 0,
                "average_score": 0,
                "subject_stats": {},
                "recent_exams": [],
            }
        ), 200

    return jsonify(stats), 200


@app.route("/api/subject_stats/<subject>", methods=["GET"])
@jwt_required()
def get_subject_stats_route(subject):
    current_user, is_class10 = get_current_user_info()
    stats = get_user_subjects(current_user, subject, is_class10)
    print("\n\nStats:", stats, "\n\n")
    if not stats:
        return jsonify(
            {
                "total_exams": 0,
                "total_questions": 0,
                "correct_answers": 0,
                "average_score": 0,
                "lesson_stats": {},
                "recent_exams": [],
            }
        ), 200

    return jsonify(stats), 200


@app.route("/api/student_stats", methods=["GET"])
@jwt_required()
def get_student_stats():
    current_user, is_class10 = get_current_user_info()

    try:
        stats = get_student_detailed_stats(current_user, is_class10)
        if not stats:
            return jsonify({"message": "No stats found for student"}), 404

        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching student stats: {str(e)}"}), 500


@app.route("/api/division_stats", methods=["GET"])
@jwt_required()
def get_division_stats():
    current_user, is_class10 = get_current_user_info()

    try:
        # Get student info to determine division
        student_data = (
            class10_student_info.get(current_user)
            if is_class10
            else student_info.get(current_user)
        )
        if not student_data:
            return jsonify({"message": "Student not found"}), 404

        division = student_data.get("div")
        if not division:
            return jsonify({"message": "Division not found"}), 404

        # Get division statistics
        students = get_students_by_division(division, is_class10)
        subject_stats = get_subject_stats_by_division(division, is_class10)

        stats = {
            "division": division,
            "total_students": len(students),
            "subject_stats": subject_stats,
            "class": "10" if is_class10 else "9",
        }

        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching division stats: {str(e)}"}), 500


@app.route("/api/standard_stats", methods=["GET"])
@jwt_required()
def get_class_stats():
    _, is_class10 = get_current_user_info()

    try:
        stats = get_standard_stats(is_class10)
        if not stats:
            return jsonify(
                {
                    "total_students": 0,
                    "total_exams": 0,
                    "average_score": 0,
                    "subject_wise_stats": {},
                    "division_wise_stats": {},
                }
            ), 200

        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching standard stats: {str(e)}"}), 500


@app.route("/api/students_by_standard", methods=["GET"])
@jwt_required()
def get_students_by_standard_route():
    _, is_class10 = get_current_user_info()
    
    # Allow teachers to specify the class
    class10_param = request.args.get("class10")
    if class10_param is not None:
        is_class10 = class10_param.lower() == "true"
        
    try:
        students = get_all_students_by_class(is_class10)
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching students: {str(e)}"}), 500

@app.route("/api/upload_files", methods=["POST"])
@jwt_required()
def upload_files():
    current_user, _ = get_current_user_info()

    # Collect any files (compatible with both 'file_*' and 'image_*' keys)
    files = [request.files[key] for key in request.files]

    if not files:
        return jsonify({'message': 'No files provided'}), 400

    # Enforce per-user daily upload limit (max 5 files in last 24 hours)
    now_ts = time.time()
    twenty_four_hours = 24 * 60 * 60

    def count_user_uploads_last_24h(user_id: str) -> int:
        count = 0
        try:
            for fname in os.listdir(app.config['UPLOAD_FOLDER']):
                if not fname.startswith(f"{user_id}_"):
                    continue
                fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                try:
                    ctime = os.path.getctime(fpath)
                except Exception:
                    continue
                if now_ts - ctime <= twenty_four_hours:
                    count += 1
        except Exception:
            pass
        return count

    existing_count = count_user_uploads_last_24h(current_user)
    if existing_count + len(files) > 10:
        return jsonify({'message': 'Daily upload limit reached (max 5 files in the last 24 hours).'}), 429

    # Allow images + pdf + pptx
    allowed_file_exts = set(ALLOWED_EXTENSIONS) | {'pdf', 'pptx'}

    uploaded_items = []
    for file in files:
        if not file or not file.filename:
            continue
        if not allowed_file(file.filename, allowed_file_exts):
            continue
        filename = secure_filename(file.filename)
        timestamp = int(now_ts)
        unique_filename = f"{current_user}_{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        try:
            file.save(filepath)
            # Determine type and generate previews
            ext = os.path.splitext(unique_filename)[1].lower()
            ftype = 'image' if ext in ('.png', '.jpg', '.jpeg', '.webp', '.bmp') else ('pdf' if ext == '.pdf' else ('pptx' if ext == '.pptx' else 'file'))
            previews = []
            if ftype == 'image':
                # the image itself is a preview
                previews = [unique_filename]
            elif ftype == 'pdf':
                previews = render_pdf_previews(filepath, app.config['UPLOAD_FOLDER'], pages=1)
            elif ftype == 'pptx':
                previews = render_pptx_previews(filepath, app.config['UPLOAD_FOLDER'], slides=1)

            uploaded_items.append({
                'filename': unique_filename,
                'type': ftype,
                'previews': previews
            })
        except Exception as e:
            print(f"Error saving file {filename}: {e}")
            continue

    if not uploaded_items:
        return jsonify({'message': 'No valid files uploaded'}), 400

    return jsonify({
        'message': 'Files uploaded successfully',
        'items': uploaded_items
    }), 200

@app.route("/api/generate_from_files", methods=["GET"])
@jwt_required()
def generate_from_files():
    """Generate questions from uploaded files using Server-Sent Events."""
    current_user, _ = get_current_user_info()
    
    # Get filenames from query parameters
    filenames = request.args.getlist('filenames')
    
    if not filenames:
        return jsonify({'message': 'No files provided'}), 400
        
    try:
        # Get full paths of the files
        file_paths = [os.path.join(app.config['UPLOAD_FOLDER'], filename) for filename in filenames]
        
        # Check if all files exist
        missing_files = []
        for path in file_paths:
            if not os.path.exists(path):
                missing_files.append(os.path.basename(path))
        
        if missing_files:
            return jsonify({
                'message': f'Some files were not found: {", ".join(missing_files)}'
            }), 404
            
        def generate_sse():
            """Generator function for SSE"""
            try:
                # Send initial message
                yield "event: start\ndata: {\"message\": \"Starting file processing\"}\n\n"
                
                questions = []
                total_count = 0
                
                try:
                    for update in generate.analyze_files(file_paths):
                        if update["type"] == "total":
                            total_count = update["count"]
                            yield f"event: total\ndata: {json.dumps({'count': update['count']})}\n\n"
                        elif update["type"] == "progress":
                            yield f"event: progress\ndata: {json.dumps({'count': update['count'], 'total': total_count})}\n\n"
                        elif update["type"] == "result":
                            questions = update["questions"]
                            yield f"event: result\ndata: {json.dumps({'questions': questions})}\n\n"
                        elif update["type"] == "error":
                            yield f"event: error\ndata: {json.dumps({'message': update['message']})}\n\n"
                            return
                    
                    # Verify we have questions
                    if not questions:
                        yield f"event: error\ndata: {json.dumps({'message': 'No questions could be extracted from the files'})}\n\n"
                        return
                    
                    # Send completion event
                    yield f"event: complete\ndata: {json.dumps({'message': 'Processing complete'})}\n\n"
                    
                except Exception as e:
                    print(f"Error processing files: {str(e)}")
                    print(traceback.format_exc())
                    yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
                    
            except Exception as e:
                print(f"Error in SSE stream: {str(e)}")
                print(traceback.format_exc())
                yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"
        
        response = Response(
            generate_sse(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Content-Type': 'text/event-stream',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no',  # For NGINX compatibility
                'Access-Control-Allow-Origin': request.headers.get('Origin', '*'),
                'Access-Control-Allow-Credentials': 'true'
            }
        )
        return response
            
    except Exception as e:
        print(f"Error in generate_from_files: {str(e)}")
        return jsonify({
            'message': f'Error processing files: {str(e)}'
        }), 500

@app.route("/api/uploads/<filename>")
@jwt_required()
def uploaded_file(filename):
    current_user, _ = get_current_user_info()
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/api/download_data", methods=["GET"])
@jwt_required()
def download_data_route():
    current_user, is_class10 = get_current_user_info()

    try:
        data = download_data(current_user, is_class10)
        if not data:
            return jsonify({"message": "No data found"}), 404

        return jsonify(json.loads(dumps(data))), 200
    except Exception as e:
        return jsonify({"message": f"Error downloading data: {str(e)}"}), 500


@app.route("/api/analytics", methods=["GET"])
@jwt_required()
def get_analytics():
    current_user, is_class10 = get_current_user_info()

    try:
        total_students = get_total_students(is_class10)
        total_exams = get_total_exams(is_class10)
        students_by_class = get_total_students_by_class(is_class10)
        exams_by_class = get_total_exams_by_class(is_class10)
        avg_scores = get_average_scores(is_class10)
        avg_percentage = get_average_percentage(is_class10)

        analytics = {
            "total_students": total_students,
            "total_exams": total_exams,
            "students_by_class": students_by_class,
            "exams_by_class": exams_by_class,
            "average_scores": avg_scores,
            "average_percentage": avg_percentage,
            "class": "10" if is_class10 else "9",
        }

        return jsonify(analytics), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching analytics: {str(e)}"}), 500


@app.route("/api/updates", methods=["GET"])
def get_updates():
    updates = UPDATE_LOGS
    if updates:
        return jsonify(updates[0]), 200
    else:
        return jsonify({"message": "No updates found"}), 200


@app.route("/api/fetch_coins", methods=["GET"])
@jwt_required()
def fetch_coins():
    current_user, is_class10 = get_current_user_info()
    user = get_user(current_user, is_class10)

    if not user:
        return jsonify({"message": "User not found"}), 404

    tasks = user.get("tasks", {})
    now = datetime.now()

    if tasks.get("generated_at"):
        generated_at = datetime.fromisoformat(tasks["generated_at"])
        if (now - generated_at) < timedelta(hours=24) and tasks.get("tasks_list"):
            print("USiNG CACHE")
            return jsonify({
                "coins": user.get("coins", 0),
                "tasks": tasks.get("tasks_list", [])
            })            

    new_tasks = []
    
    # Task 1: Complete 2 exams
    new_tasks.append({
        "id": 1,
        "title": "Boost Your Brain",
        "details": {"text": "Complete {count} exams today to sharpen your knowledge.", "count": 2},
        "completed": False,
        "reward": 5,
        "cta": "Start Exam",
        "action": {"type": "exam"},
        "num_completed": 0
    })

    user_subjects_stats = get_user_subjects(current_user, class10=is_class10)
    user_exam_history = get_user_exam_history(current_user, is_class10)
    total_exams_attempted = len(user_exam_history)

    # Task 2: Give 1 exam of {subject}
    subject_for_task2 = "Math" # Default
    task2_subject_stats = [s for s in user_subjects_stats if s.get('subject') != 'English']

    if not task2_subject_stats:
        # Fallback if only English was in stats, or no stats at all.
        subject_for_task2 = random.choice(["Math", "Science", "SS"])
    elif total_exams_attempted < 5:
        unattempted_subjects = [s['subject'] for s in task2_subject_stats if s['attempted'] == 0]
        if unattempted_subjects:
            subject_for_task2 = random.choice(unattempted_subjects)
        else:
            # If all non-English subjects attempted, pick any non-English one.
            subject_for_task2 = random.choice([s['subject'] for s in task2_subject_stats])
    else:
        # For users with more exams, find the least tested non-English subject.
        sorted_subjects = sorted(task2_subject_stats, key=lambda x: x.get('attempted', 0))
        least_tested_subjects = [s for s in sorted_subjects if s.get('attempted', 0) == sorted_subjects[0].get('attempted', 0)]
        subject_for_task2 = random.choice(least_tested_subjects)['subject']
    
    new_tasks.append({
        "id": 2,
        "title": f"Focus on {subject_for_task2}",
        "details": {"text": "Take one exam in {subject} to improve your skills.", "subject": subject_for_task2},
        "completed": False,
        "reward": 5,
        "cta": f"Test {subject_for_task2}",
        "action": {"type": "exam", "subject": subject_for_task2}
    })

    # Task 3: Give 1 exam of {lesson} {subject}
    unattempted_subjects = [s['subject'] for s in user_subjects_stats if s['attempted'] == 0]
    if total_exams_attempted == 0:
        available_subjects = [s for s in ["Math", "Science", "SS"] if s != subject_for_task2]
        random_subject = random.choice(available_subjects)
        first_lesson = get_all_lessons_for_subject(random_subject, is_class10)[0]
        new_tasks.append({"id": 3, "title": "New Horizons", "details": {"text": "Give 1 exam of {lesson} from {subject}", "lesson": first_lesson, "subject": random_subject}, "completed": False, "reward": 10, "action": {"type": "exam", "subject": random_subject, "lessons": [first_lesson]}})
    elif len(unattempted_subjects) >= 2:
        available_subjects = [s for s in ["Math", "Science", "SS"] if s != subject_for_task2]
        subject_for_task3 = random.choice(available_subjects)
        first_lesson_for_task3 = get_all_lessons_for_subject(subject_for_task3, is_class10)[0]
        new_tasks.append({"id": 3, "title": "Explore New Topics", "details": {"text": "Give 1 exam of {lesson} from {subject}", "lesson": first_lesson_for_task3, "subject": subject_for_task3}, "completed": False, "reward": 10, "action": {"type": "exam", "subject": subject_for_task3, "lessons": [first_lesson_for_task3]}})
    else:
        sorted_subjects = sorted(user_subjects_stats, key=lambda x: x.get('attempted', 0))
        least_tested_subject_info = sorted_subjects[0]
        if least_tested_subject_info['subject'] == subject_for_task2 and len(sorted_subjects) > 1:
            least_tested_subject_info = sorted_subjects[1]
        least_tested_subject = least_tested_subject_info['subject']
        subject_exam_history = [e for e in user_exam_history if e['subject'] == least_tested_subject]
        all_lessons = get_all_lessons_for_subject(least_tested_subject, is_class10)
        lesson_counts = {lesson: 0 for lesson in all_lessons}
        for exam in subject_exam_history:
            for lesson in exam.get('lessons', []):
                if lesson in lesson_counts:
                    lesson_counts[lesson] += 1
        
        min_attempts = min(lesson_counts.values()) if lesson_counts else 0
        least_tested_lessons = [lesson for lesson, count in lesson_counts.items() if count == min_attempts]
        lesson_for_task3 = random.choice(least_tested_lessons) if least_tested_lessons else all_lessons[0] if all_lessons else "a lesson"
        new_tasks.append({"id": 3, "title": "Deepen Your Knowledge", "details": {"text": "Give 1 exam of {lesson} from {subject}", "lesson": lesson_for_task3, "subject": least_tested_subject}, "completed": False, "reward": 10, "action": {"type": "exam", "subject": least_tested_subject, "lessons": [lesson_for_task3]}})

    # Task 4: Pending tests or 2nd least attempted subject
    pending_tests = get_available_tests_for_user(current_user, is_class10)
    if pending_tests:
        test_to_complete = random.choice(pending_tests)
        test_name = test_to_complete.get('test_name')

        if test_name:
            task_text = "Complete the test: {test_name}"
        else:
            task_text = "Complete the test: {subject} - {lessons}"

        task_details = {
            "text": task_text,
            "test_name": test_name,
            "subject": test_to_complete.get('subject'),
            "lessons": test_to_complete.get('lessons', [])
        }
        new_tasks.append({"id": 4, "title": "Complete Your Test", "details": task_details, "completed": False, "reward": 10, "action": {"type": "test", "test-id": test_to_complete.get('test-id')}})
    elif len(user_subjects_stats) > 1:
        second_least_attempted_subject_info = sorted(user_subjects_stats, key=lambda x: x.get('attempted', 0))[1]
        second_least_attempted_subject = second_least_attempted_subject_info['subject']
        all_lessons_second = get_all_lessons_for_subject(second_least_attempted_subject, is_class10)
        if all_lessons_second:
            lesson_to_add = [all_lessons_second[0]]
            new_tasks.append({"id": 4, "title": "Branch Out", "details": {"text": "Give exam of {lessons} from {subject}", "lessons": lesson_to_add, "subject": second_least_attempted_subject}, "completed": False, "reward": 10, "action": {"type": "exam", "subject": second_least_attempted_subject, "lessons": lesson_to_add}})

    # Task 5: Least attempted lesson of most attempted subject
    if user_subjects_stats:
        if total_exams_attempted == 0:
            random_subject_for_task5 = random.choice([s['subject'] for s in user_subjects_stats])
            all_lessons_task5 = get_all_lessons_for_subject(random_subject_for_task5, is_class10)
            lesson_for_task5 = all_lessons_task5[0] if all_lessons_task5 else None
            if lesson_for_task5:
                 new_tasks.append({"id": 5, "title": "Master Your Strengths", "details": {"text": "Give exam of {lesson} from {subject}", "lesson": lesson_for_task5, "subject": random_subject_for_task5}, "completed": False, "reward": 10, "action": {"type": "exam", "subject": random_subject_for_task5, "lessons": [lesson_for_task5]}})
        else:
            most_attempted_subject_info = sorted(user_subjects_stats, key=lambda x: x.get('attempted', 0), reverse=True)[0]
            most_attempted_subject = most_attempted_subject_info['subject']
            subject_exam_history_most = [e for e in user_exam_history if e['subject'] == most_attempted_subject]
            all_lessons_most = get_all_lessons_for_subject(most_attempted_subject, is_class10)
            lesson_counts_most = {lesson: 0 for lesson in all_lessons_most}
            for exam in subject_exam_history_most:
                for lesson in exam.get('lessons', []):
                    if lesson in lesson_counts_most:
                        lesson_counts_most[lesson] += 1
            
            min_attempts_most = min(lesson_counts_most.values()) if lesson_counts_most else 0
            least_tested_lessons_most = [lesson for lesson, count in lesson_counts_most.items() if count == min_attempts_most]
            
            if least_tested_lessons_most:
                least_tested_lessons_most.sort(key=lambda x: int(''.join(filter(str.isdigit, x))) if any(char.isdigit() for char in x) else float('inf'))
                lesson_for_task5 = least_tested_lessons_most[0]
                new_tasks.append({"id": 5, "title": "Refine Your Skills", "details": {"text": "Give exam of {lesson} from {subject}", "lesson": lesson_for_task5, "subject": most_attempted_subject}, "completed": False, "reward": 10, "action": {"type": "exam", "subject": most_attempted_subject, "lessons": [lesson_for_task5]}})

    user["tasks"] = {
        "generated_at": now.isoformat(),
        "tasks_list": new_tasks
    }
    
    update_user_tasks(current_user, user["tasks"], is_class10)
    
    return jsonify({"coins": user.get("coins", 0), "tasks": new_tasks})
        


@app.route("/admin/updates", methods=["POST"])
def add_update():
    data = request.get_json()
    if not all(key in data for key in ["version", "date", "changes"]):
        return jsonify({"message": "Missing required fields"}), 400

    UPDATE_LOGS.insert(0, data)
    return jsonify({"message": "Update added successfully"}), 201


@app.route("/api/leaderboard", methods=["GET"])
@jwt_required()
def get_leaderboard():
    current_user, is_class10 = get_current_user_info()
    class_num = 10 if is_class10 else 9
    
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    current_date = datetime.now()
    month_key = current_date.strftime("%Y-%m")
    
    # Get teacher IDs to exclude them from the leaderboard
    teachers_data = load_json_file("teachers.json")
    teacher_ids = list(teachers_data.keys()) if teachers_data else []
    leaderboard_data = data_store[class_num]["collections"][4]["Leaderboard"].get(
        month_key, {}
    )
    version = leaderboard_data.get("version", None)
    if not version:
        version = hashlib.sha256(f"{month_key}-{time.time()}".encode()).hexdigest()[:8]
        db = db10 if is_class10 else db9
        db["Leaderboard"].update_one(
            {"_id": month_key},
            {"$set": {"version": version}},
            upsert=True
        )
        # Update in-memory store as well
        data_store[class_num]["collections"][4]["Leaderboard"].setdefault(month_key, {})["version"] = version
    # Get all users from the database
    db = db10 if is_class10 else db9
    all_users = list(db['Users'].find())

    # Convert leaderboard data to list
    leaderboard = []
    students_in_leaderboard = set()

    # Add students who have taken exams
    for user_id, user_data in leaderboard_data.items():
        if user_id in teacher_ids:
            continue
        students_in_leaderboard.add(user_id)
        # Check if name exists before splitting
        if isinstance(user_data, dict) and user_data.get("name"):
            name_parts = user_data["name"].split()
            if len(name_parts) >= 2:
                display_name = f"{name_parts[0].upper()} {name_parts[-1].upper()}"
            else:
                display_name = name_parts[0].upper()
        else:
            display_name = "UNKNOWN"

        # Get user's division
        user = next((u for u in all_users if u.get('id') == user_id), None)
        division = user.get('division', 'N/A') if user else 'N/A'

        leaderboard.append(
            {
                "userId": user_id,
                "name": display_name,
                "division": division,
                "total_exams": user_data.get("total_exams", 0)
                if isinstance(user_data, dict)
                else 0,
                "coins": next((u.get("coins", 0) for u in all_users if u.get('id') == user_id), 0),
                "elo_score": user_data.get("elo_score", 0)
                if isinstance(user_data, dict)
                else 0,
                "has_taken_exam": True
            }
        )

    # Add remaining students with 0 stats
    for user in all_users:
        user_id = user.get('id')
        if user_id in teacher_ids:
            continue
        if user_id not in students_in_leaderboard:
            name_parts = user.get('name', '').split()
            if len(name_parts) >= 2:
                display_name = f"{name_parts[0].upper()} {name_parts[-1].upper()}"
            else:
                display_name = name_parts[0].upper() if name_parts else "UNKNOWN"

            division = user.get('division', 'N/A')

            leaderboard.append(
                {
                    "userId": user_id,
                    "name": display_name,
                    "division": division,
                    "total_exams": 0,
                    "coins": user.get("coins", 0),
                    "elo_score": 0,
                    "has_taken_exam": False
                }
            )

    if not leaderboard:
        return jsonify(
            {"month": current_date.strftime("%B %Y"), "leaderboard": [], "zero": True}
        ), 200

    # Sort by participation, then ELO score, then by coins
    leaderboard.sort(
        key=lambda x: (x.get("has_taken_exam", False), x.get("elo_score", 0), x.get("coins", 0)),
        reverse=True,
    )
    
    # Calculate total count before pagination
    total_count = len(leaderboard)
    
    # Apply pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    leaderboard = leaderboard[start_idx:end_idx]

    # Add ranks based on absolute position
    for i, entry in enumerate(leaderboard, 1):
        entry["rank"] = start_idx + i

    return jsonify(
        {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count
            },
            "month": current_date.strftime("%B %Y"),
            "leaderboard": leaderboard,
            "zero": False,
            "class": "10" if is_class10 else "9",
            "leaderboard_id": version
        }
    ), 200


@app.route("/api/recalculate_leaderboard", methods=["POST"])
@jwt_required()
def recalculate_leaderboard_route():
    try:
        current_user, is_class10 = get_current_user_info()
        
        # Only allow teachers to recalculate leaderboard
        teachers_data = load_json_file("teachers.json")
        if not teachers_data or current_user not in teachers_data:
            return jsonify({"message": "Unauthorized. Only teachers can recalculate leaderboard."}), 403
            
        # Recalculate leaderboard
        recalculate_current_month_leaderboard(is_class10)
        
        return jsonify({"message": "Leaderboard recalculated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error recalculating leaderboard: {str(e)}"}), 500

# Run cleanup every hour
def start_cleanup_scheduler():
    while True:
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        time.sleep(3600)

def start_expiration_scheduler():
    """Periodically checks for and moves expired tests."""
    while True:
        try:
            move_expired_tests_to_inactive()
        except Exception as e:
            print(f"Error in expiration scheduler: {e}")
        # Sleep for 1 day
        time.sleep(86400)

# Start cleanup thread when app starts
cleanup_thread = threading.Thread(target=start_cleanup_scheduler, daemon=True)
cleanup_thread.start()

# Start test expiration thread when app starts
expiration_thread = threading.Thread(target=start_expiration_scheduler, daemon=True)
expiration_thread.start()

if __name__ == "__main__":
    app.run(
        debug=False,
        host='0.0.0.0',
        port=(9027)
    )
