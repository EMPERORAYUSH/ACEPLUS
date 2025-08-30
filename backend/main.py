try:
    import logging
    import copy
    import json
    import os
    import random
    import time
    import traceback
    from datetime import datetime, timedelta

    import generate
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
        user_repo,
        exam_repo,
        test_repo,
        leaderboard_service,
        convert_objectid_to_str,
        preload_caches,
    )

    import threading
    from utils.lesson_utils import lesson2filepath, get_all_lessons_for_subject
    from utils.data_utils import load_json_file, calculate_lesson_analytics, decode_unicode
    from utils.name_utils import generate_memorable_name
    from utils.auth_utils import get_student_class, get_current_user_info
    from utils.job_utils import allowed_file, cleanup_old_files, delete_unsubmitted_exams
    from utils.parse_files import render_pdf_previews, render_pptx_previews

except ImportError as e:
    print(f"Import Error: {str(e)}")
    print("Did you run npm run setup?")
    raise

# Load environment variables
load_dotenv()

VERSION = "1.1.0"

# Setup
logging_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logging.log")
logging.basicConfig(filename=logging_file, level=logging.DEBUG)
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "data")

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
class10_student_info = json.loads(open(os.path.join(data_path, "class10_students.json")).read())

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
            "standard": teacher_info.get("current_standard"),
        }
        is_class10 = teacher_info.get("current_standard") == 10
    else:
        # Regular student login flow
        student_data, is_class10 = get_student_class(user_id, student_info, class10_student_info)
        print(student_data) 
        if student_data is None:
            return jsonify({"message": "Invalid User ID"}), 400

    # Check if user exists
    user = user_repo.get_user(user_id, is_class10)
    if user.get("password") is None:
        return jsonify({"message": "User not registered. Please register."}), 401

    if user.get("password") == password:
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

    user = user_repo.get_user(user_id, is_class10)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    if user.get("password"):
        return jsonify({"message": "User is already registered. Please login."}), 400

    # Keep legacy behavior - require registration_code to match if present on user
    if user.get("registration_code") != registration_code:
        return jsonify({"message": "Invalid registration code"}), 401

    if user_repo.set_password(user_id, new_password, is_class10):
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
        test_data = test_repo.get_test(test_id, is_class10)
        if not test_data:
            return jsonify({"message": "Test not found or already completed"}), 404
        exam_id = f"{test_id}-{current_user}"
        subject = test_data["subject"]
        lessons = test_data.get("lessons", [])
        questions = test_data.get("questions", [])

    else:
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
        "standard": 10 if is_class10 else 9,
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
        added_exam = exam_repo.add_exam(exam_data, is_class10)
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

    exam = exam_repo.get_exam(exam_id, is_class10)
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

    percentage = (score / total_questions) * 100 if total_questions else 0

    # Calculate lesson-wise analytics
    lesson_analytics = calculate_lesson_analytics(exam["questions"], selected_answers)

    # Generate performance analysis (non-critical)
    try:
        performance_analysis = generate.generate_performance_analysis(
            initial_results, exam["lessons"], is_class10
        )
        perf_analysis = performance_analysis
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

    # If it's a test submission: update completed_by list
    if exam.get("test", False):
        test_id = "-".join(exam_id.split("-")[:-1])
        try:
            test_data = test_repo.get_test(test_id, is_class10)
            if test_data:
                completed_by = test_data.get("completed_by", [])
                if current_user not in completed_by:
                    completed_by.append(current_user)
                    test_repo.update_test(test_id, {"completed_by": completed_by}, is_class10)
        except Exception as e:
            print(f"Error updating active test: {e}")

    # Persist exam update
    if exam_repo.update_exam(exam_id, updated_data, is_class10):
        # Update user stats in user-centric model
        try:
            user_stats, subject_stats = user_repo.update_stats_after_exam(
                current_user,
                exam["subject"],
                score,
                total_questions,
                float(percentage),
                exam_id,
                exam.get("lessons", []),
                exam.get("test", False),
                exam.get("test_name"),
                is_class10,
            )
            # Update leaderboard snapshot asynchronously
            standard = 10 if is_class10 else 9
            leaderboard_service.update_on_submission(current_user, standard)
        except Exception as e:
            print(f"Error updating user stats: {e}")

        # Check for task completion
        completed_tasks = check_and_update_tasks(current_user, is_class10, exam)

        # Award 10 coins for test completion
        if exam.get("test", False):
            user = user_repo.get_user(current_user, is_class10)
            if user:
                new_coins = user.get("coins", 0) + 10
                user_repo.update_tasks(current_user, user.get("tasks", {}), is_class10, coins=new_coins)
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
    user = user_repo.get_user(user_id, is_class10)
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

        # Various task completion logics
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
        user_repo.update_tasks(user_id, user["tasks"], coins=user.get("coins"))

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
            headers={'Cache-Control': 'no-cache'}
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

    if isinstance(question_index, str):
        try:
            question_index = int(question_index)
        except ValueError:
            return jsonify({"message": "Question index must be a valid integer"}), 400

    exam = exam_repo.get_exam(exam_id, is_class10)
    if not exam:
        return jsonify({"message": "Exam not found"}), 404

    if exam["userId"] != current_user:
        return jsonify({"message": "Unauthorized access to exam"}), 401

    if not exam.get("results") or question_index >= len(exam["results"]):
        return jsonify({"message": "Invalid question index or exam has no results"}), 400

    result = exam["results"][question_index]
    question_text = result["question"]

    correct_answer = result["correct_answer"]
    selected_answer = result["selected_answer"]

    correct_answer_text = correct_answer.split(") ", 1)[1] if ") " in correct_answer else correct_answer
    selected_answer_text = selected_answer.split(") ", 1)[1] if ") " in selected_answer else selected_answer

    # Find original question to get options
    original_question = None
    for i, q in enumerate(exam["questions"]):
        if q["question"] == question_text:
            original_question = q
            break

    if not original_question:
        return jsonify({"message": "Question not found in exam"}), 404

    options = original_question["options"]

    try:
        def generate_and_save():
            full_solution = ""
            for chunk in generate.generate_solution_stream(
                question_text,
                correct_answer_text,
                selected_answer_text,
                options
            ):
                full_solution += chunk
                yield chunk
            try:
                exam_repo.update_exam_solution(exam_id, question_index, full_solution, is_class10)
            except Exception as e:
                print(f"Error saving solution to database: {e}")

        return Response(
            generate_and_save(),
            mimetype='text/event-stream',
            headers={'Cache-Control': 'no-cache'}
        )
    except Exception as e:
        print(f"Error generating solution: {e}")
        return jsonify({"message": f"Error generating solution: {str(e)}"}), 500


