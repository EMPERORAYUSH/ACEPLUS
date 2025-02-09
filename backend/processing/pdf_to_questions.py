import os
import json
import base64
import google.generativeai as genai
from openai import OpenAI
import logging
import traceback
from dotenv import load_dotenv
import time
import random
import sys

# Get the script's directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configure logging with detailed format including tracebacks
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.FileHandler(os.path.join(SCRIPT_DIR, 'app.log'))  # File handler
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure API clients
GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY is required")

# Configure Gemini
genai.configure(
    api_key=GOOGLE_API_KEY,
    transport="rest"  # Use REST transport for better stability with large requests
)

# Initialize model with default settings
DEFAULT_GENERATION_CONFIG = {
    "temperature": 0.7,
    "candidate_count": 1,
    "max_output_tokens": 8192
}

DEFAULT_REQUEST_OPTIONS = {
    "timeout": 300,  # 5 minutes timeout
    "retry_strategy": "adaptive"
}

CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CEREBRAS_BASE_URL = os.getenv('CEREBRAS_BASE_URL')
if not CEREBRAS_API_KEY or not CEREBRAS_BASE_URL:
    raise ValueError("CEREBRAS_API_KEY and CEREBRAS_BASE_URL are required")

# Initialize Cerebras client
cerebras_client = OpenAI(
    base_url=CEREBRAS_BASE_URL,
    api_key=CEREBRAS_API_KEY,
)

# Initialize Groq client only if credentials are provided
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_BASE_URL = os.getenv('GROQ_BASE_URL')
groq_client = None
if GROQ_API_KEY and GROQ_BASE_URL:
    groq_client = OpenAI(
        base_url=GROQ_BASE_URL,
        api_key=GROQ_API_KEY
    )
    logger.info("Groq client initialized successfully")
else:
    logger.info("Groq client not initialized (optional)")

# Special instructions for specific lessons
LESSON_SPECIAL_INSTRUCTIONS = {
    "ss/e.1": "Do not give any attention to Notes for the teacher page",
    "ss/e.2": "Do not give any attention to Notes for the teacher page",
    "ss/e.3": "Do not give any attention to Notes for the teacher page",
    "ss/e.4": "Do not give any attention to Notes for the teacher page. Only include questions to the topics: 'What is Globalization?', 'Factors that have enabled Globalisation'. Do not include questions from any other topic!"
    # Add more special messages for other lessons as needed
}

def load_lessons_data(class10=False):
    """Load lessons data from the appropriate JSON file"""
    try:
        filename = "lessons10.json" if class10 else "lessons.json"
        file_path = os.path.join(base_dir, "data", filename)
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading lessons data: {str(e)}\n{traceback.format_exc()}")
        return None

def lesson2filepath(subject, lesson, class10=False):
    subject_lower = subject.lower()
    # Add class10 folder prefix if needed
    base_folder = "lessons10" if class10 else "lessons"

    if subject == "SS":
        # For SS, lesson format is like "C: Lesson-1" or "E: Lesson-1"
        prefix, lesson_num = lesson.split(":")  # Split into prefix (C/E/G/H) and lesson number
        lesson_num = lesson_num.strip().split("-")[1]  # Get the number after "Lesson-"
        prefix_lower = prefix.lower().strip()
        return os.path.join(
            base_dir,
            base_folder,
            subject_lower,
            f"{prefix_lower}.{lesson_num}.json"
        )
    elif subject == "Science":
        lesson_number = lesson.split()[-1]
        return os.path.join(
            base_dir,
            base_folder, subject_lower, f"lesson-{lesson_number}.json"
        )
    elif subject == "Math":
        lesson_number = lesson.split()[-1]
        return os.path.join(
            base_dir,
            base_folder, subject_lower, f"lesson{lesson_number}.json"
        )
    else:
        lesson_number = lesson.split()[-1]
        return os.path.join(
            base_dir,
            base_folder, subject_lower, f"lesson{lesson_number}.json"
        )

def is_lesson_processed(subject, lesson_name, class_num):
    """Check if a lesson is already processed based on subject-specific formats"""
    lessons_data = load_lessons_data(class_num == 10)
    if not lessons_data or subject not in lessons_data:
        return False

    # Get lesson name without extension
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

