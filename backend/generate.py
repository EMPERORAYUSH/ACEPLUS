import random
import json
from openai import OpenAI
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import ast
import traceback
from typing import Dict, List, Tuple
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
    
)
from utils.validate_env import validate_env_config

# Load environment variables
load_dotenv()

# Validate environment configuration
valid_providers = validate_env_config()

def get_provider_configs() -> Dict[str, Dict]:
    """
    Get configurations for validated providers.
    Returns a dictionary of provider configurations with their API keys and base URLs.
    """
    providers = {}
    
    # Process each validated provider
    for provider in valid_providers:
        base_keys = []
        base_urls = []
        
        # Get the first key and URL
        api_key = os.getenv(f'{provider}_API_KEY')
        base_url = os.getenv(f'{provider}_BASE_URL')
        base_keys.append(api_key)
        base_urls.append(base_url)
        
        # Get additional keys if they exist
        i = 2
        while True:
            key = f"{provider}_API_KEY_{i}"
            base_url_key = f"{provider}_BASE_URL_{i}"
            
            api_key = os.getenv(key)
            base_url = os.getenv(base_url_key)
            
            if not api_key or not base_url:
                break
                
            base_keys.append(api_key)
            base_urls.append(base_url)
            i += 1

        # Get models (already validated)
        models = ast.literal_eval(os.getenv(f'{provider}_MODELS'))
        
        # Store configuration
        providers[provider] = {
            'keys': list(zip(base_keys, base_urls)),
            'models': models
        }

    return providers

# Configure OpenAI clients
clients = {}
provider_configs = get_provider_configs()

# Initialize clients for each provider and key
for provider, config in provider_configs.items():
    for i, (api_key, base_url) in enumerate(config['keys'], 1):
        client_key = f"{provider.lower()}{i}" if len(config['keys']) > 1 else provider.lower()
        try:
            # Create OpenAI client with only required parameters
            clients[client_key] = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            print(f"Successfully initialized client for {provider} key {i}")
        except Exception as e:
            print(f"Error initializing client for {provider} key {i}: {str(e)}")

# Model configurations
MODEL_CONFIGS = {
    provider.lower(): config['models']
    for provider, config in provider_configs.items()
}

# Get validated model providers and models
IMAGE_MODEL_PROVIDER = os.getenv('IMAGE_MODEL_PROVIDER', '').upper()
IMAGE_MODEL = os.getenv('IMAGE_MODEL')
PERFORMANCE_MODEL_PROVIDER = os.getenv('PERFORMANCE_MODEL_PROVIDER', '').upper()
PERFORMANCE_MODEL = os.getenv('PERFORMANCE_MODEL')

def get_provider_clients(provider: str) -> List[Tuple[str, OpenAI]]:
    """Get all clients for a specific provider."""
    provider = provider.lower()
    provider_clients = []
    
    # If single client
    if provider in clients:
        provider_clients.append((provider, clients[provider]))
    
    # If multiple clients
    i = 1
    while True:
        client_key = f"{provider}{i}"
        if client_key not in clients:
            break
        provider_clients.append((client_key, clients[client_key]))
        i += 1
    
    if not provider_clients:
        raise ValueError(f"No clients found for provider: {provider}")
    
    return provider_clients

def get_random_provider_client(provider: str) -> Tuple[str, OpenAI]:
    """Get a random client for a specific provider."""
    provider_clients = get_provider_clients(provider)
    return random.choice(provider_clients)

# Validate providers exist
try:
    image_clients = get_provider_clients(IMAGE_MODEL_PROVIDER)
except ValueError as e:
    raise ValueError(f"Invalid IMAGE_MODEL_PROVIDER: {str(e)}")

try:
    performance_clients = get_provider_clients(PERFORMANCE_MODEL_PROVIDER)
except ValueError as e:
    raise ValueError(f"Invalid PERFORMANCE_MODEL_PROVIDER: {str(e)}")

# Add at the top of the file with other global variables
user_question_history = {}  # Stores used question IDs per user

def get_random_client():
    """Get a random client from the available clients."""
    if not clients:
        raise ValueError("No API clients configured")
    return random.choice(list(clients.items()))

def generate_solution(question, correct_answer, given_answer, options, client, model_name):
    prompt = SOLUTION_GENERATION_PROMPT

    try:
        # Get model based on client type
        model = random.choice(MODEL_CONFIGS[model_name])
            
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Provide direct solutions without introductory phrases. Jump straight to the answer. Do not cheerup anyone in your responses. Dont use formatting like bold (**) etc.",
                },
                {"role": "user", "content": prompt},
            ],
            model=model,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise e

def process_question(question_data):
    """Helper function to process individual questions for parallel execution"""
    client_name, client = get_random_provider_client(IMAGE_MODEL_PROVIDER)
    return generate_solution(
        question_data["question"],
        question_data["correct_answer"],
        question_data["given_answer"],
        question_data["options"],
        client,
        client_name
    )


