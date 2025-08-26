import os
import json
from openai import OpenAI, RateLimitError
import logging
import traceback
from dotenv import load_dotenv
import time
import random
import sys
from pdf_prompts import (
    get_prompt as get_subject_prompt,
    get_verification_prompt,
    get_verification_system_prompt,
    get_fix_questions_prompt,
    get_fix_questions_system_prompt,
    get_format_prompt,
)
import copy
import concurrent.futures
from typing import Dict, List, Tuple, Any
from pdftext.extraction import plain_text_output
# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler(os.path.join(SCRIPT_DIR, 'app.log'))  # File handler
    ]
)
logger = logging.getLogger(__name__)
load_dotenv()
# Special instructions for specific lessons
LESSON_SPECIAL_INSTRUCTIONS = {
# Format:
# {
#   "Subject": {
#     "LessonName": "special instructions for this lesson",
#     ...
#   },
#   ...
# }
}


category_distribution = {
    "A": 30,
    "B": 30,
    "C": 20,
    "D": 20,
    "E": 20
}

def get_config(provider):
    providers = os.getenv("PROVIDERS")
    if not providers:
        raise ValueError("PROVIDERS environment variable is not set properly!")
    providers = json.loads(providers)
    model_configs = {}
    for i in providers:
        model_configs[i] = {
            "api_key": os.getenv(f"{i.upper()}_API_KEY"),
            "base_url": os.getenv(f"{i.upper()}_BASE_URL")
        }
    return model_configs[provider]

def extract_pdf(pdf_path):
    text = plain_text_output(pdf_path, sort=False, hyphens=False) # Optional arguments explained above
    text = text.replace('\n\n', '<PARAGRAPH_BREAK>')  # Temporarily replace double newlines
    text = text.replace('\n', ' ')  # Replace single newlines with a space
    text = text.replace('<PARAGRAPH_BREAK>', '\n\n')  # Restore double newlines
    return text



def model_inference(mode, system_prompt, prompt, response_format=None, reasoning_effort="high"):
    models_env_var = f"{mode.upper()}_MODELS"
    models = os.getenv(models_env_var)
    if not models:
        raise ValueError(f"{models_env_var} environment variable is not set properly!")
    models_list = json.loads(models)
    if not models:
        raise ValueError(f"{models_env_var} environment variable is not set properly!")
    temperature = 1.0 if mode.lower() in ["processing", "additional_questions"] else 0.1
    max_retry = 10


    for retry in range(max_retry):
        if len(models_list) == 1:
            models_list = json.loads(models) #reset models_list
        model_full_name = random.choice(models_list)
        provider, model_name = model_full_name.split("/")
        provider_config = get_config(provider)
        client = OpenAI(api_key=provider_config["api_key"], base_url=provider_config["base_url"])
        logger.info(f"Using model {model_full_name} for {mode} ATTEMPT - {retry+1}")
        
        try:
            api_params = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature
            }
            if response_format:
                api_params["response_format"] = {"type": response_format}
            if provider.lower() == "gemini":
                if "2.5" in model_name:
                    api_params["reasoning_effort"] = reasoning_effort
            response = client.chat.completions.create(**api_params)
            if not response or not response.choices:
                raise Exception("Invalid or empty response received from API")
            content = response.choices[0].message.content
            if response_format and response_format == "json_object":
                cleaned_content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned_content), model_full_name
            else:
                return content, model_full_name
        except RateLimitError as e:
            logging.error(f"Rate limit exceeded for model {model_full_name}. Error: {e}")
            time.sleep(60)
            if len(models_list) > 1:
                models_list.remove(model_full_name)
            else:
                time.sleep(60)
            continue
        except Exception as e:
            logging.error(f"Attempt {retry + 1}/{max_retry} failed for model {model_full_name}. Error: {e}")
            if len(models_list) > 1:
                models_list.remove(model_full_name)
            if retry == max_retry - 1:
                raise Exception(f"Max retries exceeded for model {model_full_name}. Last error: {e}")

    raise Exception("Max retries exceeded without a successful response.")