@app.route("/api/exam/<exam_id>", methods=["GET"])
@jwt_required()
def get_exam_route(exam_id):
    _, is_class10 = get_current_user_info()
    exam_data = exam_repo.get_exam(exam_id, is_class10)

    if exam_data:
        response_data = copy.deepcopy(exam_data)
        if not response_data.get("is_submitted", False):
            for question in response_data["questions"]:
                question.pop("answer", None)

        response_data = decode_unicode(response_data)
        response_data = convert_objectid_to_str(response_data)
        return jsonify(response_data), 200
    else:
        return jsonify({"message": "Exam not found"}), 404


@app.route("/api/user_exams", methods=["GET"])
@jwt_required()
def get_user_exams_route():
    current_user, is_class10 = get_current_user_info()
    overview_list = user_repo.get_user_exams_overview(current_user, is_class10)
    overview_list = convert_objectid_to_str(overview_list)
    return jsonify(overview_list), 200


@app.route("/api/report", methods=["POST"])
@jwt_required()
def report_question():
    current_user, is_class10 = get_current_user_info()
    data = request.get_json()

    exam_id = data.get("examId")
    question_index = data.get("questionIndex")
    reason = data.get("reason")
    description = data.get("description")

    if not all([exam_id, question_index is not None, description]):
        return jsonify({"message": "Missing required fields"}), 400

    try:
        # Get the exam data
        exam = exam_repo.get_exam(exam_id, is_class10)
        if not exam:
            return jsonify({"message": "Exam not found"}), 404

        # Get the question data
        if question_index >= len(exam.get("questions", [])):
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

        # Check if question already reported by this user
        for report in reports:
            if (
                report.get("exam_id") == exam_id
                and report.get("question_index") == question_index
                and report.get("user_id") == current_user
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
            "subject": exam.get("subject"),
            "lessons": exam.get("lessons"),
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
    standard = 10 if is_class10 else 9
    all_tests = test_repo.get_all_tests_by_standard(standard)
    user = user_repo.get_user(user_id, is_class10)

    available_tests = []
    for test in all_tests:
        if user_id in test.get("completed_by", []):
            continue

        assigned_students = test.get("students")
        assigned_division = test.get("division")
        test_standard = test.get("standard")

        if (test_standard == 10) != is_class10:
            continue

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

    if is_teacher:
        all_tests = test_repo.get_all_tests_by_standard(10 if is_class10 else 9)
        available_tests = [
            test for test in all_tests if test.get("created_by") == current_user
        ]
    else:
        available_tests = get_available_tests_for_user(current_user, is_class10)

    if not is_teacher:
        available_tests = [
            test for test in available_tests
            if current_user not in test.get("completed_by", [])
        ]

    if not available_tests and not is_teacher:
        return jsonify({"message": "No tests available"}), 404

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

    response = convert_objectid_to_str(response)
    return jsonify(response), 200


@app.route("/api/generate_test", methods=["POST"])
@jwt_required()
def generate_test():
    current_user, _ = get_current_user_info()
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
            pass
        else:
            try:
                questions = generate.generate_exam_questions(subject, lesson_paths, current_user)
            except Exception as e:
                print(f"Error generating questions: {e}")
                return jsonify({"message": f"Error generating questions: {str(e)}"}), 500

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
    students = data.get("students")
    division = data.get("division")
    expiration_date = data.get("expiration_date")
    test_name = data.get("test_name")

    if not all([subject, questions, expiration_date]):
        return jsonify({"message": "Subject, questions, and expiration date are required"}), 400

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
        test_repo.add_test(test_data)
        return jsonify({"test-id": test_id}), 201
    except Exception as e:
        print(f"Error creating test: {e}")
        return jsonify({"message": f"Error creating test: {str(e)}"}), 500


@app.route("/api/user_stats", methods=["GET"])
@jwt_required()
def get_user_stats_route():
    current_user, is_class10 = get_current_user_info()
    stats = user_repo.get_user_stats(current_user)

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
        {"average_percentage": f"{stats.get('avgPercentage', 0):2.2f}%"},
    ]

    response = {"version": VERSION, "stats": formatted_stats}
    return jsonify(response), 200