def generate_solutions_batch(questions_list):
    """
    Generate solutions for a batch of questions in parallel
    Each question in questions_list should be a dictionary with the format:
    {
        'question': 'question text',
        'correct_answer': 'correct answer',
        'given_answer': 'student answer',
        'options': {'A': 'option1', 'B': 'option2', ...}
    }
    """
    batch_size = 10
    solutions = []

    for i in range(0, len(questions_list), batch_size):
        batch = questions_list[i : i + batch_size]

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_question = {}
            for question in batch:
                # Try different clients if one fails
                available_clients = list(clients.keys())
                random.shuffle(available_clients)

                def try_with_client(client_name):
                    selected_client = clients[client_name]
                    return generate_solution(
                        question["question"],
                        question["correct_answer"],
                        question["given_answer"],
                        question["options"],
                        selected_client,
                        client_name,
                    )

                future = executor.submit(
                    lambda q: next(
                        (
                            try_with_client(client)
                            for client in available_clients
                            if True
                        ),
                        "Error: All clients failed",
                    ),
                    question,
                )
                future_to_question[future] = question

            # Collect results as they complete
            for future in as_completed(future_to_question):
                question = future_to_question[future]
                try:
                    solution = future.result()
                    solutions.append(
                        {"question": question["question"], "solution": solution}
                    )
                except Exception as e:
                    solutions.append(
                        {
                            "question": question["question"],
                            "solution": f"Error: {str(e)}",
                        }
                    )

    return solutions


def generate_exam_questions(subject, lesson_files, user_id):
    global user_question_history
    
    # Initialize user history if not exists
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

    # First, collect all available questions
    for lesson_index, file in enumerate(lesson_files, 1):
        try:
            questions = parse_questions_from_json(file)
            if not questions:  # Skip if no questions were loaded
                print(f"Warning: No questions loaded from {file}")
                continue
                
            questions = shuffle_question_options(questions)  # Shuffle options
            lesson_question_counts[lesson_index] = len(questions)
            for q_index, question in enumerate(questions, 1):
                question_id = f"L{lesson_index}Q{q_index}"
                all_questions[question_id] = question
                question["lesson"] = lesson_index
                question["l-id"] = question_id
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            continue

    if not all_questions:
        raise Exception("No valid questions could be loaded from any lesson file")

    # Remove previously used questions
    available_questions = {
        qid: q
        for qid, q in all_questions.items()
        if qid not in user_question_history[user_id]
    }
    
    # If we don't have enough questions, reset history for these lesson files
    if len(available_questions) < num_questions:
        print(
            f"Resetting question history for user {user_id} due to insufficient questions"
        )
        current_lesson_ids = set(all_questions.keys())
        user_question_history[user_id] = [
            qid
            for qid in user_question_history[user_id]
            if qid not in current_lesson_ids
        ]
        available_questions = all_questions

    # Calculate the number of questions to select from each lesson
    total_questions = sum(lesson_question_counts.values())
    questions_per_lesson = {
        lesson: int(round(count / total_questions * num_questions))
        for lesson, count in lesson_question_counts.items()
    }

    # Adjust the total number of questions if rounding caused a discrepancy
    total_selected = sum(questions_per_lesson.values())
    if total_selected < num_questions:
        questions_per_lesson[
            max(questions_per_lesson, key=questions_per_lesson.get)
        ] += num_questions - total_selected
    elif total_selected > num_questions:
        questions_per_lesson[
            max(questions_per_lesson, key=questions_per_lesson.get)
        ] -= total_selected - num_questions

    # Select questions from each lesson
    selected_questions = []
    for lesson, count in questions_per_lesson.items():
        lesson_questions = [
            q for q in available_questions.values() 
            if q["lesson"] == lesson
        ]
        selected = random.sample(lesson_questions, min(count, len(lesson_questions)))
        selected_questions.extend(selected)

    # Remove duplicates and replace them with new questions
    selected_questions = remove_duplicates_and_replace(selected_questions, available_questions)
    
    # Shuffle the final selection
    random.shuffle(selected_questions)
    
    # Update user history with final selected questions
    user_question_history[user_id].extend(q["l-id"] for q in selected_questions)

    # Final validation of questions
    valid_questions = [
        q for q in selected_questions
        if isinstance(q.get("options"), dict) and len(q["options"]) == 4
    ]

    return valid_questions


