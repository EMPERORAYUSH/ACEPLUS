try:
    import copy
    import json
    import os
    import random
    import time
    import traceback
    from datetime import datetime
    import generate
    from bson.json_util import dumps
    from werkzeug.utils import secure_filename
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS
    from flask_jwt_extended import (
        JWTManager,
        create_access_token,
        jwt_required,
    )
    from dotenv import load_dotenv
    from db import (
        add_exam,
        create_user_data,
        download_data,
        get_average_percentage,
        get_average_scores,
        get_exam,
        get_overview_stats,
        get_standard_stats,
        get_student_detailed_stats,
        data_store,
        get_students_by_division,
        get_subject_stats_by_division,
        get_total_exams,
        get_total_exams_by_class,
        get_total_students,
        get_total_students_by_class,
        get_user,
        get_user_exam_history,
        get_user_stats,
        get_user_subjects,
        update_exam,
        update_user_stats_after_exam,
        db9,
        db10,
        recalculate_current_month_leaderboard,
    )
    import threading
    import uuid
    from utils.lesson_utils import lesson2filepath
    from utils.data_utils import load_json_file, calculate_lesson_analytics, decode_unicode
    from utils.name_utils import generate_memorable_name
    from .utils.auth_utils import get_student_class, get_current_user_info
    from .utils.job_utils import allowed_file, cleanup_old_files, cleanup_old_jobs, JOB_QUEUE, JOB_RESULTS, JOB_STATUS, job_processor

except ImportError as e:
    print(f"Import Error: {str(e)}")
    print("Did you run npm run setup?")
    raise

# Load environment variables
load_dotenv()

# Setup
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
        "expose_headers": ["Content-Type", "Authorization"],
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

# Add this near the top with other global variables
UPDATE_LOGS = [
    {
        "version": "1.8.3",
        "date": "2024-11-19",
        "changes": [
            {
                "title": "Added Performance Overview",
                "description": "Students will be able to see a performance overview of the exam. AI model will analyse and suggest topics to re-read and steps to practise. This provides a good assistance on what students should study next",
            },
            {
                "title": "Questions repeat less",
                "description": "If you want to practise a lesson more, repeated questions across exams won't haunt you!",
            },
            {
                "title": "Randomised options",
                "description": "Questions would now have varied options for correct answers, which previously revolved around B & C. Assertion and resoning questions are not affected by this change.",
            },
        ],
    }
]

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
        student_data, is_class10 = get_student_class(user_id)
        if student_data is None:
            return jsonify({"message": "Invalid User ID"}), 400

    # Check if user exists in database
    user = get_user(user_id, class10=is_class10)

    if user is None:
        try:
            name = student_data["name"]
            roll = student_data["roll"]
            division = student_data["div"]
            user = create_user_data(user_id, password, name, roll, division, is_class10)

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
            }
            return jsonify(response), 200

        except Exception as e:
            return jsonify({"message": f"Error creating new user: {str(e)}"}), 500

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
        }
        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401


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

        # Load test data from active_tests.json
        active_tests = load_json_file("active_tests.json")
        if not active_tests or "tests" not in active_tests:
            return jsonify({"message": "Test not found"}), 404
        print("\n\n", active_tests, "\n\n")
        # Access the tests array inside active_tests
        test_data = next(
            (
                test
                for test in active_tests["tests"]
                if test["test-id"] == test_id
                and current_user not in test.get("completed_by", [])
            ),
            None,
        )
        print("\n\n", test_data, "\n\n")
        if not test_data:
            return jsonify({"message": "Test not found or already completed"}), 404
        print(is_class10)
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

    # Generate solutions if there are any incorrect answers
    if questions_needing_solutions:
        try:
            solutions = generate.generate_solutions_batch(questions_needing_solutions)

            # Map solutions back to results
            for solution in solutions:
                for i, result in enumerate(initial_results):
                    if result["question"] == solution["question"]:
                        initial_results[i]["solution"] = solution["solution"]
                        break

        except Exception as e:
            print(f"Error generating solutions: {e}")
            # Continue without solutions if generation fails
            pass

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
    }

    # If it's a test submission
    if exam.get("test", False):
        # Extract the test ID from exam ID (e.g., "TS-Math-101" from "TS-Math-101-user123")
        test_id = "-".join(
            exam_id.split("-")[:-1]
        )  # Get everything before the last segment

        try:
            # Load and update active_tests.json
            active_tests_data = load_json_file("active_tests.json")
            if active_tests_data and "tests" in active_tests_data:
                # Find and update the specific test
                for test in active_tests_data["tests"]:
                    if test["test-id"] == test_id:
                        # Initialize completed_by if it doesn't exist
                        if "completed_by" not in test:
                            test["completed_by"] = []

                        # Add current user if not already completed
                        if current_user not in test["completed_by"]:
                            test["completed_by"].append(current_user)

                        # Write updates back to file
                        with open(
                            os.path.join(data_path, "active_tests.json"),
                            "w",
                            encoding="utf-8",
                        ) as f:
                            json.dump(
                                active_tests_data, f, indent=4, ensure_ascii=False
                            )
                        break
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

        return jsonify(
            {
                "message": "Exam submitted successfully",
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "results": initial_results,
            }
        ), 200
    else:
        return jsonify({"message": "Failed to submit exam"}), 500


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

    if not all([exam_id, question_index]):
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