@app.route("/api/subject_stats/<subject>", methods=["GET"])
@jwt_required()
def get_subject_stats_route(subject):
    current_user, is_class10 = get_current_user_info()
    stats = user_repo.get_user_subject_stats(current_user, subject)
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

    stats = convert_objectid_to_str(stats)
    return jsonify(stats), 20


@app.route("/api/students_by_standard", methods=["GET"])
@jwt_required()
def get_students_by_standard_route():
    _, is_class10 = get_current_user_info()

    # Allow teachers to specify the class
    class10_param = request.args.get("class10")
    if class10_param is not None:
        is_class10 = class10_param.lower() == "true"

    try:
        students = user_repo.get_all_students_by_standard(10 if is_class10 else 9)
        return jsonify(students), 200
    except Exception as e:
        return jsonify({"message": f"Error fetching students: {str(e)}"}), 500


@app.route("/api/leaderboard", methods=["GET"])
@jwt_required()
def get_leaderboard():
    current_user, is_class10 = get_current_user_info()
    standard = 10 if is_class10 else 9

    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))

    # Get snapshot (build if missing)
    snapshot = leaderboard_service.get_or_build_monthly(standard, page=page, page_size=page_size)
    entries = snapshot.get("entries", [])
    total_count = snapshot.get("total_count", 0)
    version = snapshot.get("version")
    mk = snapshot.get("month")

    # Convert month_key (YYYY-MM) to "Month YYYY"
    try:
        dt = datetime.strptime(mk + "-01", "%Y-%m-%d")
        month_label = dt.strftime("%B %Y")
    except Exception:
        month_label = mk

    # entries are already sorted and paginated, add in coins and fields are present
    leaderboard = []
    for e in entries:
        leaderboard.append(
            {
                "userId": e.get("userId"),
                "name": e.get("name"),
                "division": e.get("division"),
                "total_exams": e.get("total_exams", 0),
                "coins": e.get("coins", 0),
                "elo_score": e.get("elo_score", 0),
                "has_taken_exam": e.get("has_taken_exam", False),
                "rank": e.get("rank"),
            }
        )

    return jsonify(
        {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count
            },
            "month": month_label,
            "leaderboard": leaderboard,
            "zero": False,
            "class": "10" if is_class10 else "9",
            "leaderboard_id": version
        }
    ), 200