def get_subject_prompt(subject, class_num):
    """Get the appropriate prompt based on subject and class"""
    if subject.lower() == "math":
        return f"""Generate challenging questions for CBSE NCERT Class {class_num} Math based on the given lesson. Create exactly 50 questions covering:
1. Knowledge-based direct questions (15 questions)
2. Problem-solving questions (15 questions)
3. Application-based questions (10 questions)
4. Critical thinking questions (10 questions)

Make options confusing and avoid using questions directly from the textbook.
Include such type of questions that are asked in board exams or have come recently in previous year board examinations.
After writing each question, write its answer too.

IMPORTANT RULES:
- NO diagrams or visual references allowed
- ALL questions MUST be MCQ type with EXACTLY 4 options
- NO sub-questions allowed
- Make options challenging and confusing
- Distribute answers evenly across A, B, C, and D
- Questions should be solvable without diagrams
- Include step-by-step solutions where appropriate

Start generating questions immediately without any introductory text."""

    elif subject.lower() == "science":
        return f"""Create challenging questions for CBSE NCERT Class {class_num} Science based on the given lesson. Generate exactly 50 questions including:
1. Knowledge-based MCQs (15 questions)
2. Problem-solving questions (15 questions)
3. Application-based questions (10 questions)
4. Critical thinking questions (10 questions)

IMPORTANT RULES:
- ALL questions MUST be MCQ type with EXACTLY 4 options
- NO diagrams or visual references allowed
- NO sub-questions allowed
- Make options challenging and confusing
- Distribute answers evenly across A, B, C, and D
- Questions should be solvable without diagrams
- Include step-by-step solutions where appropriate
- Focus on board exam style questions
- Include numerical problems for physics topics

Start generating questions immediately without any introductory text."""

    else:  # Social Studies
        return f"""Create challenging questions for CBSE NCERT Class {class_num} Social Studies based on the given lesson. Generate exactly 50 questions including:
1. Knowledge-based MCQs (15 questions)
2. Case-based questions with paragraphs (15 questions, one question per paragraph)
3. Application-based questions (10 questions)
4. Critical thinking questions (10 questions)

IMPORTANT RULES:
- ALL questions MUST be MCQ type with EXACTLY 4 options
- NO diagrams or visual references allowed
- NO sub-questions allowed
- Make options challenging and confusing
- Distribute answers evenly across A, B, C, and D
- For case-based questions, include a short paragraph followed by ONE question only
- Focus on board exam style questions
- Include analytical and interpretative questions
- You MUST include answer for each and every question.
Start generating questions immediately without any introductory text."""

def get_lesson_key(subject, lesson_name):
    """Generate the key for looking up special instructions"""
    subject_lower = subject.lower()
    # Remove file extension if present
    lesson_base = os.path.splitext(lesson_name)[0]
    return f"{subject_lower}/{lesson_base}"

