import random
import json
from openai import OpenAI
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import traceback
from typing import Dict, Tuple
from utils.generate_utils import (
    encode_image_to_base64,
    extract_tag_content,
    parse_question_xml,
    shuffle_question_options,
    remove_duplicates_and_replace,
    parse_questions_from_json
)
from utils.prompts import (
    SOLUTION_GENERATION_PROMPT,
    PERFORMANCE_ANALYSIS_PROMPT,
    IMAGE_ANALYSIS_PROMPT,
    HINT_GENERATION_PROMPT,
)
from utils.validate_env import validate_env_config
from utils.parse_files import parse_any
import logging

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

# Validate environment configuration
valid_providers = validate_env_config()

def get_provider_config(provider: str) -> Dict[str, str]:
    """Get API key and base URL for a specific provider."""
    return {
        "api_key": os.getenv(f"{provider.upper()}_API_KEY"),
        "base_url": os.getenv(f"{provider.upper()}_BASE_URL"),
    }

def get_random_model(model_type: str) -> Tuple[str, str, bool]:
    """
    Selects a random model from the specified model type list in .env.
    Handles '::nothink' suffix to disable thinking.
    Example: model_type='IMAGE_MODELS'
    """
    models_str = os.getenv(model_type)
    if not models_str:
        raise ValueError(f"Model type '{model_type}' not found in environment variables.")
    
    models_list = json.loads(models_str)
    if not models_list:
        raise ValueError(f"No models configured for '{model_type}'.")
        
    model_full_name = random.choice(models_list)
    
    nothink_enabled = False
    if model_full_name.endswith("::nothink"):
        nothink_enabled = True
        model_full_name = model_full_name.removesuffix("::nothink")

    provider, model_name = model_full_name.split('/')
    return provider, model_name, nothink_enabled

def get_client_for_model(model_type: str) -> Tuple[OpenAI, str, bool]:
    """
    Gets a random model for the given type and returns an initialized client,
    the model name, and a flag indicating if 'nothink' is enabled.
    """
    provider, model_name, nothink_enabled = get_random_model(model_type)
    config = get_provider_config(provider)
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    return client, model_name, nothink_enabled

# Add at the top of the file with other global variables
user_question_history = {}  # Stores used question IDs per user

def generate_hint(question_text: str):
    """
    Generate a helpful hint for a given question without revealing the answer, streaming the output.
    Uses HINT_MODELS from the environment configuration.
    """
    try:
        client, model_name, nothink_enabled = get_client_for_model("HINT_MODELS")
        logging.debug(f"Using model for hints: {model_name}")

        prompt = HINT_GENERATION_PROMPT.format(question=question_text)
        
        params = {
            "messages": [{"role": "user", "content": prompt}],
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 512,
            "stream": True
        }

        if nothink_enabled:
            params['extra_body'] = {
                "extra_body":{
                "google": {
                    "thinking_config": {
                        "thinking_budget": 0
                    }
                }
            }
            }

        stream = client.chat.completions.create(**params)

        latex_buffer = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                latex_buffer += content
                while True:
                    inline_match = re.search(r'\$(.+?)\$', latex_buffer)
                    display_match = re.search(r'\$\$(.+?)\$\$', latex_buffer)
                    if inline_match:
                        yield " " + inline_match.group(0)
                        latex_buffer = latex_buffer.replace(inline_match.group(0), '', 1)
                    elif display_match:
                        yield " " + display_match.group(0)
                        latex_buffer = latex_buffer.replace(display_match.group(0), '', 1)
                    else:
                        break
                if not re.search(r'[\$]', latex_buffer):
                    yield latex_buffer
                    latex_buffer = ""
        if latex_buffer:
            yield latex_buffer
    except Exception as e:
        logging.error(f"Unable to generate hint: {e}")
        yield f"Unable to generate hint: {str(e)}"

