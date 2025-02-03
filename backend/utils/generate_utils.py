import base64
import json
import random

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_tag_content(text, tag):
    """Extract content between XML tags"""
    start_tag = f"<{tag}>"
    end_tag = f"</{tag}>"
    start_idx = text.find(start_tag)
    if start_idx == -1:
        return None
    start_idx += len(start_tag)
    end_idx = text.find(end_tag, start_idx)
    if end_idx == -1:
        return None
    return text[start_idx:end_idx]

def parse_question_xml(xml_text):
    """Parse a single question XML into a question dict"""
    try:
        question_text = extract_tag_content(xml_text, "question_text")
        if not question_text:
            return None

        options = {}
        for opt in ['a', 'b', 'c', 'd']:
            opt_text = extract_tag_content(xml_text, opt)
            if opt_text:
                options[opt] = opt_text

        if len(options) != 4:
            return None

        answer = extract_tag_content(xml_text, "answer")
        if not answer:
            answer = ""

        return {
            "question": question_text,
            "options": options,
            "answer": answer
        }
    except Exception as e:
        print(f"Error parsing question XML: {e}")
        return None

def shuffle_question_options(questions):
    """
    Shuffle the options of each question while maintaining the correct answer.
    Assertion reason questions will not have their options shuffled.
    """

    for question in questions:
        # Check if this is an assertion reason question by looking at the options
        is_assertion_reason = any(
            "assertion" in str(value).lower() and "reason" in str(value).lower()
            for value in question["options"].values()
        )

        if not is_assertion_reason:
            # Store the correct answer value
            correct_answer_key = question["answer"]
            correct_answer_value = question["options"][correct_answer_key]

            # Get all option values and shuffle them
            option_values = list(question["options"].values())
            random.shuffle(option_values)

            # Create new options dictionary with shuffled values
            option_keys = list(
                question["options"].keys()
            )  # usually ['a', 'b', 'c', 'd']
            question["options"] = dict(zip(option_keys, option_values))

            # Find the new key for the correct answer
            for key, value in question["options"].items():
                if value == correct_answer_value:
                    question["answer"] = key
                    break

    return questions

def remove_duplicates_and_replace(questions, available_questions):
    """
    Remove duplicate questions and replace them with new ones from available questions.
    Simple exact match comparison.
    """
    seen_questions = {}  # question text -> question dict
    unique_questions = []

    for question in questions:
        q_text = question['question'].strip().lower()
        if q_text not in seen_questions:
            seen_questions[q_text] = question
            unique_questions.append(question)

    # If we removed any duplicates, try to replace them
    remaining_questions = [
        q for q in available_questions.values()
        if q['question'].strip().lower() not in seen_questions
    ]

    while len(unique_questions) < len(questions) and remaining_questions:
        new_question = random.choice(remaining_questions)
        unique_questions.append(new_question)
        remaining_questions.remove(new_question)

    return unique_questions

def parse_questions_from_json(file_path):
    # Update to explicitly use UTF-8 encoding
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        # Fallback to read with 'latin-1' if UTF-8 fails
        with open(file_path, 'r', encoding='latin-1') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return []