def add_new_questions_to_json(questions_json, new_questions):
    final_json = copy.deepcopy(questions_json)

    category_map = {cat['category_code']: cat for cat in final_json}

    for new_category in new_questions:
        cat_code = new_category['category_code']
        if cat_code in category_map:
            existing_category = category_map[cat_code]
            existing_questions_map = {q['question_number']: q for q in existing_category['questions']}
            for new_question in new_category['questions']:
                q_num = new_question['question_number']
                if q_num in existing_questions_map:
                    for i, q in enumerate(existing_category['questions']):
                        if q['question_number'] == q_num:
                            existing_category['questions'][i] = new_question
                            break
                else:
                    existing_category['questions'].append(new_question)        
        else:
            final_json.append(new_category)
            category_map[cat_code] = new_category

    return final_json



def load_lessons_data(class10=False):
    """Load lessons data from the appropriate JSON file"""
    try:
        logger.info("Attempting to load lessons data...")
        filename = "lessons10.json" if class10 else "lessons.json"
        file_path = os.path.join(base_dir, "data", filename)
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading lessons data: {str(e)}\n{traceback.format_exc()}")
        return None

def remove_delimited_text(text, start_delimiter, end_delimiter):
    result = []
    last_index = 0
    start_delimiter_len = len(start_delimiter)
    end_delimiter_len = len(end_delimiter)

    while True:
        start_index = text.find(start_delimiter, last_index)
        if start_index == -1:
            break

        end_index = text.find(end_delimiter, start_index + start_delimiter_len)
        if end_index == -1:
            break

        result.append(text[last_index:start_index])
        last_index = end_index + end_delimiter_len

    result.append(text[last_index:])
    return "".join(result)


def lesson2filepath(subject, lesson, class10=False):
    subject_lower = subject.lower()
    # Add class10 folder prefix if needed
    base_folder = "lessons10" if class10 else "lessons"

    if subject == "SS":
        # For SS, lesson format is like "C: Lesson-1" or "E: Lesson-1"
        prefix, lesson_num = lesson.split(":")  # Split into prefix (C/E/G/H) and lesson number
        lesson_num = lesson_num.strip().split("-")[1]  # Get the number after "Lesson-"
        prefix_lower = prefix.lower().strip()
        return os.path.join(base_dir, base_folder, subject_lower,f"{prefix_lower}.{lesson_num}.json")
    elif subject == "Science":
        lesson_number = lesson.split()[-1]
        return os.path.join(base_dir, base_folder, subject_lower, f"lesson-{lesson_number}.json")
    elif subject == "Math":
        lesson_number = lesson.split()[-1]
        return os.path.join(
            base_dir,
            base_folder, subject_lower, f"lesson{lesson_number}.json"
        )
    else:
        raise ValueError(f"Unsupported subject: {subject}")

def is_lesson_processed(subject, lesson_name, class_num):
    logger.info("Checking if lesson is processed")
    lessons_data = load_lessons_data(class_num == 10)
    if not lessons_data or subject not in lessons_data:
        return False
    base_name = os.path.splitext(os.path.basename(lesson_name))[0]

    # Different formats for different subjects
    if subject.lower() == "ss":
        # Extract prefix (e/c/g/h) and number from filename (e.g., "e.1.pdf" -> "E: Lesson-1")
        try:
            prefix, number = base_name.split(".")
            formatted_name = f"{prefix.upper()}: Lesson-{number}"
            if formatted_name not in lessons_data[subject]:
                return False
        except ValueError:
            logger.error(f"Invalid SS lesson filename format: {lesson_name}")
            return False
    else:
        # Math and Science format: "Lesson X"
        formatted_name = f"Lesson {base_name}"
        if formatted_name not in lessons_data[subject]:
            return False

    # Check if the corresponding question file exists
    question_file = lesson2filepath(subject, formatted_name, class_num == 10)
    return os.path.exists(question_file)

def get_lesson_key(subject, lesson_name):
    """Generate the key for looking up special instructions"""
    subject_lower = subject.lower()
    # Remove file extension if present
    lesson_base = os.path.splitext(lesson_name)[0]
    return f"{subject_lower}/{lesson_base}"

def format_questions_as_json(questions_str) -> List[Dict[str, Any]]:
    """Format questions into JSON using available models"""
    prompt = get_format_prompt(questions_str)
    model_choice = None
    try:
        content, model_choice = model_inference("formatting", system_prompt="You are a precise JSON formatter.", prompt=prompt, response_format="json_object", reasoning_effort="low")
        return (content)
    except json.JSONDecodeError as je:
        logger.error(f"JSON decode error with {model_choice}: {str(je)}")
        raise  # Re-raise to trigger alternate model attempt
        