def generate_solution_stream(question_text: str, correct_answer: str, given_answer: str, options: dict):
    """
    Generate a solution for a given question with streaming output.
    Uses SOLUTION_MODELS from the environment configuration.
    """
    try:
        client, model_name, nothink_enabled = get_client_for_model("SOLUTION_MODELS")
        logging.debug(f"Using model for solution streaming: {model_name}")

        prompt = SOLUTION_GENERATION_PROMPT.format(
            question=question_text,
            correct_answer=correct_answer,
            given_answer=given_answer,
            options=options
        )
        
        params = {
            "messages": [
                {
                    "role": "system",
                    "content": "Provide direct solutions without introductory phrases. Jump straight to the answer. Do not cheerup anyone in your responses. Dont use formatting like bold (**) etc.",
                },
                {"role": "user", "content": prompt}
            ],
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": True
        }

        if nothink_enabled:
            params['extra_body'] = {
                "extra_body":{
                "google": {
                    "thinking_config": {
                        "thinking_budget": 0
                    }
                }
            }
            }
        
        stream = client.chat.completions.create(**params)

        latex_buffer = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                latex_buffer += content
                while True:
                    inline_match = re.search(r'\$(.+?)\$', latex_buffer)
                    display_match = re.search(r'\$\$(.+?)\$\$', latex_buffer)
                    if inline_match:
                        yield " " + inline_match.group(0)
                        latex_buffer = latex_buffer.replace(inline_match.group(0), '', 1)
                    elif display_match:
                        yield " " + display_match.group(0)
                        latex_buffer = latex_buffer.replace(display_match.group(0), '', 1)
                    else:
                        break
                if not re.search(r'[\$]', latex_buffer):
                    yield latex_buffer
                    latex_buffer = ""
        if latex_buffer:
            yield latex_buffer
    except Exception as e:
        logging.error(f"Unable to generate solution: {e}")
        yield f"Unable to generate solution: {str(e)}"

def generate_solution(question, correct_answer, given_answer, options):
    """Generates a solution using a randomly selected solution model."""
    prompt = SOLUTION_GENERATION_PROMPT.format(
        question=question,
        correct_answer=correct_answer,
        given_answer=given_answer,
        options=options
    )
    try:
        client, model_name, nothink_enabled = get_client_for_model("SOLUTION_MODELS")
        logging.debug(f"Generating solution with {model_name}")
        
        params = {
            "messages": [
                {
                    "role": "system",
                    "content": "Provide direct solutions without introductory phrases. Jump straight to the answer.",
                },
                {"role": "user", "content": prompt},
            ],
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False,
        }

        if nothink_enabled:
            params['extra_body'] = {
                "extra_body":{
                "google": {
                    "thinking_config": {
                        "thinking_budget": 0
                    }
                }
            }
            }

        chat_completion = client.chat.completions.create(**params)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating solution with {model_name}: {e}")
        raise

def process_question(question_data):
    """Helper function to process individual questions for parallel execution"""
    return generate_solution(
        question_data["question"],
        question_data["correct_answer"],
        question_data["given_answer"],
        question_data["options"],
    )

def generate_solutions_batch(questions_list):
    """
    Generate solutions for a batch of questions in parallel.
    """
    solutions = []
    with ThreadPoolExecutor() as executor:
        future_to_question = {
            executor.submit(process_question, q): q for q in questions_list
        }
        for future in as_completed(future_to_question):
            question = future_to_question[future]
            try:
                solution = future.result()
                solutions.append({"question": question["question"], "solution": solution})
            except Exception as exc:
                solutions.append({"question": question["question"], "solution": f"Error: {exc}"})
    return solutions