@app.route("/api/tests", methods=["GET"])
@jwt_required()
def get_tests():
    current_user, is_class10 = get_current_user_info()
    # Load required JSON files
    active_tests_data = load_json_file("active_tests.json")
    teachers_data = load_json_file("teachers.json")

    if not active_tests_data or "tests" not in active_tests_data:
        return jsonify({"message": "No tests available"}), 404

    # Get the tests array from the data
    active_tests = active_tests_data["tests"]

    # Check if user is teacher
    is_teacher = current_user in teachers_data if teachers_data else False

    # Filter tests based on class
    available_tests = []
    for test in active_tests:
        # Ensure test is a dictionary
        if not isinstance(test, dict):
            continue

        # For teachers, only show tests they created
        if is_teacher:
            if test.get("created_by") != current_user:
                continue
        else:
            # For students, skip if already completed
            completed_users = test.get("completed_by", [])
            if current_user in completed_users:
                continue

            # Skip if test is not for student's class
            test_standard = test.get("standard")
            if (test_standard == 10) != is_class10:
                continue

        test_info = {
            "subject": test.get("subject"),
            "test-id": test.get("test-id"),
            "lessons": test.get("lessons", []),
            "questions": len(test.get("questions", [])),
        }
        available_tests.append(test_info)

    response = {"tests": available_tests, "teacher": is_teacher}

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
    # Verify teacher access (0001-0009)
    teachers_data = load_json_file("teachers.json")
    if not teachers_data or current_user not in teachers_data:
        return jsonify({"message": "Unauthorized access"}), 401

    data = request.get_json()
    subject = data.get("subject")
    lessons = data.get("lessons")
    class10 = data.get("class10", False)  # Allow teacher to specify class

    if not subject or not lessons:
        return jsonify({"message": "Subject and lessons are required"}), 400

    lesson_paths = [
        lesson2filepath(subject, lesson, class10=class10) for lesson in lessons
    ]

    if not lesson_paths:
        return jsonify({"message": "Invalid lessons provided"}), 400

    try:
        questions = generate.generate_exam_questions(subject, lesson_paths, current_user)
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

    except Exception as e:
        print(f"Error generating questions: {e}")
        return jsonify({"message": f"Error generating questions: {str(e)}"}), 500


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

    if not all([subject, lessons, questions]):
        return jsonify({"message": "Subject, lessons, and questions are required"}), 400

    # Validate question format
    for q in questions:
        if not all(key in q for key in ["question", "options", "answer"]):
            return jsonify({"message": "Invalid question format"}), 400
        if not all(key in q["options"] for key in ["a", "b", "c", "d"]):
            return jsonify({"message": "Invalid options format"}), 400

    # Shuffle questions
    random.shuffle(questions)

    # Generate test ID using random
    test_id = f"TS-{subject}-{str(random.randint(100,999))}"

    # Create test data
    test_data = {
        "test-id": test_id,
        "subject": subject,
        "standard": 10 if class10 else 9,
        "lessons": lessons,
        "questions": questions,
        "created_by": current_user,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "completed_by": [],
    }

    try:
        # Load and update active_tests.json
        active_tests = load_json_file("active_tests.json") or {"tests": []}
        active_tests["tests"].append(test_data)

        with open(os.path.join(data_path, "active_tests.json"), "w") as f:
            json.dump(active_tests, f, indent=4)

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
        return jsonify(
            [
                {"title": "Total Exams Attempted", "value": 0},
                {"title": "Total Marks Attempted", "value": 0},
                {"title": "Total Marks Gained", "value": 0},
                {"title": "Average Percentage", "value": "0.00%"},
            ]
        ), 200

    formatted_stats = [
        {"title": "Total Exams Attempted", "value": stats.get("attempted", 0)},
        {"title": "Total Marks Attempted", "value": stats.get("questions", 0)},
        {"title": "Total Marks Gained", "value": stats.get("correct", 0)},
        {
            "title": "Average Percentage",
            "value": f"{stats.get('avgpercentage', 0):2.2f}%",
        },
    ]
    return jsonify(formatted_stats), 200


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