@app.route("/api/upload_files", methods=["POST"])
@jwt_required()
def upload_files():
    current_user, _ = get_current_user_info()

    # Collect any files (compatible with both 'file_*' and 'image_*' keys)
    files = [request.files[key] for key in request.files]

    if not files:
        return jsonify({'message': 'No files provided'}), 400

    # Per-user daily data cap: 100 MB
    BYTES_LIMIT = 100 * 1024 * 1024  # 100 MB
    now_ts = time.time()
    twenty_four_hours = 24 * 60 * 60

    def list_user_files_last_24h(user_id: str):
        items = []
        try:
            for fname in os.listdir(app.config['UPLOAD_FOLDER']):
                if not fname.startswith(f"{user_id}_"):
                    continue
                fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                try:
                    ctime = os.path.getctime(fpath)
                    if now_ts - ctime <= twenty_four_hours:
                        size = os.path.getsize(fpath)
                        items.append({
                            'name': fname,
                            'path': fpath,
                            'ctime': ctime,
                            'size': size
                        })
                except Exception:
                    continue
        except Exception:
            pass
        items.sort(key=lambda x: x['ctime'])
        return items

    def enforce_user_bytes_cap(user_id: str):
        files_24h = list_user_files_last_24h(user_id)
        total_bytes = sum(f['size'] for f in files_24h)
        while total_bytes > BYTES_LIMIT and files_24h:
            oldest = files_24h.pop(0)
            try:
                os.remove(oldest['path'])
                print(f"Deleted oldest file to enforce cap: {oldest['name']}")
                total_bytes -= oldest['size']
            except Exception as e:
                print(f"Error deleting oldest file {oldest['name']}: {e}")
                break

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
                previews = [unique_filename]
            elif ftype == 'pdf':
                previews = render_pdf_previews(filepath, app.config['UPLOAD_FOLDER'], pages=1)
            elif ftype == 'pptx':
                previews = render_pptx_previews(filepath, app.config['UPLOAD_FOLDER'], slides=1)

            try:
                enforce_user_bytes_cap(current_user)
            except Exception as e:
                print(f"Error enforcing data cap for user {current_user}: {e}")

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

    filenames = request.args.getlist('filenames')

    if not filenames:
        return jsonify({'message': 'No files provided'}), 400

    try:
        file_paths = [os.path.join(app.config['UPLOAD_FOLDER'], filename) for filename in filenames]

        missing_files = []
        for path in file_paths:
            if not os.path.exists(path):
                missing_files.append(os.path.basename(path))

        if missing_files:
            return jsonify({
                'message': f'Some files were not found: {", ".join(missing_files)}'
            }), 404

        def generate_sse():
            try:
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

                    if not questions:
                        yield f"event: error\ndata: {json.dumps({'message': 'No questions could be extracted from the files'})}\n\n"
                        return

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
                'X-Accel-Buffering': 'no',
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
    user = user_repo.get_user(current_user, is_class10)

    if not user:
        return jsonify({"message": "User not found"}), 404

    tasks = user.get("tasks", {})
    now = datetime.now()

    if tasks.get("generated_at"):
        try:
            generated_at = datetime.fromisoformat(tasks["generated_at"])
            if (now - generated_at) < timedelta(hours=24) and tasks.get("tasks_list"):
                return jsonify({
                    "coins": user.get("coins", 0),
                    "tasks": tasks.get("tasks_list", [])
                })
        except Exception:
            pass

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

    user_subjects_stats = user_repo.get_all_user_subject_stats(current_user)
    user_exam_history = user_repo.get_user_exams_overview(current_user)
    total_exams_attempted = len(user_exam_history)

    # Task 2: Give 1 exam of {subject}
    subject_for_task2 = "Math"
    task2_subject_stats = [s for s in user_subjects_stats if s.get('subject') != 'English']

    if not task2_subject_stats:
        subject_for_task2 = random.choice(["Math", "Science", "SS"])
    elif total_exams_attempted < 5:
        unattempted_subjects = [s['subject'] for s in task2_subject_stats if s['attempted'] == 0]
        if unattempted_subjects:
            subject_for_task2 = random.choice(unattempted_subjects)
        else:
            subject_for_task2 = random.choice([s['subject'] for s in task2_subject_stats])
    else:
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

    user_repo.update_tasks(current_user, user["tasks"])

    response_data = {"coins": user.get("coins", 0), "tasks": new_tasks}
    response_data = convert_objectid_to_str(response_data)
    return jsonify(response_data)


# Run cleanup every hour
def start_cleanup_scheduler():
    while True:
        cleanup_old_files(app.config['UPLOAD_FOLDER'])
        time.sleep(3600)


def start_expiration_scheduler():
    """Periodically checks for and moves expired tests."""
    while True:
        try:
            test_repo.move_expired_tests_to_inactive()
        except Exception as e:
            print(f"Error in expiration scheduler: {e}")
        time.sleep(86400)


def start_unsubmitted_exams_scheduler():
    """Periodically deletes unsubmitted exams older than 7 days."""
    while True:
        try:
            delete_unsubmitted_exams(exam_repo)
        except Exception as e:
            print(f"Error in unsubmitted exams scheduler: {e}")
        # Run once per day (86400 seconds)
        time.sleep(86400)


# Start background threads when app starts
cleanup_thread = threading.Thread(target=start_cleanup_scheduler, daemon=True)
cleanup_thread.start()

expiration_thread = threading.Thread(target=start_expiration_scheduler, daemon=True)
expiration_thread.start()

unsubmitted_exams_thread = threading.Thread(target=start_unsubmitted_exams_scheduler, daemon=True)
unsubmitted_exams_thread.start()

if __name__ == "__main__":
    print("Preloading caches before starting server...")
    preload_caches()
    print("Server starting...")
    app.run(
        debug=False,
        host='0.0.0.0',
        port=(9027)
    )