def generate_performance_analysis(results, lessons, is_class10):
    """
    Generate a performance analysis based on exam results and lessons.

    Args:
        results: List of question results including correctness and solutions
        lessons: List of lesson names the exam covered
        is_class10: Boolean indicating if this is for class 10

    Returns:
        str: AI-generated performance analysis
    """
    # Load lessons data
    lessons_file = "lessons10.json" if is_class10 else "lessons.json"
    with open(os.path.join("backend/data", lessons_file), "r") as f:
        all_lessons = json.load(f)

    # Format lesson names
    lesson_names = []
    for lesson in lessons:
        for subject, subject_lessons in all_lessons.items():
            if lesson in subject_lessons:
                lesson_names.append(f"{subject}: {lesson}")
                break

    # Calculate statistics
    total_questions = len(results)
    correct_answers = sum(1 for r in results if r["is_correct"])
    percentage = (correct_answers / total_questions) * 100
    
    # Format results into a string for analysis
    result = ""
    for r in results:
        result += f"Question: {r['question']}\n"
        result += f"Correct Answer: {r['correct_answer']}\n"
        result += f"Student's Answer: {r['selected_answer']}\n"
        result += f"Is Correct: {r['is_correct']}\n"
        if "solution" in r:
            result += f"Solution: {r['solution']}\n"
        result += "\n"

    # Create the prompt
    prompt = PERFORMANCE_ANALYSIS_PROMPT.format(
        correct_answers=correct_answers,
        total_questions=total_questions,
        percentage=percentage,
        result=result,
        lesson_names=', '.join(lesson_names)
    )

    try:
        client_name, client = get_random_provider_client(PERFORMANCE_MODEL_PROVIDER)
        print(f"Generating performance analysis using {client_name} client...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an experienced teacher providing constructive feedback on exam performance. Be specific, encouraging, and practical in your advice.",
                },
                {"role": "user", "content": prompt},
            ],
            model=PERFORMANCE_MODEL,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            stream=False,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating performance analysis with {PERFORMANCE_MODEL_PROVIDER}: {e}")
        return "Unable to generate performance analysis at this time."



# Prompt for image analysis

def analyze_images(image_paths):
    """
    Analyze multiple images containing MCQ questions using configured image model with streaming.
    Yields progress updates and returns a list of questions extracted from the images.
    """
    try:
        client_name, client = get_random_provider_client(IMAGE_MODEL_PROVIDER)

        # Prepare all images
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
                print(f"Error encoding image {path}: {e}")
                print(traceback.format_exc())
                continue

        if not image_contents:
            print("No valid images to process")
            yield {"type": "error", "message": "No valid images to process"}
            return

        # Combine prompt and all images in the content
        content = [{"type": "text", "text": IMAGE_ANALYSIS_PROMPT}]
        content.extend(image_contents)

        print(f"Processing {len(image_paths)} images using {client_name} client with streaming...")

        chat_completion = client.chat.completions.create(
            model=IMAGE_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=8192,
            temperature=0.1,
            timeout=120,
            stream=True
        )

        full_response = ""
        question_list = []
        total_questions_count = 0
        response_buffer = ""
        is_total_questions_extracted = False

        print("Starting to process streaming response...")

        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                full_response += chunk_content
                response_buffer += chunk_content
        
                # Try to extract total questions if not already done
                if not is_total_questions_extracted:
                    total_tag_content = extract_tag_content(response_buffer, "total_questions")
                    if total_tag_content:
                        try:
                            total_questions_count = int(total_tag_content)
                            is_total_questions_extracted = True
                            print(f"Successfully extracted total questions: {total_questions_count}")
                            yield {"type": "total", "count": total_questions_count}
                        except ValueError:
                            print(f"Invalid total_questions value: {total_tag_content}")

                # Try to extract complete questions
                while "<question>" in response_buffer and "</question>" in response_buffer:
                    question_start = response_buffer.find("<question>")
                    question_end = response_buffer.find("</question>") + len("</question>")
                    question_xml = response_buffer[question_start:question_end]
                    
                    # Parse the question
                    question_data = parse_question_xml(question_xml)
                    if question_data:
                        question_list.append(question_data)
                        yield {"type": "progress", "count": len(question_list)}
                    
                    # Remove processed question from buffer
                    response_buffer = response_buffer[question_end:]

        if not question_list and full_response:
            
            # Try to get total questions if not already done
            if not is_total_questions_extracted:
                total_tag_content = extract_tag_content(full_response, "total_questions")
                if total_tag_content:
                    try:
                        total_questions_count = int(total_tag_content)
                        yield {"type": "total", "count": total_questions_count}
                    except ValueError:
                        print(f"Invalid total_questions value: {total_tag_content}")

            # Extract all questions
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
                print(f"Successfully extracted {len(question_list)} questions from final parse")
                yield {"type": "progress", "count": len(question_list)}

        # If we never got a total_questions count, use the number of questions found
        if not is_total_questions_extracted and question_list:
            total_questions_count = len(question_list)
            yield {"type": "total", "count": total_questions_count}

        print(f"\nFound {len(question_list)} questions")
        # Send one final progress update before the result
        yield {"type": "progress", "count": len(question_list)}
        yield {"type": "result", "questions": question_list}

    except Exception as e:
        print(f"Error in analyze_images: {e}")
        print("Full error details:")
        print(traceback.format_exc())
        yield {"type": "error", "message": str(e)}


if __name__ == "__main__":
    pass