def update_lessons_json(subject, lesson_name, class_num):
    logger.info(f"Updating lessons.json for {subject} {lesson_name} {class_num}")
    try:
        # Determine which lessons file to update
        filename = "lessons10.json" if class_num == 10 else "lessons.json"
        file_path = os.path.join(base_dir, "data", filename)

        with open(file_path, 'r') as f:
            lessons_data = json.load(f)

        if subject == "Science":
            lesson_number = lesson_name.split('-')[-1]
            formatted_name = f"Lesson {lesson_number}"
        elif subject == "Math":
            lesson_number = lesson_name.split('lesson')[-1]
            formatted_name = f"Lesson {lesson_number}"
        elif subject == "SS":
            # For SS files, lesson_name should be in format "prefix.number"
            prefix, number = lesson_name.split('.')
            formatted_name = f"{prefix.upper()}: Lesson-{number}"
        else:
            lesson_number = lesson_name.split('lesson')[-1]
            formatted_name = f"Lesson {lesson_number}"

        if subject not in lessons_data:
            lessons_data[subject] = []

        if formatted_name not in lessons_data[subject]:
            lessons_data[subject].append(formatted_name)
            # Sort lessons
            if subject == "SS":
                # Sort SS lessons by prefix and then number
                lessons_data[subject].sort(key=lambda x: (x.split(':')[0], int(x.split('-')[1])))
            else:
                lessons_data[subject].sort(key=lambda x: int(x.split()[-1]))

            # Save updated data
            with open(file_path, 'w') as f:
                json.dump(lessons_data, f, indent=2)

            logger.info(f"Added {formatted_name} to {subject} in {filename}")

    except Exception as e:
        logger.error(f"Error updating lessons JSON: {str(e)}\n{traceback.format_exc()}")

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Define base_dir at module level

def validate_questions(questions_list):
    logger.info("Validating questions json with invalid questions and distribution issues....")
    invalid_questions = {
        "skipped_questions":{},
        "invalid_options":{},
        "invalid_answers":{}
        }
    issues = False
    distribution_issues = {}
    for i in questions_list:
        # find distribution issues
        category_code = i["category_code"]
        question_numbers = []
        questions = i["questions"]
        for j in questions:
            question_numbers.append(j["question_number"])
        if max(question_numbers) < category_distribution[category_code.upper()]:
            logger.info(max(question_numbers))
            logger.info(category_distribution[category_code.upper()])
            distribution_issues[i["category_code"]] = category_distribution[category_code.upper()] - max(question_numbers)
            issues = True
        # find missing numbers
        questions_set = set(question_numbers)
        required_numbers = set(range(1, max(question_numbers) + 1))
        missing_numbers = required_numbers - questions_set
        if missing_numbers:
            invalid_questions["skipped_questions"].setdefault(category_code, []).extend(list(missing_numbers))
            issues = True
        # find missing options
        for j in questions:
            if len(j["options"].keys()) != 4:
                invalid_questions["invalid_options"].setdefault(category_code, []).append(j["question_number"])
                issues = True
            # find invalid answers
            elif len(j["answer"]) != 1:
                invalid_questions["invalid_answers"].setdefault(category_code, []).append(j["question_number"])
                issues = True
    return invalid_questions, distribution_issues, issues

