import random
import json
from openai import OpenAI
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import base64
from dotenv import load_dotenv
import ast
import traceback
from typing import Dict, List, Tuple

# Load environment variables
load_dotenv()

def validate_env_config() -> List[str]:
    """
    Validate all required environment variables before initializing any clients.
    Returns a list of valid provider names.
    Raises ValueError if any required configuration is missing or invalid.
    """
    valid_providers = []
    env_vars = os.environ

    # Find all potential providers by looking for *_API_KEY pattern
    for key in env_vars:
        if key.endswith('_API_KEY'):
            provider = key.replace('_API_KEY', '')
            if provider:
                # Validate base URL exists
                base_url = os.getenv(f'{provider}_BASE_URL')
                if not base_url:
                    raise ValueError(f"Missing base URL for provider: {provider}")

                # Validate models configuration
                models_str = os.getenv(f'{provider}_MODELS')
                if not models_str:
                    raise ValueError(f"Missing models configuration for provider: {provider}")

                try:
                    models = ast.literal_eval(models_str)
                    if not isinstance(models, list) or not models:
                        raise ValueError(f"Invalid models configuration for provider: {provider}")
                except Exception as e:
                    raise ValueError(f"Error parsing models for provider {provider}: {str(e)}")

                # Check additional keys if they exist
                i = 2
                while True:
                    key = f"{provider}_API_KEY_{i}"
                    base_url_key = f"{provider}_BASE_URL_{i}"
                    
                    api_key = os.getenv(key)
                    base_url = os.getenv(base_url_key)
                    
                    # Break if no more keys found
                    if not api_key:
                        break
                    
                    # Validate base URL exists for additional key
                    if not base_url:
                        raise ValueError(f"Missing base URL for API key: {key}")
                    
                    i += 1

                valid_providers.append(provider)

    if not valid_providers:
        raise ValueError("No valid API providers found. Please check your environment variables.")

    # Validate specific use case configurations
    image_provider = os.getenv('IMAGE_MODEL_PROVIDER', '').upper()
    image_model = os.getenv('IMAGE_MODEL')
    if not image_provider or not image_model:
        raise ValueError("IMAGE_MODEL_PROVIDER and IMAGE_MODEL must be configured")
    if image_provider not in valid_providers:
        raise ValueError(f"IMAGE_MODEL_PROVIDER '{image_provider}' is not a valid provider")

    perf_provider = os.getenv('PERFORMANCE_MODEL_PROVIDER', '').upper()
    perf_model = os.getenv('PERFORMANCE_MODEL')
    if not perf_provider or not perf_model:
        raise ValueError("PERFORMANCE_MODEL_PROVIDER and PERFORMANCE_MODEL must be configured")
    if perf_provider not in valid_providers:
        raise ValueError(f"PERFORMANCE_MODEL_PROVIDER '{perf_provider}' is not a valid provider")

    return valid_providers

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
    prompt = f"""As an expert tutor, help a student understand a problem they got wrong. You have:

        1. The original question
        2. The correct answer
        3. The student's incorrect answer

        Create a response that:

        1. Explains why the correct answer is right
        2. Breaks down the problem-solving steps
        3. Provides helpful context
        4. Uses LaTeX for:
           - Mathematical expressions and equations (e.g. $x^2$, \\frac{1}{2})
           - Scientific formulas (e.g. $H_2O$, $CO_2$)
           - Physical quantities and units (e.g. $9.8 \\text{{ m/s}}^2$)
           - Chemical equations (e.g. $2H_2 + O_2 \\rightarrow 2H_2O$)

        Use simple language and be encouraging. Here's the information:

        Question: {question}
        Correct Answer: {correct_answer}
        Student's Answer: {given_answer}
        provided options: {options}
        
        Provide a detailed explanation based on this. Make sure to use LaTeX notation for all mathematical and scientific expressions."""

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