def try_alternate_model(current_model, system_prompt, prompt, cerebras_client, groq_client):
    """Helper function to try alternate models in sequence"""
    # Build list of available models
    models = ['cerebras', 'gemini']
    if groq_client:
        models.append('groq')
        
    # Remove current model from list and shuffle the remaining
    models.remove(current_model)
    random.shuffle(models)
    
    for model in models:
        try:
            if model == 'cerebras':
                response = cerebras_client.chat.completions.create(
                    model="llama-3.3-70b",
                    messages=[
                        {"role": "system", "content": system_prompt} if system_prompt else {"role": "system", "content": "You are a precise JSON formatter."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                return 'cerebras', response.choices[0].message.content
            elif model == 'groq' and groq_client:
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt} if system_prompt else {"role": "system", "content": "You are a precise JSON formatter."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                return 'groq', response.choices[0].message.content
            else:  # gemini
                model = genai.GenerativeModel('gemini-exp-1206')
                response = model.generate_content(
                    [system_prompt, prompt] if system_prompt else prompt,
                    generation_config={"temperature": 0.1},
                    request_options={"timeout": 300}
                )
                return 'gemini', response.text
        except Exception as e:
            logger.error(f"{model} model failed: {str(e)}")
            continue
    return None, None

def validate_questions_format(questions_str, cerebras_client):
    """Validate questions format and distribution using available models"""
    system_prompt = """
    You are a format validator. Check both FORMAT and QUESTION TYPE DISTRIBUTION requirements:

    Format requirements:
    1. Each question must have exactly 4 options (a, b, c, d) ((A), (B), (C), (D) is also fine)
    2. Each question must have an answer field with value a, b, c, or d ((A), (B), (C), (D) is also fine) 
    3. Each question must be a single question (no sub-questions)
    4. No diagrams or visual references

    DO NOT:
    - Judge if answers are correct
    - Evaluate question quality
    - Suggest content improvements
    - Check if options make sense

    Here are examples of valid and invalid formats:

    Valid format example:
    Q1. What is the capital of France?
    a) London
    b) Berlin
    c) Paris
    d) Madrid
    Answer: c

    Q1. The rise of nationalism in India during the early 20th century was closely linked to economic policies of the British. The drain of wealth from India to Britain through heavy taxation, unfair trade practices, and exploitation of raw materials led to widespread poverty. This economic exploitation helped unite Indians across religious and regional differences as they realized the need to achieve independence. The swadeshi movement, which promoted the use of Indian-made goods, became a powerful expression of economic nationalism.
    a) The British taxation system helped India's economic growth
    b) Economic exploitation by the British strengthened the nationalist movement
    c) The swadeshi movement promoted the use of British goods
    d) Nationalism in India was unrelated to economic factors
    Answer: b


    Invalid format examples:

    Missing option:
    Q1. What is the capital of France?
    a) London
    b) Berlin
    c) Paris
    Answer: c

    Invalid answer format:
    Q1. What is the capital of France?
    a) London
    b) Berlin
    c) Paris
    d) Madrid
    Answer: Paris

    Contains sub-questions:
    Q1. Consider the following:
    i) What is the capital of France?
    ii) What is the capital of Germany?
    a) Paris, Berlin
    b) London, Paris
    c) Berlin, Madrid
    d) Madrid, London
    Answer: a

    Contains diagram reference:
    Q1. In the diagram above, what is the value of angle x?
    a) 30°
    b) 45°
    c) 60°
    d) 90°
    Answer: b

    Does not contain answer:
    Q1. What is the capital of France?
    a) London
    b) Berlin
    c) Paris
    d) Madrid

    Question distribution requirements:
    1. Knowledge-based direct questions: 15 questions
    2. Problem-solving questions (or case-based questions): 15 questions 
    3. Application-based questions: 10 questions
    4. Critical thinking questions : 10 questions
    Total required: 50 questions

    Identify both format issues and distribution issues in your response.
    """

    prompt = f"""Analyze these questions and provide a JSON response with format and distribution issues:
{{
    "total_questions": number,
    "format_issues": [
        {{
            "question_number": number,
            "issue": "format/structure issues like: missing options, invalid answer format, contains sub-questions, etc.",
            "needs_rewrite": boolean
        }}
    ],
    "distribution": {{
        "knowledge_based": number,
        "problem_solving": number,
        "application_based": number,
        "critical_thinking": number
    }},
    "distribution_issues": [
        {{
            "type": "question type (e.g., knowledge_based)",
            "current": number,
            "required": number,
            "missing": number
        }}
    ],
    "is_valid": boolean (true if no format or distribution issues found)
}}

Questions to analyze:
{questions_str}"""

    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Build list of available models for first attempt
            available_models = ['cerebras', 'gemini']
            if groq_client:
                available_models.append('groq')
                
            # Randomly choose from available models
            model_choice = random.choice(available_models)
            logger.info(f"First attempt using {model_choice} for validation")
            
            try:
                if model_choice == 'cerebras':
                    response = cerebras_client.chat.completions.create(
                        model="llama-3.3-70b",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content
                elif model_choice == 'groq' and groq_client:
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content
                else:  # gemini
                    model = genai.GenerativeModel('gemini-exp-1206')
                    response = model.generate_content(
                        [system_prompt, prompt],
                        generation_config={"temperature": 0.1},
                        request_options={"timeout": 300}
                    )
                    content = response.text
                
                # Clean up the response
                content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error with {model_choice}: {str(je)}")
                    logger.error(f"Raw response content that caused error:\n{content}")
                    raise  # Re-raise to trigger alternate model attempt
                    
            except Exception as e:
                logger.error(f"First model failed, trying alternate models after delay: {str(e)}")
                time.sleep(60)  # Wait 1 minute before trying alternate models
                
                # Try alternate models
                model_used, content = try_alternate_model(model_choice, system_prompt, prompt, cerebras_client, groq_client)
                if model_used and content:
                    # Clean up and parse the response
                    content = content.replace("```json", "").replace("```", "").strip()
                    return json.loads(content)
                else:
                    logger.error("All models failed for validation")
                    retry_count += 1
                    if retry_count == max_retries:
                        return None
                    logger.info(f"Retrying attempt {retry_count} of {max_retries}")
                    time.sleep(60)  # Wait another minute before next attempt
                    continue
                
        except Exception as e:
            logger.error(f"Error in validation loop: {str(e)}")
            retry_count += 1
            if retry_count == max_retries:
                return None
            logger.info(f"Retrying attempt {retry_count} of {max_retries}")
            time.sleep(60)
            continue

def format_questions_as_json(questions_str, cerebras_client):
    """Format questions into JSON using available models"""
    example_format = """[
    {
        "question": "What is the value of x in the equation 2x + 5 = 15?",
        "options": {
            "a": "5",
            "b": "10",
            "c": "15",
            "d": "20"
        },
        "answer": "a"
    }
]"""

    prompt = f"""Format these questions into JSON following this exact format:
{example_format}

Questions to format:
{questions_str}"""

    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Build list of available models for first attempt
            available_models = ['cerebras', 'gemini']
            if groq_client:
                available_models.append('groq')
                
            # Randomly choose from available models
            model_choice = random.choice(available_models)
            logger.info(f"First attempt using {model_choice} for formatting")
            
            try:
                if model_choice == 'cerebras':
                    response = cerebras_client.chat.completions.create(
                        model="llama-3.1-70b",
                        messages=[
                            {"role": "system", "content": "You are a precise JSON formatter."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content
                elif model_choice == 'groq' and groq_client:
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are a precise JSON formatter."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content
                else:  # gemini
                    model = genai.GenerativeModel('gemini-exp-1206')
                    response = model.generate_content(
                        prompt,
                        generation_config={"temperature": 0.1},
                        request_options={"timeout": 300}
                    )
                    content = response.text
                
                # Clean up the response
                content = content.replace("```json", "").replace("```", "").strip()
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError as je:
                    logger.error(f"JSON decode error with {model_choice}: {str(je)}")
                    logger.error(f"Raw response content that caused error:\n{content}")
                    raise  # Re-raise to trigger alternate model attempt
                    
            except Exception as e:
                logger.error(f"First model failed, trying alternate models after delay: {str(e)}")
                time.sleep(60)  # Wait 1 minute before trying alternate models
                
                # Try alternate models
                model_used, content = try_alternate_model(model_choice, None, prompt, cerebras_client, groq_client)
                if model_used and content:
                    # Clean up and parse the response
                    content = content.replace("```json", "").replace("```", "").strip()
                    return json.loads(content)
                else:
                    logger.error("All models failed for formatting")
                    retry_count += 1
                    if retry_count == max_retries:
                        return None
                    logger.info(f"Retrying attempt {retry_count} of {max_retries}")
                    time.sleep(60)  # Wait another minute before next attempt
                    continue
                
        except Exception as e:
            logger.error(f"Error in formatting loop: {str(e)}")
            retry_count += 1
            if retry_count == max_retries:
                return None
            logger.info(f"Retrying attempt {retry_count} of {max_retries}")
            time.sleep(60)
            continue

def verify_with_cerebras(question, options, answer):
    """Verify a question using Cerebras LLaMA model"""
    prompt = f"""Solve this question and verify if the given answer is correct:

Question: {question}
Options:
A) {options['a']}
B) {options['b']}
C) {options['c']}
D) {options['d']}

Respond in this exact JSON format:
{{
    "solution": "detailed step-by-step solution",
    "answer": "correct answer letter (a/b/c/d)",
}}"""

    response = cerebras_client.chat.completions.create(
        model="llama-3.3-70b",
        messages=[
            {"role": "system", "content": "You are a precise question solver and verifier."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    response_content = response.choices[0].message.content
    response_content = response_content.replace("```json", "").replace("```", "").strip()
    logger.info(f"Cerebras verification response:\n{response_content}")
    
    return json.loads(response_content)

def verify_with_gemini(question, options, answer):
    """Verify a question using Google's Gemini model"""
    # Randomly choose between Gemini 1.5 Flash and 2.0 Flash
    model_name = random.choice(['gemini-1.5-flash', 'gemini-2.0-flash-exp'])
    model = genai.GenerativeModel(model_name)
    
    prompt = f"""Solve this question and verify if the given answer is correct:

Question: {question}
Options:
A) {options['a']}
B) {options['b']}
C) {options['c']}
D) {options['d']}

Respond in this exact JSON format:
{{
    "solution": "detailed step-by-step solution",
    "answer": "correct answer letter (a/b/c/d)",
}}"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0.2, "response_mime_type": "application/json"}
    )
    
    logger.info(f"Gemini ({model_name}) verification response:\n{response.text}")
    return json.loads(response.text)

def verify_with_groq(question, options, answer):
    """Verify a question using Groq's LLaMA model"""
    if not groq_client:
        raise ValueError("Groq client not initialized")
        
    prompt = f"""Solve this question and verify if the given answer is correct:

Question: {question}
Options:
A) {options['a']}
B) {options['b']}
C) {options['c']}
D) {options['d']}

Respond in this exact JSON format:
{{
    "solution": "detailed step-by-step solution",
    "answer": "correct answer letter (a/b/c/d)",
}}"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a precise question solver and verifier."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    response_content = response.choices[0].message.content
    response_content = response_content.replace("```json", "").replace("```", "").strip()
    logger.info(f"Groq verification response:\n{response_content}")
    
    return json.loads(response_content)

def request_additional_questions(pdf_data, missing_types, subject, class_num, previous_questions):
    """Request additional questions for missing types"""
    model = genai.GenerativeModel('gemini-exp-1206')
    
    # Create prompt for specific missing question types
    prompt = f"""Based on the PDF content and existing questions, generate additional questions.

Current questions for reference:
{previous_questions}

Required additional questions:
"""
    for qtype, count in missing_types.items():
        if count > 0:
            prompt += f"- {count} more {qtype.replace('_', ' ')} questions\n"
    
    prompt += """
Important:
1. Do not duplicate or rephrase existing questions
2. Maintain same level of difficulty and style as existing questions
3. Follow the same format as existing questions
4. Questions should be unique and test different concepts
5. Ensure new questions complement existing ones"""
    
    try:
        response = model.generate_content(
            [
                {'mime_type': 'application/pdf', 'data': pdf_data},
                prompt
            ],
            generation_config=DEFAULT_GENERATION_CONFIG,
            request_options={"timeout": 900}
        )
        
        additional_questions = ""
        for chunk in response:
            if chunk.text:
                additional_questions += chunk.text
        
        return additional_questions
    except Exception as e:
        logger.error(f"Error generating additional questions: {str(e)}")
        return None

def update_lessons_json(subject, lesson_name, class_num):
    """
    Update the appropriate lessons.json file with a new lesson.
    
    Args:
        subject (str): Subject name (Math, Science, or SS)
        lesson_name (str): Name of the lesson
        class_num (int): Class number (9 or 10)
    """
    try:
        # Determine which lessons file to update
        filename = "lessons10.json" if class_num == 10 else "lessons.json"
        file_path = os.path.join(base_dir, "data", filename)
        
        # Load current lessons data
        with open(file_path, 'r') as f:
            lessons_data = json.load(f)
            
        # Format lesson name based on subject
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
            
        # Add lesson if not already present
        if subject not in lessons_data:
            lessons_data[subject] = []
            
        if formatted_name not in lessons_data[subject]:
            lessons_data[subject].append(formatted_name)
            # Sort lessons
            if subject == "SS":
                # Sort SS lessons by prefix and then number
                lessons_data[subject].sort(key=lambda x: (x.split(':')[0], int(x.split('-')[1])))
            else:
                # Sort other subjects by lesson number
                lessons_data[subject].sort(key=lambda x: int(x.split()[-1]))
            
            # Save updated data
            with open(file_path, 'w') as f:
                json.dump(lessons_data, f, indent=2)
                
            logger.info(f"Added {formatted_name} to {subject} in {filename}")
            
    except Exception as e:
        logger.error(f"Error updating lessons JSON: {str(e)}\n{traceback.format_exc()}")

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Define base_dir at module level

def process_pdf(pdf_path, subject, class_num):
    """Process a PDF file and generate questions"""
    # Check if lesson is already processed
    lesson_name = os.path.splitext(os.path.basename(pdf_path))[0]
    if is_lesson_processed(subject, lesson_name, class_num):
        logger.info(f"Lesson {lesson_name} already processed for {subject} Class {class_num}")
        return None

    try:
        # Read and encode the PDF file
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = base64.standard_b64encode(pdf_file.read()).decode("utf-8")
        
        logger.info(f"Successfully encoded file {lesson_name}")

        # Initialize Gemini model
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                model = genai.GenerativeModel('gemini-exp-1206')
                base_prompt = get_subject_prompt(subject, class_num)
                
                # Create content list with PDF and base prompt
                content_list = [
                    {'mime_type': 'application/pdf', 'data': pdf_data},
                    base_prompt
                ]
                
                # Add special instructions if they exist
                lesson_key = get_lesson_key(subject, lesson_name)
                if lesson_key in LESSON_SPECIAL_INSTRUCTIONS:
                    logger.info(f"Adding special instructions for {lesson_key}")
                    content_list.append(LESSON_SPECIAL_INSTRUCTIONS[lesson_key])

                # Generate questions with streaming
                response = model.generate_content(
                    content_list,
                    generation_config=DEFAULT_GENERATION_CONFIG,
                    request_options={"timeout": 900}
                )
                break
            except Exception as e:
                logger.error(f"Error generating questions: {e}")
                retry_count += 1
                if retry_count == max_retries:
                    return None
                logger.info(f"Retrying attempt {retry_count} of {max_retries}")
                time.sleep(60)
                continue

        # Collect streamed response
        questions_str = ""
        try:
            for chunk in response:
                if chunk.text:
                    questions_str += chunk.text
            
            # Validate questions format and distribution
            validation = validate_questions_format(questions_str, cerebras_client)
            if validation is None:
                logger.error("Question validation failed. Check previous logs for details.")
                return None
            
            logger.info(f"Initial validation result:\n{json.dumps(validation, indent=2)}")
            
            # Request additional questions if needed based on distribution issues
            if not validation['is_valid']:
                distribution_fixes_needed = validation.get('distribution_issues', [])
                if distribution_fixes_needed:
                    logger.info("Requesting additional questions for missing types")
                    missing_types = {
                        issue['type']: issue['missing']
                        for issue in distribution_fixes_needed
                    }
                    additional_questions = request_additional_questions(
                        pdf_data,
                        missing_types,
                        subject,
                        class_num,
                        questions_str
                    )
                    
                    if additional_questions:
                        questions_str += "\n" + additional_questions
                        # Revalidate after adding questions
                        validation = validate_questions_format(questions_str, cerebras_client)
                        logger.info(f"Validation after adding questions:\n{json.dumps(validation, indent=2)}")
            
            # Log the complete generated questions for debugging
            logger.info(f"Generated questions from PDF:\n{questions_str}")
            
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            if questions_str:
                logger.info(f"Partial results before error:\n{questions_str}")
                logger.info("Proceeding with partial results")
            else:
                raise  # Re-raise if we got no content at all

        # Handle any remaining format issues
        if not validation['is_valid']:
            format_fixes_needed = [issue for issue in validation['format_issues'] if issue['needs_rewrite']]
            if format_fixes_needed:
                fix_prompt = "Please fix the following format issues in these questions:\n"
                for fix in format_fixes_needed:
                    fix_prompt += f"- Question {fix['question_number']}: {fix['issue']}\n"
                
                # Generate fixes with streaming
                max_retries = 3
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        response = model.generate_content(
                            [
                                {'mime_type': 'application/pdf', 'data': pdf_data},
                                fix_prompt
                            ],
                            generation_config=DEFAULT_GENERATION_CONFIG,
                            request_options={"timeout": 900}
                        )
                        break
                    except Exception as e:
                        logger.error(f"Error generating fixes: {e}")
                        retry_count += 1
                        if retry_count == max_retries:
                            return None
                        logger.info(f"Retrying attempt {retry_count} of {max_retries}")
                        time.sleep(60)
                        continue
                
                fixed_questions = ""
                for chunk in response:
                    if chunk.text:
                        fixed_questions += chunk.text
                
                # Use fixed questions
                questions_str = fixed_questions
                
                # Final validation
                validation = validate_questions_format(questions_str, cerebras_client)
                if validation is None or not validation['is_valid']:
                    logger.error("Questions still invalid after fixes. Check logs for details.")
                    if validation:
                        logger.error(f"Final validation result:\n{json.dumps(validation, indent=2)}")
                    return None
                
                logger.info(f"Fixed questions:\n{questions_str}")
                logger.info(f"Final distribution:\n{json.dumps(validation['distribution'], indent=2)}")

        # Format questions as JSON
        questions_json = format_questions_as_json(questions_str, cerebras_client)
        if questions_json is None:
            logger.error("Question formatting failed. Check previous logs for details.")
            return None

        # Verify answers using randomly selected model
        incorrect_questions = []
        for i, question in enumerate(questions_json):
            max_retries = 3
            retry_delay = 60  # 1 minute in seconds
            
            for attempt in range(max_retries):
                try:
                    # Randomly choose between all three models
                    model_choice = random.choice(['cerebras', 'gemini', 'groq'])
                    logger.info(f"First attempt using {model_choice} for question {i+1}")
                    
                    try:
                        if model_choice == 'cerebras':
                            result = verify_with_cerebras(
                                question['question'],
                                question['options'],
                                question['answer']
                            )
                        elif model_choice == 'groq' and groq_client:
                            result = verify_with_groq(
                                question['question'],
                                question['options'],
                                question['answer']
                            )
                        else:  # gemini
                            result = verify_with_gemini(
                                question['question'],
                                question['options'],
                                question['answer']
                            )
                            
                        if result['answer'].lower() != question['answer'].lower():
                            incorrect_questions.append({
                                "question_index": i,
                                "question": question,
                                "correct_answer": result['answer'],
                                "solution": result['solution'],
                                "model_used": model_choice
                            })
                        break  # Success - exit retry loop
                        
                    except Exception as e:
                        logger.error(f"First model failed, trying alternate models after delay: {str(e)}")
                        time.sleep(60)  # Wait 1 minute before trying alternate models
                        
                        # Try alternate models in random order
                        models = ['cerebras', 'gemini', 'groq']
                        models.remove(model_choice)
                        random.shuffle(models)
                        
                        success = False
                        for alt_model in models:
                            try:
                                if alt_model == 'cerebras':
                                    result = verify_with_cerebras(
                                        question['question'],
                                        question['options'],
                                        question['answer']
                                    )
                                elif alt_model == 'groq' and groq_client:
                                    result = verify_with_groq(
                                        question['question'],
                                        question['options'],
                                        question['answer']
                                    )
                                else:  # gemini
                                    result = verify_with_gemini(
                                        question['question'],
                                        question['options'],
                                        question['answer']
                                    )
                                    
                                if result['answer'].lower() != question['answer'].lower():
                                    incorrect_questions.append({
                                        "question_index": i,
                                        "question": question,
                                        "correct_answer": result['answer'],
                                        "solution": result['solution'],
                                        "model_used": alt_model
                                    })
                                success = True
                                break  # Found a working model
                                
                            except Exception as e2:
                                logger.error(f"{alt_model} model failed: {str(e2)}")
                                continue
                                
                        if success:
                            break  # Exit retry loop if any model succeeded
                        else:
                            logger.error("All models failed for this question")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                            else:
                                continue  # Skip this question after all retries fail
                    
                except Exception as e:
                    logger.error(f"Error verifying question {i} (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        continue  # Skip this question after all retries fail
        
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

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}\n{traceback.format_exc()}")
        return None

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