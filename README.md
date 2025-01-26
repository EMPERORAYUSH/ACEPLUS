
# AcePlus - AI-Powered Exam Preparation Platform

AcePlus is a cutting-edge web application designed to revolutionize exam preparation for students. Leveraging the power of Artificial Intelligence, AcePlus provides a personalized and efficient learning experience, helping students excel in their studies.


## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Environment Setup](#environment-setup)
  - [Adding Students and Teachers](#adding-students-and-teachers)
  - [Adding Lessons using PDFs](#adding-lessons-using-pdfs)
- [Contributing](#contributing)


## Features

AcePlus boasts a wide array of features designed to enhance the learning process:

-   **Smart Exam Creation:**
    -   Generate customized exams tailored to specific subjects and lessons.
    -   Adjust the number of questions based on the number of selected lessons.
    -   Automatic generation of unique exam IDs for easy tracking.
    -   Ability for teachers to create and assign tests to students.
    -   Image-to-question conversion: Upload images of questions and let the AI create exam questions from them.
-   **AI-Powered Analysis:**
    -   Receive detailed performance analysis after each exam, including overall score, percentage, and subject-wise breakdown.
    -   Identify strongest and weakest areas based on exam results.
    -   Get personalized, actionable feedback generated by AI, focusing on specific topics and concepts that need attention.
    -   Access AI-generated solutions for incorrect answers, explaining the correct approach and breaking down problem-solving steps.
-   **Subject-wise Performance Tracking:**
    -   Monitor progress across different subjects (Math, Science, Social Studies, English).
    -   View detailed statistics, including:
        -   Total exams attempted
        -   Average percentage
        -   Marks gained vs. marks attempted
        -   Highest and lowest marks in each subject
    -   Analyze performance trends over time to identify areas for improvement.
-   **Monthly Leaderboard:**
    -   Engage in friendly competition with peers within your division.
    -   Track your monthly ranking based on a comprehensive ELO scoring system, which considers exam scores, difficulty, and subject weights.
    -   Motivate yourself to climb the leaderboard and achieve academic excellence.
-   **User-Friendly Interface:**
    -   Intuitive navigation with a sidebar for easy access to different sections.
    -   Responsive design optimized for both desktop and mobile devices.
    -   Clear and concise presentation of information for a seamless user experience.
-   **Secure Authentication:**
    -   Robust login system to protect user data and ensure privacy.
    -   JWT (JSON Web Tokens) for secure authentication and authorization.
-   **Exam History:**
    -   Review past exam attempts and track your progress over time.
    -   Access detailed results, including scores, percentages, and AI-generated feedback for each exam.
    -   Filter exams by subject and sort them by date.
-   **Test Series:**
    -   Access a curated collection of practice tests created by teachers.
    -   Take tests within a specific time frame to simulate exam conditions.
    -   Get immediate feedback and detailed analysis after completing a test.
-   **Teacher Tools:**
    -   Dedicated section for teachers to manage test series.
    -   Ability to generate tests with customized subject, lessons, and difficulty.
    -   Option to specify the class (9th or 10th) for which the test is intended.
    -   Automatic assignment of unique test IDs.
-   **Error Handling and Reporting:**
    -   Robust error handling to provide informative messages to users in case of issues.
    -   Option for users to report incorrect or problematic questions for review.
-   **Continuous Updates:**
    -   Regular updates with new features, improvements, and bug fixes.
-   **Performance Optimization:**
    -   Optimized for fast loading times and smooth performance.
    -   Efficient data fetching and caching strategies to minimize latency.

## Installation

### Prerequisites

Before installing AcePlus, ensure you have the following installed:

- Python 3.8 or higher
- Node.js 18.x or higher and npm

### Setup Instructions

To install and set up AcePlus, follow these steps:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/EMPERORAYUSH/ACEPLUS.git
    cd ACEPLUS
    ```

2. **Setup backend & Install backend dependencies:**

    ```bash
    npm run setup
    ```
    
    This will install all required Python packages listed in `requirements.txt` & create files nessasry for script to run.

3. **Install frontend dependencies:**

    ```bash
    npm install
    ```

## Usage

### Running the Application

1. **Start the backend server:**

    ```bash
    npm run start-backend
    ```

    This will start the Flask development server, typically on port 9027.

2. **Start the frontend development server:**

    ```bash
    npm start
    ```

    This will start the React development server, on port 3000.

3. **Access the application:**

    Open your web browser and go to `http://localhost:3000`.

### Environment Setup

AcePlus uses environment variables to manage configuration. Here's how to set them up:
1. **Backend Environment:**

    -   In the `backend` directory, locate the `.env.example` file
    -   Make a copy of `.env.example` and rename it to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and configure the following sections:

        1. **MongoDB Configuration:**
        ```bash
        MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?appName=<app>
        MONGODB_DB_CLASS9=student_database
        MONGODB_DB_CLASS10=student_database_class10
        ```

        2. **Flask Configuration:**
        ```bash
        FLASK_SECRET_KEY=your_secret_key          # Required for security
        FLASK_PORT=9027                           # Default port
        FLASK_HOST=0.0.0.0                        # Default host
        FLASK_DEBUG=False                         # Set True for development
        ```

        3. **AI Provider Configuration:**
        ```bash
        # Example for Cerebras:
        CEREBRAS_API_KEY=your_cerebras_api_key
        CEREBRAS_BASE_URL=https://api.cerebras.ai/v1
        CEREBRAS_MODELS=["llama-3.1-70b", "llama-3.3-70b"]

        # Example for Gemini:
        GEMINI_API_KEY=your_gemini_api_key
        GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
        ```

        4. **Model Selection:**
        ```bash
        IMAGE_MODEL_PROVIDER=GEMINI              # Provider for image processing
        IMAGE_MODEL=gemini-exp-1206              # Specific model to use
        
        PERFORMANCE_MODEL_PROVIDER=GEMINI        # Provider for performance tasks
        PERFORMANCE_MODEL=gemini-2.0-flash-exp   # Specific model to use
        ```

    **Note:** Replace all placeholder values (like `your_secret_key`, `your_gemini_api_key`, etc.) with your actual configuration. You only need to configure the AI providers you plan to use.
### Adding Students and Teachers

#### **Student Data:**

Student data is stored in JSON files within the `backend/data` directory (visible after running [Backend Setup](#backend-setup)).

-   `students.json`: Contains data for Class 9 students.
-   `class10_students.json`: Contains data for Class 10 students.

Each file contains a JSON object where:

-   **Keys:** are the student's GR Number (e.g., "1234").
-   **Values:** are objects with the following structure:

```json
{
  "name": "Student Name",
  "roll": 25,
  "div": "A"
}
```

**To add a new student:**

1. Open the appropriate JSON file (`students.json` or `class10_students.json`).
2. Add a new key-value pair with the student's GR number as the key and their details as the value.

**Example:**

```json
{
  "1234": {
    "name": "John Doe",
    "roll": 25,
    "div": "A"
  }
}
```

#### **Teacher Data:**

Teacher data is stored in the `teachers.json` file within the `backend/data` directory.

It's a JSON object where:

-   **Keys:** are the teacher's ID (e.g., "0001").
-   **Values:** are objects with the following structure:

```json
{
  "name": "Teacher Name",
  "subject": "Mathematics",
  "standard": [9, 10],
  "division": "A"
}
```

**To add a new teacher:**

1. Open `teachers.json`.
2. Add a new key-value pair with the teacher's ID as the key and their details as the value.

**Example:**

```json
{
  "0001": {
    "name": "Jane Smith",
    "subject": "Science",
    "standard": [9],
    "division": "B"
  }
}
```

**Important Notes:**

-   Ensure that the JSON format is strictly followed.
-   The application needs to be restarted for changes to these files to take effect.
-   Division should be one of: A, B, C, D, E.
-   Standard should be an array containing either 9, 10 or both.
-   Subject should be one of: Math, Science, English, SS.

### Adding Lessons using PDFs

AcePlus allows you to add lessons using PDF files. Here's how the process works:

1. **PDF Structure:**
    -   Place your PDF files in the `backend/pdfs` directory.
    -   Organize them into subfolders based on class and subject. The structure should follow this pattern:
    ```
    pdfs/
    ├── 9/
    │   ├── Math/
    │   ├── Science/
    │   └── SS/
    └── 10/
        ├── Math/
        ├── Science/
        └── SS/
    ```

2. **Naming Conventions:**
    -   **Science:** `lesson-{number}.pdf` (e.g., `lesson-1.pdf`, `lesson-2.pdf`)
    -   **Math:** `lesson{number}.pdf` (e.g., `lesson1.pdf`, `lesson2.pdf`)
    -   **Social Studies (SS):** `{prefix}.{number}.pdf` where the prefix is:
        -   `e` for Economics (e.g., `e.1.pdf`)
        -   `c` for Civics (e.g., `c.1.pdf`)
        -   `g` for Geography (e.g., `g.1.pdf`)
        -   `h` for History (e.g., `h.1.pdf`)

3. **Running the PDF Processing Script:**
    -   Navigate to the `backend/processing` directory: `cd backend/processing`
    -   Run the `pdf_to_questions.py` script: `python pdf_to_questions.py`
    -   This script will:
        1. Validate the PDF directory structure.
        2. Process each PDF using the configured AI model (Gemini).
        3. Extract questions, options, and answers from the PDFs.
        4. Format the extracted data into JSON.
        5. Save the generated questions in the `backend/data/lessons` (for Class 9) or `backend/data/lessons10` (for Class 10) directory, organized by subject.
        6. Create a `lessons.json` (or `lessons10.json`) file in `backend/data` that lists the available lessons for each subject.
        7. Store any incorrect questions (identified by the verification process) in the `backend/data/incorrect_questions` directory.
    
    **Important Notes:**
    -   Ensure that you have set up the environment variables correctly. Refer to the [Environment Setup](#environment-setup) section for configuration details.
    -   The processing script may take a significant amount of time depending on the number and size of the PDFs.
    -   The script will skip lessons that have already been processed (based on the existence of the corresponding JSON file).
    -   New lessons will be automatically visible in the frontend without requiring a restart.


## Contributing

Contributions to AcePlus are welcome! If you'd like to contribute, please follow these guidelines:

1. **Fork the repository.**
2. **Create a new branch** for your feature or bug fix: `git checkout -b feature/your-feature-name` or `git checkout -b bugfix/your-bugfix-name`.
3. **Make your changes** and commit them with clear, descriptive commit messages.
4. **Push your branch** to your forked repository: `git push origin your-branch-name`.
5. **Open a pull request** to the `main` branch of the original repository.