def process_pdf(pdf_path, subject, class_num):
    """Process a PDF file and generate questions"""
    lesson_name = os.path.splitext(os.path.basename(pdf_path))[0]
    if is_lesson_processed(subject, lesson_name, class_num):
        logger.info(f"Lesson {lesson_name} already processed for {subject} Class {class_num}")
        return None

    pdf_data = extract_pdf(pdf_path)
    logger.info(f"Successfully extracted data from {lesson_name}")
    special_instructions = None
    # Add special instructions if they exist
    lesson_key = get_lesson_key(subject, lesson_name)
    if lesson_key in LESSON_SPECIAL_INSTRUCTIONS:
        logger.info(f"Adding special instructions for {lesson_key}")
        special_instructions = LESSON_SPECIAL_INSTRUCTIONS[lesson_key]
    prompt = get_subject_prompt(subject, class_num, pdf=pdf_data, special_instructions=special_instructions)
    questions_str = None
    system_prompt = prompt[0]
    base_prompt = prompt[1]
    logger.info(f"Generating questions for {lesson_name}")
    try:
            # Generate questions with streaming
        questions_str = model_inference(mode="processing", system_prompt=system_prompt, prompt=base_prompt, reasoning_effort="high")[0]
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
    if not questions_str:
        raise ValueError("No response received")
    questions_str = remove_delimited_text(questions_str, "<explaination>", "</explaination>")
    print(f"\n\n\n\n {questions_str} \n\n\n\n")
    logger.info(f"Starting formatting for {lesson_name}") 

    #initialzing vars
    try_count = 0
    error_count = 0

    try:
        questions_json = format_questions_as_json(questions_str)
        if not questions_json:
            logger.error("Question formatting failed. Check previous logs for details.")
            raise ValueError("Question formatting failed. No response received.")
    except Exception as e:
        logger.error(f"Question formatting failed: {e}")
        return None
    questions_json = questions_json #idk what i am doing
    while True:
        if error_count>3:
            logger.info("Too many errors, exiting")
            break
        try_count += 1    
        print(f"try count: {try_count}")
        #initialize variables
        question_issues = None
        distribution_issues = None

        validation = validate_questions(questions_json)
        logger.info(f"validation: {validation}")
        if validation[2]:
            print(validation)
            question_issues = validation[0]
            logger.info(f"Found Question issues: {question_issues}")
            distribution_issues = validation[1]
            logger.info(f"Found Distribution issues: {distribution_issues}")
        else:
            logger.info("No issues found in last validation attempt. Skipping additional questions...") 
            break
        
        #build rewriting prompt.
        system_prompt = get_fix_questions_system_prompt()
        prompt = get_fix_questions_prompt(previous_questions=questions_str, pdf_file=pdf_path, format_issues=question_issues, distribution_issues=distribution_issues)
        try:
            logger.info("Generating additional questions / fixing questions...")
            new_questions = model_inference(mode="ADDITIONAL_QUESTIONS", system_prompt=system_prompt, prompt=prompt, reasoning_effort="medium")
            print(f"\n\n\n\n {new_questions} \n\n\n\n")
            question_js = format_questions_as_json(new_questions)
            print(question_js)
            if question_js is None:
                logger.error("Question formatting failed. cheack previous logs for details.")
                error_count += 1
                raise
        except Exception as e:
            logger.info(f"Error occured {e}")
            error_count += 1
            continue
    
        questions_json = add_new_questions_to_json(questions_json, question_js)
        validation2  = validate_questions(questions_json)
        if validation2[2]:
            print(validation)
            continue
        else:
            break
    # Verify answers using randomly selected model
    logger.info("Verifying answers for given questions...")
    formatted_questions = []
    last_question = 0
    for i in questions_json:
        questions = i["questions"]
        for question in questions:
            question["question_number"] = last_question+1
            last_question += 1
            formatted_questions.append(question)
    print(len(formatted_questions))
    #Ik its a mess, i am too lazy to find and change questions_json to  formatted_questions everywhere
    questions_json = formatted_questions 
    logger.info(f"questions_json: {questions_json}")
    logger.info("Verifying answers for given questions...")
    incorrect_questions = []
    for i, question in enumerate(questions_json):
        system_prompt= get_verification_system_prompt()
        logger.info(f"Verifying question {i}")
        try:
            options = question["options"]
            prompt = get_verification_prompt(question=question["question"], options=options)
            result, model_choice = model_inference("verification", system_prompt=system_prompt, prompt=prompt, response_format="json_object", reasoning_effort="low")
            logger.info(f"result: {result}")
            if result['answer'].lower() != question['answer'].lower(): # ik we can use a loop here, bur who will do so much work?
                # confirm answer is incorrect by verifying the question again
                result2, model_choice2 = model_inference("verification", system_prompt=system_prompt, prompt=prompt, response_format="json_object", reasoning_effort="low")
                if result2['answer'].lower() == question['answer'].lower():
                    incorrect_questions.append({
                        "question_index": i,
                        "question": question,
                        "correct_answer": result['answer'],
                        "solution": [result['solution'], result2['solution']],
                        "models_used": [model_choice, model_choice2]
                    })
        except Exception as e:
            logger.error(f"Error verifying question {i} : {e}")
            incorrect_questions.append({
                "question_index": i,
                "question": question,
                "correct_answer": result['answer'],
                "solution": None,
                "models_used": None
            })
    # Save incorrect questions if any
    if incorrect_questions:
        lesson_name = os.path.splitext(os.path.basename(pdf_path))[0]
        base_folder = "lessons10" if class_num == 10 else "lessons"
        subject_lower = subject.lower()

        incorrect_file = os.path.join(
            base_dir,
            "data",
            "incorrect_questions",
            base_folder,
            subject_lower,
            f"incorrect_{lesson_name}.json"
        )
        os.makedirs(os.path.dirname(incorrect_file), exist_ok=True)

        with open(incorrect_file, 'w') as f:
            json.dump(incorrect_questions, f, indent=2)

        # Remove incorrect questions from main list
        correct_questions = [q for i, q in enumerate(questions_json)
                           if i not in [ic['question_index'] for ic in incorrect_questions]]
        questions_json = correct_questions

    # Save final questions with proper directory structure
    lesson_name = os.path.splitext(os.path.basename(pdf_path))[0]
    base_folder = "lessons10" if class_num == 10 else "lessons"
    subject_lower = subject.lower()

    # Format filename based on subject
    if subject == "Science":
        filename = f"lesson-{lesson_name}.json"
    elif subject == "Math":
        filename = f"lesson{lesson_name}.json"
    elif subject == "SS":
        # For SS files, lesson_name should already be in format "prefix.number"
        filename = f"{lesson_name}.json"
    else:
        filename = f"lesson{lesson_name}.json"

    output_file = os.path.join(
        base_dir,
        "data",
        base_folder,
        subject_lower,
        filename
    )
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(questions_json, f, indent=2)

    # After successfully saving questions, update lessons.json
    if questions_json:  # Only update if questions were successfully generated
        update_lessons_json(subject, lesson_name, class_num)

    return output_file