def generate_exam_questions(subject, lesson_files, user_id):
    global user_question_history
    
    if user_id not in user_question_history:
        user_question_history[user_id] = []
    
    num_lessons = len(lesson_files)
    if num_lessons == 1:
        num_questions = 15
    elif num_lessons == 2:
        num_questions = 20
    elif num_lessons == 3:
        num_questions = 30
    elif num_lessons == 4:
        num_questions = 40
    else:
        num_questions = min(40 + (num_lessons - 4) * 10, 60)

    all_questions = {}
    lesson_question_counts = {}

    for lesson_index, file in enumerate(lesson_files, 1):
        try:
            questions = parse_questions_from_json(file)
            if not questions:
                logging.warning(f"No questions loaded from {file}")
                continue
                
            questions = shuffle_question_options(questions)
            lesson_question_counts[lesson_index] = len(questions)
            for q_index, question in enumerate(questions, 1):
                question_id = f"L{lesson_index}Q{q_index}"
                all_questions[question_id] = question
                question["lesson"] = lesson_index
                question["l-id"] = question_id
        except Exception as e:
            logging.error(f"Error processing file {file}: {e}")
            continue

    if not all_questions:
        raise Exception("No valid questions could be loaded from any lesson file")

    available_questions = {
        qid: q
        for qid, q in all_questions.items()
        if qid not in user_question_history[user_id]
    }
    
    if len(available_questions) < num_questions:
        logging.info(
            f"Resetting question history for user {user_id} due to insufficient questions"
        )
        current_lesson_ids = set(all_questions.keys())
        user_question_history[user_id] = [
            qid
            for qid in user_question_history[user_id]
            if qid not in current_lesson_ids
        ]
        available_questions = all_questions

    total_questions = sum(lesson_question_counts.values())
    questions_per_lesson = {
        lesson: int(round(count / total_questions * num_questions))
        for lesson, count in lesson_question_counts.items()
    }

    total_selected = sum(questions_per_lesson.values())
    if total_selected < num_questions:
        questions_per_lesson[
            max(questions_per_lesson, key=questions_per_lesson.get)
        ] += num_questions - total_selected
    elif total_selected > num_questions:
        questions_per_lesson[
            max(questions_per_lesson, key=questions_per_lesson.get)
        ] -= total_selected - num_questions

    selected_questions = []
    for lesson, count in questions_per_lesson.items():
        lesson_questions = [
            q for q in available_questions.values() 
            if q["lesson"] == lesson
        ]
        selected = random.sample(lesson_questions, min(count, len(lesson_questions)))
        selected_questions.extend(selected)

    selected_questions = remove_duplicates_and_replace(selected_questions, available_questions)
    
    random.shuffle(selected_questions)
    
    user_question_history[user_id].extend(q["l-id"] for q in selected_questions)

    valid_questions = [
        q for q in selected_questions
        if isinstance(q.get("options"), dict) and len(q["options"]) == 4
    ]

    return valid_questions


def generate_performance_analysis(results, lessons, is_class10):
    """
    Generate a performance analysis based on exam results and lessons.
    """
    lessons_file = "lessons10.json" if is_class10 else "lessons.json"
    with open(os.path.join("backend/data", lessons_file), "r") as f:
        all_lessons = json.load(f)

    lesson_names = []
    for lesson in lessons:
        for subject, subject_lessons in all_lessons.items():
            if lesson in subject_lessons:
                lesson_names.append(f"{subject}: {lesson}")
                break

    total_questions = len(results)
    correct_answers = sum(1 for r in results if r["is_correct"])
    percentage = (correct_answers / total_questions) * 100
    
    result = ""
    for r in results:
        result += f"Question: {r['question']}\n"
        result += f"Correct Answer: {r['correct_answer']}\n"
        result += f"Student's Answer: {r['selected_answer']}\n"
        result += f"Is Correct: {r['is_correct']}\n"
        if "solution" in r:
            result += f"Solution: {r['solution']}\n"
        result += "\n"

    prompt = PERFORMANCE_ANALYSIS_PROMPT.format(
        correct_answers=correct_answers,
        total_questions=total_questions,
        percentage=percentage,
        result=result,
        lesson_names=', '.join(lesson_names)
    )

    try:
        client, model_name, nothink_enabled = get_client_for_model("PERFORMANCE_ANALYSIS_MODELS")
        logging.info(f"Generating performance analysis using {model_name}...")
        
        params = {
            "messages": [
                {
                    "role": "system",
                    "content": "You are an experienced teacher providing constructive feedback on exam performance. Be specific, encouraging, and practical in your advice.",
                },
                {"role": "user", "content": prompt},
            ],
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": False,
        }

        if nothink_enabled:
            params['extra_body'] = {
                "extra_body":{
                "google": {
                    "thinking_config": {
                        "thinking_budget": 0
                    }
                }
            }
            }
        
        chat_completion = client.chat.completions.create(**params)
        return chat_completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error generating performance analysis: {e}")
        return "Unable to generate performance analysis at this time."