def shuffle_question_options(questions):
    """
    Shuffle the options of each question while maintaining the correct answer.
    Assertion reason questions will not have their options shuffled.

    Args:
        questions (list): List of question dictionaries

    Returns:
        list: Questions with shuffled options
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
    prompt = f"""Analyze my exam performance and provide specific, actionable feedback.

    Format your response using these exact sections and formatting rules:

    ### Performance Overview
    • Start with a brief overview of overall performance
    • Include the score: {correct_answers}/{total_questions} ({percentage:.1f}%)
    • Mention strongest and weakest areas based on actual results

    Results : {result}

    ### Topic Analysis 
    For each topic where mistakes were made:
    • Topic name: Number of mistakes
      * Specific concept that needs attention
      * Common misconception identified
      * Example of type of question that caused difficulty

    ### Focus Areas
    List specific topics to practice, in order of priority:
    • Topic 1
      * Sub-concept to focus on
      * Specific type of problems to practice
    • Topic 2
      * Sub-concept to focus on
      * Specific type of problems to practice

    ### Next Steps
    3-4 specific, actionable steps based on their performance in these exact topics:
    • Step 1: [Topic-specific action]
    • Step 2: [Topic-specific action]
    • Step 3: [Topic-specific action]

    Reference these lessons in your analysis: {', '.join(lesson_names)}

    Important:
    - Identify topics from the questions to give better feedback
    - Don't give generic study tips
    - Focus on the specific topics where mistakes were made
    - Provide concrete examples based on the actual mistakes
    - Keep formatting consistent with the above structure
    - Use bullet points (•) for main points and (*) for sub-points
    """

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


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_single_image(image_path, client):
    """Analyze a single image and extract questions"""
    try:
        # Read image and encode to base64
        image_base64 = encode_image_to_base64(image_path)
        
        prompt = """You are a model that analyses a given image containing MCQ questions and identifies the question and 4 options and an answer which will be tick marked upon. Answer in json only with this format:

        [
        {
        "question":"",
        "options":{"a":"",...},
        "answer":"a/b/c/d" 
        }
        ]

        Question would be generally in bold text but not always.
        If no question is found, return an empty list!
        If no option is tick marked, return empty string for answer.
        If options are not found, do not include the question in the response.
        """

        chat_completion = client.chat.completions.create(
            model="gemini-1.5-pro",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text", 
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2048,
            temperature=0.1,
            timeout=90  # 90 second timeout per image
        )
        
        # Clean up any markdown code block indicators from the response
        response_text = chat_completion.choices[0].message.content.strip()
        response_text = response_text.replace('```json', '').replace('```', '')
        
        try:
            questions = json.loads(response_text)
            return questions if isinstance(questions, list) else []
        except json.JSONDecodeError:
            print(f"Error parsing response for {image_path}")
            return []
            
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return []


# XML parsing helpers
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

# Prompt for image analysis
prompt = """Analyze these images containing MCQ questions. Output your response in XML format with the following structure:

<response>
<total_questions>number</total_questions>
<questions>
  <question>
    <question_text>The question text here</question_text>
    <a>Option A text</a>
    <b>Option B text</b>
    <c>Option C text</c>
    <d>Option D text</d>
    <answer>a/b/c/d</answer>
  </question>
  <!-- More questions -->
</questions>
</response>

Use LaTeX formatting with $ delimiters for:
1. All mathematical expressions and equations (e.g. $x^2 + y^2 = z^2$)
2. Chemical formulas and equations (e.g. $H_2SO_4$, $2H_2 + O_2 \rightarrow 2H_2O$)
3. Scientific notations (e.g. $3.6 \\times 10^{-19}$)
4. Units with superscripts/subscripts (e.g. $m/s^2$, $cm^3$)
5. Greek letters (e.g. $\alpha$, $\beta$, $\theta$)
6. Special mathematical symbols (e.g. $\pm$, $\div$, $\leq$)
7. Fractions (e.g. $\frac{1}{2}$)
8. Square roots (e.g. $\sqrt{2}$)
9. Vector notations (e.g. $\vec{F}$)
10. Degree symbols (e.g. $45°$ as $45^\circ$)

Important rules:
1. Always output valid XML with proper opening and closing tags
2. Include total_questions before the questions list
3. Each question must have question_text and all four options (a,b,c,d)
4. If no answer is marked, use empty answer tag: <answer></answer>
5. For tables, use markdown table syntax within the question_text
6. For sub-options like (i), (ii), etc., include them in the question_text
7. Include any source info like [NCERT Exemplar] at the end of question_text

For questions with tables:
1. Format tables using markdown table syntax with | for columns and - for headers
2. Example table format:
   | Header1 | Header2 |
   |---------|---------|
   | Cell1   | Cell2   |
3. Include the formatted table as part of the question_text
4. Preserve table alignment and spacing
5. Use LaTeX formatting within table cells where applicable

Remember to maintain proper LaTeX spacing and use proper LaTeX commands for mathematical operations.
For example:
- Use \\times for multiplication instead of x
- Use \\cdot for dot multiplication
- Use proper spacing in equations with \\ when needed
- Use \\text{} for text within math mode
- Escape special characters properly
"""

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
        content = [{"type": "text", "text": prompt}]
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
                
                print(f"\nCurrent buffer content: {response_buffer}\n")

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
                        print(f"Added question: {question_data['question']}")
                        yield {"type": "progress", "count": len(question_list)}
                    
                    # Remove processed question from buffer
                    response_buffer = response_buffer[question_end:]

        print("\nFinal response from model:")
        print(full_response)
        print(f"\nExtracted questions: {len(question_list)}")

        # If no questions were extracted, try one final parse
        if not question_list and full_response:
            print("No questions were extracted from the response")
            print("Attempting one final parse of the complete response...")
            
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