def process_directory(directory_path):
    """Process all PDFs in a directory structure"""
    try:
        # Dictionary to store question counts for each PDF
        question_counts = {}

        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_path = os.path.join(root, file)

                    # Extract class and subject from path
                    path_parts = root.split(os.sep)
                    try:
                        class_num = int(path_parts[-2])
                        subject = path_parts[-1]
                    except (IndexError, ValueError) as e:
                        logger.error(f"Invalid directory structure for {pdf_path}: {str(e)}\n{traceback.format_exc()}")
                        continue

                    # Check if corresponding JSON file already exists
                    lesson_name = os.path.splitext(os.path.basename(pdf_path))[0]
                    base_folder = "lessons10" if class_num == 10 else "lessons"
                    subject_lower = subject.lower()

                    # Format filename based on subject
                    if subject == "Science":
                        filename = f"lesson-{lesson_name}.json"
                    elif subject == "Math":
                        filename = f"lesson{lesson_name}.json"
                    elif subject == "SS":
                        # For SS files, lesson_name should already be in format "prefix.number"
                        filename = f"{lesson_name}.json"
                    else:
                        filename = f"lesson{lesson_name}.json"

                    json_file = os.path.join(
                        base_dir,
                        "data",
                        base_folder,
                        subject_lower,
                        filename
                    )

                    if os.path.exists(json_file):
                        logger.info(f"{lesson_name} is skipped")
                        # Add the count from existing JSON file
                        try:
                            with open(json_file, 'r') as f:
                                questions = json.load(f)
                                question_counts[pdf_path] = len(questions)
                        except Exception as e:
                            logger.error(f"Error counting questions in existing {json_file}: {str(e)}")
                            question_counts[pdf_path] = 0
                        continue

                    logger.info(f"Processing {pdf_path}")
                    output_file = process_pdf(pdf_path, subject, class_num)
                    if output_file:
                        logger.info(f"Generated questions saved to {output_file}")
                        # Read the output file to count questions
                        try:
                            with open(output_file, 'r') as f:
                                questions = json.load(f)
                                question_counts[pdf_path] = len(questions)
                        except Exception as e:
                            logger.error(f"Error counting questions in {output_file}: {str(e)}")
                            question_counts[pdf_path] = 0
                    else:
                        logger.error(f"Failed to process {pdf_path}")
                        question_counts[pdf_path] = 0

        # Save question counts to numbers.json
        numbers_file = os.path.join(base_dir, 'numbers.json')
        try:
            with open(numbers_file, 'w') as f:
                json.dump(question_counts, f, indent=2)
            logger.info(f"Question counts saved to {numbers_file}")
        except Exception as e:
            logger.error(f"Error saving question counts: {str(e)}\n{traceback.format_exc()}")

    except Exception as e:
        logger.error(f"Error processing directory {directory_path}: {str(e)}\n{traceback.format_exc()}")