def analyze_files(file_paths):
    """
    Analyze a mixed list of files (images, PDFs, PPTX). Uses parse_any to extract:
      - text from PDFs/PPTX (fitz/python-pptx)
      - embedded images from PDFs/PPTX saved to upload_folder
      - pass-through of images
    Streams progress/events identical to analyze_images.
    """
    try:
        client, model_name, nothink_enabled = get_client_for_model("IMAGE_MODELS")

        aggregated_texts = []
        upload_folder = os.path.dirname(file_paths[0]) if file_paths else os.getcwd()
        collected_image_paths = []
        for p in file_paths:
            try:
                parsed = parse_any(p, upload_folder)
                t = (parsed.get("text") or "").strip()
                if t:
                    aggregated_texts.append(t)
                imgs = parsed.get("images") or []
                for ip in imgs:
                    if os.path.exists(ip):
                        collected_image_paths.append(ip)
            except Exception as e:
                logging.error(f"Error parsing file {p}: {e}")
                logging.debug(traceback.format_exc())
                continue
        image_paths = collected_image_paths

        image_contents = []
        for path in image_paths:
            try:
                image_base64 = encode_image_to_base64(path)
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                })
            except Exception as e:
                logging.error(f"Error encoding image {path}: {e}")
                logging.debug(traceback.format_exc())
                continue

        if not image_contents and not aggregated_texts:
            logging.warning("No content (text or images) to process")
            yield {"type": "error", "message": "No content (text or images) to process"}
            return

        content = [{"type": "text", "text": IMAGE_ANALYSIS_PROMPT}]
        if aggregated_texts:
            content.append({"type": "text", "text": "\n\n".join(aggregated_texts)})
        content.extend(image_contents)
        print(content)
        logging.info(f"Processing {len(file_paths)} files using {model_name} with streaming...")
        
        params = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "max_tokens": 65536,
            "temperature": 1,
            "timeout": 120,
            "stream": True
        }

        if nothink_enabled:
            params['extra_body'] = {
                "google": {
                    "thinking_config": {
                        "thinking_budget": 0
                    }
                }
            }

        chat_completion = client.chat.completions.create(**params)

        full_response = ""
        question_list = []
        total_questions_count = 0
        response_buffer = ""
        is_total_questions_extracted = False

        logging.info("Starting to process streaming response...")

        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                full_response += chunk_content
                response_buffer += chunk_content
        
                if not is_total_questions_extracted:
                    total_tag_content = extract_tag_content(response_buffer, "total_questions")
                    if total_tag_content:
                        try:
                            total_questions_count = int(total_tag_content)
                            is_total_questions_extracted = True
                            logging.info(f"Successfully extracted total questions: {total_questions_count}")
                            yield {"type": "total", "count": total_questions_count}
                        except ValueError:
                            logging.warning(f"Invalid total_questions value: {total_tag_content}")

                while "<question>" in response_buffer and "</question>" in response_buffer:
                    question_start = response_buffer.find("<question>")
                    question_end = response_buffer.find("</question>") + len("</question>")
                    question_xml = response_buffer[question_start:question_end]
                    
                    question_data = parse_question_xml(question_xml)
                    if question_data:
                        question_list.append(question_data)
                        yield {"type": "progress", "count": len(question_list)}
                    
                    response_buffer = response_buffer[question_end:]

        if not question_list and full_response:
            
            if not is_total_questions_extracted:
                total_tag_content = extract_tag_content(full_response, "total_questions")
                if total_tag_content:
                    try:
                        total_questions_count = int(total_tag_content)
                        yield {"type": "total", "count": total_questions_count}
                    except ValueError:
                        logging.warning(f"Invalid total_questions value: {total_tag_content}")

            current_pos = 0
            while True:
                question_start = full_response.find("<question>", current_pos)
                if question_start == -1:
                    break
                    
                question_end = full_response.find("</question>", question_start)
                if question_end == -1:
                    break
                    
                question_end += len("</question>")
                question_xml = full_response[question_start:question_end]
                
                question_data = parse_question_xml(question_xml)
                if question_data:
                    question_list.append(question_data)
                    
                current_pos = question_end

            if question_list:
                logging.info(f"Successfully extracted {len(question_list)} questions from final parse")
                yield {"type": "progress", "count": len(question_list)}

        if not is_total_questions_extracted and question_list:
            total_questions_count = len(question_list)
            yield {"type": "total", "count": total_questions_count}

        logging.info(f"\nFound {len(question_list)} questions")
        yield {"type": "progress", "count": len(question_list)}
        yield {"type": "result", "questions": question_list}

    except Exception as e:
        logging.error(f"Error in analyze_images: {e}")
        logging.debug(f"Full error details:\n{traceback.format_exc()}")
        yield {"type": "error", "message": str(e)}


if __name__ == "__main__":
    pass