@app.route("/api/upload_images", methods=["POST"])
@jwt_required()
def upload_images():
    current_user, _ = get_current_user_info()
    
    # Check if any files were uploaded
    files = []
    for key in request.files:
        if key.startswith('image_'):
            files.append(request.files[key])
    
    if not files:
        return jsonify({'message': 'No images provided'}), 400
        
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = int(time.time())
            unique_filename = f"{current_user}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            uploaded_files.append(unique_filename)
    
    if not uploaded_files:
        return jsonify({'message': 'No valid images uploaded'}), 400
        
    return jsonify({
        'message': 'Images uploaded successfully',
        'files': uploaded_files
    }), 200


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
    return jsonify(UPDATE_LOGS[0]), 200


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
    current_date = datetime.now()
    month_key = current_date.strftime("%Y-%m")

    # Get current month's leaderboard
    leaderboard_data = data_store[class_num]["collections"][4]["Leaderboard"].get(
        month_key, {}
    )

    # Get all users from the database
    db = db10 if is_class10 else db9
    all_users = list(db['Users'].find())

    # Convert leaderboard data to list
    leaderboard = []
    students_in_leaderboard = set()

    # Add students who have taken exams
    for user_id, user_data in leaderboard_data.items():
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
                "name": display_name,
                "division": division,
                "total_exams": user_data.get("total_exams", 0)
                if isinstance(user_data, dict)
                else 0,
                "average_percentage": round(user_data.get("average_percentage", 0), 2)
                if isinstance(user_data, dict)
                else 0,
                "elo_score": user_data.get("elo_score", 0)
                if isinstance(user_data, dict)
                else 0,
                "has_taken_exam": True
            }
        )

    # Add remaining students with 0 stats
    for user in all_users:
        user_id = user.get('id')
        if user_id not in students_in_leaderboard:
            name_parts = user.get('name', '').split()
            if len(name_parts) >= 2:
                display_name = f"{name_parts[0].upper()} {name_parts[-1].upper()}"
            else:
                display_name = name_parts[0].upper() if name_parts else "UNKNOWN"

            division = user.get('division', 'N/A')

            leaderboard.append(
                {
                    "name": display_name,
                    "division": division,
                    "total_exams": 0,
                    "average_percentage": 0,
                    "elo_score": 0,
                    "has_taken_exam": False
                }
            )

    if not leaderboard:
        return jsonify(
            {"month": current_date.strftime("%B %Y"), "leaderboard": [], "zero": True}
        ), 200

    # Sort by ELO score first, then by average percentage
    leaderboard.sort(
        key=lambda x: (x["elo_score"], x["average_percentage"]),
        reverse=True,
    )

    # Add ranks
    for i, entry in enumerate(leaderboard, 1):
        entry["rank"] = i

    return jsonify(
        {
            "month": current_date.strftime("%B %Y"),
            "leaderboard": leaderboard,
            "zero": False,
            "class": "10" if is_class10 else "9"
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
        cleanup_old_files()
        time.sleep(3600)

# Start cleanup thread when app starts
cleanup_thread = threading.Thread(target=start_cleanup_scheduler, daemon=True)
cleanup_thread.start()


def process_images_job(job_id, image_paths):
    try:
        print(f"\nStarting job {job_id} for {len(image_paths)} images")
        JOB_STATUS[job_id] = {
            "status": "processing",
            "total": 0,
            "completed": 0,
            "start_time": time.time()
        }
        print(f"Processing {len(image_paths)} images...")
        
        try:
            questions = []
            print("\nStarting image analysis stream...")
            for update in generate.analyze_images(image_paths):
                print(f"\nReceived update: {json.dumps(update, indent=2)}")
                
                if update["type"] == "total":
                    JOB_STATUS[job_id]["total"] = update["count"]
                    print(f"Updated total questions count: {update['count']}")
                elif update["type"] == "progress":
                    JOB_STATUS[job_id]["completed"] = update["count"]
                    print(f"Updated completed questions count: {update['count']}")
                elif update["type"] == "result":
                    questions = update["questions"]
                    print(f"Received final questions: {len(questions)}")
                    print("Questions structure:")
                    print(json.dumps(questions, indent=2))
                elif update["type"] == "error":
                    print(f"Received error update: {update['message']}")
                    raise Exception(update["message"])
            
            if questions:
                print(f"\nJob completed successfully with {len(questions)} questions")
                JOB_RESULTS[job_id] = questions
                JOB_STATUS[job_id]["status"] = "completed"
                # Ensure final counts are accurate
                if JOB_STATUS[job_id]["total"] == 0:
                    JOB_STATUS[job_id]["total"] = len(questions)
                JOB_STATUS[job_id]["completed"] = len(questions)
            else:
                print("\nNo questions were extracted")
                JOB_STATUS[job_id]["status"] = "failed"
                JOB_RESULTS[job_id] = "No questions could be extracted from the images"
                
        except Exception as e:
            print(f"Error processing images: {str(e)}")
            print("Full error details:")
            print(traceback.format_exc())
            JOB_STATUS[job_id]["status"] = "failed"
            JOB_RESULTS[job_id] = str(e)
            
    except Exception as e:
        print(f"Error in job {job_id}: {str(e)}")
        print("Full error details:")
        print(traceback.format_exc())
        JOB_STATUS[job_id]["status"] = "failed"
        JOB_RESULTS[job_id] = str(e)
    finally:
        # Calculate processing time
        end_time = time.time()
        processing_time = end_time - JOB_STATUS[job_id].get("start_time", end_time)
        
        print(f"\nFinal job status for {job_id}:")
        print(f"Status: {JOB_STATUS[job_id]['status']}")
        print(f"Total: {JOB_STATUS[job_id]['total']}")
        print(f"Completed: {JOB_STATUS[job_id]['completed']}")
        print(f"Processing time: {processing_time:.2f} seconds")

# Start the job processor thread
job_thread = threading.Thread(target=job_processor, daemon=True)
job_thread.start()

# Replace the generate_from_images route
@app.route("/api/generate_from_images", methods=["POST"])
@jwt_required()
def generate_from_images():
    current_user, _ = get_current_user_info()
    data = request.get_json()
    filenames = data.get('filenames', [])
    
    if not filenames:
        return jsonify({'message': 'No images provided'}), 400
        
    try:
        # Get full paths of the images
        image_paths = [os.path.join(app.config['UPLOAD_FOLDER'], filename) for filename in filenames]
        
        # Check if all files exist
        missing_files = []
        for path in image_paths:
            if not os.path.exists(path):
                missing_files.append(os.path.basename(path))
        
        if missing_files:
            return jsonify({
                'message': f'Some images were not found: {", ".join(missing_files)}'
            }), 404
            
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Add job to queue
        JOB_QUEUE.put((job_id, image_paths))
        
        return jsonify({
            'message': 'Image processing started',
            'job_id': job_id
        }), 202
            
    except Exception as e:
        print(f"Error in generate_from_images: {str(e)}")
        return jsonify({
            'message': f'Error processing images: {str(e)}'
        }), 500

@app.route("/api/check_job_status/<job_id>", methods=["GET"])
@jwt_required()
def check_job_status(job_id):
    job_status = JOB_STATUS.get(job_id)
    
    if job_status is None:
        return jsonify({
            'status': 'not_found',
            'message': 'Job not found'
        }), 404
        
    status = job_status["status"]
    
    if status == "completed":
        questions = JOB_RESULTS.get(job_id)
        # Clean up after sending results
        del JOB_STATUS[job_id]
        del JOB_RESULTS[job_id]
        
        # Debug print
        print(f"Questions being returned: {questions}")
        
        # Ensure questions is an array
        if not isinstance(questions, list):
            print(f"Questions is not a list, type: {type(questions)}")
            return jsonify({
                'status': 'failed',
                'message': 'No questions could be extracted from the images'
            }), 400
            
        if not questions:  # Empty list
            print("Questions list is empty")
            return jsonify({
                'status': 'failed',
                'message': 'No questions could be extracted from the images'
            }), 400
            
        return jsonify({
            'status': status,
            'questions': questions
        }), 200
        
    if status == "failed":
        error = JOB_RESULTS.get(job_id)
        # Clean up after sending error
        del JOB_STATUS[job_id]
        del JOB_RESULTS[job_id]
        return jsonify({
            'status': status,
            'message': error or 'Failed to process images'
        }), 400
        
    return jsonify({
        'status': status,
        'total': job_status.get('total', 0),
        'completed': job_status.get('completed', 0),
        'message': 'Job is still processing'
    }), 200

cleanup_thread = threading.Thread(target=cleanup_old_jobs, daemon=True)
cleanup_thread.start()

if __name__ == "__main__":
    app.run(
        debug=False,
        host='0.0.0.0',
        port=(9027)
    )