def validate_pdf_structure(base_dir):
    """
    Validate the PDF directory structure and return any issues found.
    Skips directories that don't contain PDFs.
    """
    issues = []
    valid_structure = False

    # Check if pdfs directory exists
    pdfs_dir = os.path.join(base_dir, 'pdfs')
    if not os.path.exists(pdfs_dir):
        issues.append("❌ 'pdfs' directory not found in the workspace")
        issues.append("ℹ️ Create a 'pdfs' directory in your workspace")
        return False, issues

    # Expected structure
    expected_classes = ['9', '10']
    expected_subjects = ['Math', 'Science', 'SS']

    # Check class directories
    class_dirs = [d for d in os.listdir(pdfs_dir) if os.path.isdir(os.path.join(pdfs_dir, d))]
    if not class_dirs:
        issues.append("❌ No class directories found in 'pdfs' directory")
        issues.append("ℹ️ Create directories '9' and '10' inside 'pdfs' directory")
    else:
        for expected_class in expected_classes:
            if (expected_class not in class_dirs):
                issues.append(f"❌ Class directory '{expected_class}' not found")
                issues.append(f"ℹ️ Create directory '{expected_class}' inside 'pdfs' directory")
            else:
                # Check subject directories
                class_path = os.path.join(pdfs_dir, expected_class)
                subject_dirs = [d for d in os.listdir(class_path) if os.path.isdir(os.path.join(class_path, d))]

                if not subject_dirs:
                    issues.append(f"❌ No subject directories found in 'pdfs/{expected_class}'")
                    issues.append(f"ℹ️ Create subject directories (Math, Science, SS) inside 'pdfs/{expected_class}'")
                else:
                    for expected_subject in expected_subjects:
                        if expected_subject not in subject_dirs:
                            issues.append(f"❌ Subject directory '{expected_subject}' not found in 'pdfs/{expected_class}'")
                            issues.append(f"ℹ️ Create directory '{expected_subject}' inside 'pdfs/{expected_class}'")

    # Structure is valid if all required directories exist (regardless of PDF presence)
    valid_structure = len(issues) == 0

    # Add setup instructions if there are issues
    if not valid_structure:
        issues.append("\nTo set up the correct directory structure:")
        issues.append("1. Create a 'pdfs' directory in your workspace")
        issues.append("2. Inside 'pdfs', create directories '9' and '10'")
        issues.append("3. Inside each class directory, create subject directories:")
        issues.append("   - Math")
        issues.append("   - Science")
        issues.append("   - SS")
        issues.append("4. Add your PDF files to the appropriate subject directories")
        issues.append("\nExample valid path: pdfs/9/Math/1.pdf")

    return valid_structure, issues

if __name__ == "__main__":
    try:
        # base_dir is already defined at module level
        print(f"Using base directory: {base_dir}")
        # Validate PDF directory structure
        valid_structure, issues = validate_pdf_structure(base_dir)
        print(valid_structure)
        if not valid_structure:
            print("""
❌ Invalid PDF Structure Found!

📚 PDF Placement Guide 📚
========================

Place your PDF files in the following structure:

workspace/
└── pdfs/
    ├── 9/
    │   ├── Math/         <- Put class 9 Math PDFs here
    │   ├── Science/      <- Put class 9 Science PDFs here
    │   └── SS/           <- Put class 9 Social Studies PDFs here
    └── 10/
        ├── Math/         <- Put class 10 Math PDFs here
        ├── Science/      <- Put class 10 Science PDFs here
        └── SS/           <- Put class 10 Social Studies PDFs here

Example valid paths:
- pdfs/9/Math/chapter1.pdf
- pdfs/10/Science/lesson2.pdf
- pdfs/9/SS/e.1.pdf

Note: For SS (Social Studies) PDFs:
- Use format: e.1.pdf, e.2.pdf for Economics
- Use format: c.1.pdf, c.2.pdf for Civics
- Use format: g.1.pdf, g.2.pdf for Geography
- Use format: h.1.pdf, h.2.pdf for History

Issues Found:
""")
            for issue in issues:
                print(issue)
            sys.exit(1)

        print("✅ PDF directory structure is valid")
        print("Processing PDFs...")

        # Process the pdfs directory
        pdfs_dir = os.path.join(base_dir, 'pdfs')
        process_directory(pdfs_dir)

    except Exception as e:
        logger.error(f"Main execution error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)
