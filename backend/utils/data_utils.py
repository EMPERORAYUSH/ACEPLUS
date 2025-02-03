import json
import os

def load_json_file(filename, data_path="data"):
    try:
        with open(os.path.join(data_path, filename), "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def calculate_lesson_analytics(questions, selected_answers):
    """
    Calculate per-lesson analytics using l-id or lesson field from questions

    Args:
        questions: List of question dictionaries containing l-id or lesson
        selected_answers: List of user's selected answers

    Returns:
        dict: Lesson-wise analytics with scores and details
    """
    lesson_analytics = {}

    for i, (question, selected_answer) in enumerate(zip(questions, selected_answers)):
        # Try to get lesson ID from l-id first, then from lesson field
        if "l-id" in question:
            lesson_id = question["l-id"].split("Q")[0]  # Extract L1, L2, etc.
        elif "lesson" in question:
            lesson_id = f"L{question['lesson']}"
        else:
            # Skip questions without lesson identification
            continue

        if lesson_id not in lesson_analytics:
            lesson_analytics[lesson_id] = {
                "lesson_name": f"Lesson {lesson_id[1:]}",  # L1 -> Lesson 1
                "questions_total": 0,
                "questions_correct": 0,
                "percentage": 0,
            }

        lesson_analytics[lesson_id]["questions_total"] += 1
        if selected_answer["option"] == question.get("answer"):
            lesson_analytics[lesson_id]["questions_correct"] += 1

    # Calculate percentages for each lesson
    for lesson in lesson_analytics.values():
        lesson["percentage"] = (
            lesson["questions_correct"] / lesson["questions_total"]
        ) * 100

    return lesson_analytics

def decode_unicode(obj):
    if isinstance(obj, str):
        try:
            return json.loads(f'"{obj}"')
        except json.JSONDecodeError:
            return obj
    elif isinstance(obj, dict):
        return {
            decode_unicode(key): decode_unicode(value) for key, value in obj.items()
        }
    elif isinstance(obj, list):
        return [decode_unicode(element) for element in obj]
    return obj

