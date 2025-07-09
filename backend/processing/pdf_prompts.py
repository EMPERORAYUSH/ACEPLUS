common_instructions_mcq = """

**Your Core Task:** Generate Multiple Choice Questions (MCQs).

**Provided Material (for each task):**
*   You will be given a text document or lesson content for a specific chapter/topic, hereafter referred to 'the lesson'. This will be specific to Class {class_num} and the subject (Math, Science, or Social Studies) of the current task.

**General Instructions & Rules (Applicable to ALL subjects unless specified otherwise):**

1.  **Goal:** Your objective is to create exactly 50 distinct MCQs based *solely* on the information, concepts, principles, and problem-solving techniques presented within "the Lesson." Do not use any external knowledge or information not found in "the Lesson."
2.  **No Visuals:** No diagrams, graphs, images, maps (unless key features can be described textually for SS), chemical structures (unless describable by simple text formulas), or any other visual references are permitted in the questions or options. All questions must be solvable using textual information and subject-specific reasoning alone.
3.  **No Sub-questions:** Each question must be a single, standalone MCQ. Do not create questions with parts (a), (b), (c), etc.
4.  **Originality & Board Exam Relevance:**
    *   Formulate original questions. While concepts will be from "the Lesson," the specific wording and problem setup should not be a direct copy from any textbook examples, unless "the Lesson" *is* a list of textbook examples to be re-purposed. Aim to rephrase and present problems in a novel way.
    *   Ensure the style, complexity, and type of questions reflect those typically asked in CBSE board examinations, or those that have appeared in recent previous year board examinations, while adhering to the content of "the Lesson."
5.  **MCQ Options:**
    *   Each question MUST have EXACTLY 4 options: (A), (B), (C), and (D).
    *   Make options challenging and confusing. Distractors (incorrect options) should be plausible and potentially based on common misconceptions or slight, incorrect variations of correct information relevant to "the Lesson."
6.  **Answer Distribution:** After generating all  questions, review the "Correct Answer" for each. Strive to have the correct answers distributed as evenly as possible across options A, B, C, and D. For example, aim for approximately 12-13 questions with (A) as the answer, 12-13 for (B), and so on. Adjust your questions/options if the distribution is heavily skewed, without compromising question quality or correctness. Do this distribution in your thinking stage itself.
7.  **Output Format:**
    *   Start generating questions immediately without any introductory text other than what is specified for each question's structure.
    *   Provide the complete list of 130 generated questions sequentially.
    *   Ensure all information is derived *exclusively* from the provided "Lesson."

**Standard Structure for Each Question:**
*   `Question Number: [NUMBER]`
*   `Question Text: [Your formulated question text]`
*   `Options:`
    *   `(A) [Text for Option A]`
    *   `(B) [Text for Option B]`
    *   `(C) [Text for Option C]`
    *   `(D) [Text for Option D]`
*   `<explaination [Provide detailed step-by-step solution for problem-solving/numerical questions. For other types, provide a clear justification for the correct answer, referencing "the Lesson."] <explaination>` 
*   `Correct Answer: [Specify A, B, C, or D]`
Clearly mark heading before starting each category of questions and use '---' to separate question categories.
BEFORE BEGINNING EACH QUESTION CATEGORY, write category code for the category in json. like this : {{"category_code": "A"}}
Here are the category codes for each type of questions:
    - Knowledge-based Direct Questions: 'A'
    - Problem-solving Questions: 'B'
    - Application-based Questions: 'C'
    - Critical Thinking Questions: 'D'
    - Assertion and Reasoning Questions: 'E'

Always start question number of each category from 1

Explanation MUST start and end with <explaination> tag. ANY MISTAKE IN THIS IS UNACCEPTABLE!
Example of a correct question format:
```
Question Number: 1
Question Text: What is the primary function of the root system in a plant?
Options:
(A) To produce flowers and seeds
(B) To synthesize sunlight into energy
(C) To absorb water and nutrients from the soil
(D) To produce stems and leaves
 <explaination> The primary function of the root system in a plant is to absorb water and nutrients from the soil, which are then transported to the rest of the plant. This is essential for the plant's growth and survival. The roots also anchor the plant in the soil, providing stability. According to the Lesson on plant anatomy, roots are specialized to perform these critical functions, making option C the correct answer. <explaination>
Correct Answer: C
```
Think as much as you can
"""
category_codes = {
    "A": "Knowledge-based Direct Questions",
    "B": "Problem-solving Questions (or case-based questions)",
    "C": "Application-based Questions",
    "D": "Critical Thinking Questions",
    "E": "Assertion and Reasoning Questions"
}

math_specific_instructions = """
**Subject:** CBSE NCERT Class {class_num} Math
**Total Questions:** 120

**Question Distribution & Category Definitions:**

1.  **Knowledge-based Direct Questions (minimum 30 questions):**
    *   **Focus:** Definitions, formulas, theorems, properties, or direct factual information from "the Lesson."
    *   **Task:** Test direct recall or understanding.
    *   **Explanation/Solution:** Brief justification or restatement of the relevant fact/formula from "the Lesson."

2.  **Problem-solving Questions (minimum 30 questions):**
    *   **Focus:** Procedures, algorithms, or multi-step calculations (numerical or algebraic) taught in "the Lesson."
    *   **Task:** Require application of these procedures to arrive at a solution.
    *   **Explanation/Solution:** Provide a detailed, step-by-step solution demonstrating how to arrive at the correct answer using methods from "the Lesson."

3.  **Application-based Questions (minimum 20 questions):**
    *   **Focus:** Applying concepts from "the Lesson" to textually described real-world (simplified) or different mathematical contexts.
    *   **Task:** Identify the correct concept/formula and apply it to the given scenario.
    *   **Explanation/Solution:** Explain the application of the concept/formula and how the answer is derived.

4.  **Critical Thinking Questions (minimum 20 questions):**
    *   **Focus:** Deeper analysis, comparison, evaluation of statements, drawing non-obvious conclusions based on mathematical principles in "the Lesson."
    *   **Task:** Reason beyond direct recall or standard problem-solving (e.g., evaluate validity, identify assumptions, compare methods, determine effects of parameter changes).
    *   **Explanation/Solution:** Explain the critical reasoning process leading to the correct answer, referencing principles from "the Lesson."

5.  **Assertion and Reasoning Questions (minimum 20 questions):**
    *   **Focus:** Evaluating two statements - an Assertion (A) and a Reason (R) - both derived from mathematical concepts, definitions, theorems, properties, or problem-solving outcomes from "the Lesson." Questions test the understanding of the truthfulness of A and R and whether R is a correct explanation for A.
    *   **Task:** Create a minimum of `30` distinct Assertion-Reasoning (A/R) type questions. Each question must:
        *   Be based *solely* on the information presented within "the Lesson." Do not use external knowledge.
        *   Consist of an Assertion (A) and a Reason (R).
        *   Be accompanied by the four standard options:
            *   (A) Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).
            *   (B) Both Assertion (A) and Reason (R) are true, but Reason (R) is not the correct explanation of Assertion (A).
            *   (C) Assertion (A) is true, but Reason (R) is false.
            *   (D) Assertion (A) is false, but Reason (R) is true.
    *   **Explanation/Solution (for each A/R question):**
        1.  State the correct option (A, B, C, or D).
        2.  Provide a detailed analysis:
            *   Evaluate the truthfulness of Assertion (A) with justification from "the Lesson."
            *   Evaluate the truthfulness of Reason (R) with justification from "the Lesson."
            *   Explain why Reason (R) correctly explains Assertion (A) or not, leading to the chosen option.
        *   Ensure explanations are clear and questions are diverse and challenging.
"""

science_specific_instructions = """
**Subject:** CBSE NCERT Class {class_num} Science
**Total Questions:** 120

**Category Definitions:**

1.  **Knowledge-based MCQs (minimum 30 questions):**
    *   **Focus:** Core definitions, laws, principles, scientific facts, properties of substances, biological terms/processes, or chemical reactions explicitly stated in "the Lesson."
    *   **Task:** Test direct recall or understanding.
    *   **Explanation/Solution:** Brief justification or restatement of the relevant fact/principle from "the Lesson."

2.  **Problem-solving Questions (minimum 30 questions):**
    *   **Focus:** Quantitative relationships (formulas), stoichiometric calculations, or multi-step logical deductions based on scientific principles from "the Lesson."
    *   **Specifics:**
        *   For Physics topics: Include a significant portion of numerical problems requiring application of formulas. Provide necessary data textually.
        *   For Chemistry topics: Problems involving balancing equations (if textually describable), mole concept, stoichiometry, predicting products (if rules are given).
        *   For Biology topics: Problems involving genetic crosses (if concepts are textually describable), ecological calculations (e.g., energy flow if data is provided).
    *   **Explanation/Solution:** Provide a detailed, step-by-step solution, especially for numericals, showing calculations and application of formulas/principles from "the Lesson."

3.  **Application-based Questions (minimum 20 questions):**
    *   **Focus:** Applying scientific concepts/principles from "the Lesson" to explain textually described everyday phenomena, technological uses, or hypothetical scenarios.
    *   **Task:** Identify the correct concept and apply it to interpret or explain the given scenario.
    *   **Explanation/Solution:** Explain the application of the scientific principle and how it leads to the correct answer, referencing "the Lesson."

4.  **Critical Thinking Questions (minimum 20 questions):**
    *   **Focus:** Analysis of experimental design (textually described), interpretation of data (textually presented), evaluation of scientific claims, or deducing implications of a scientific finding from "the Lesson."
    *   **Task:** Reason beyond direct recall (e.g., identify controls, predict outcomes of changes, evaluate conclusions, distinguish observation/inference).
    *   **Explanation/Solution:** Explain the scientific and critical reasoning process, referencing principles or information from "the Lesson."

5.  **Assertion and Reasoning Questions (minimum 30 questions):**
    *   **Focus:** Evaluating two statements - an Assertion (A) and a Reason (R) - both derived from scientific concepts, laws, principles, facts, experimental observations, or problem-solving outcomes from "the Lesson." Questions test the understanding of the truthfulness of A and R and whether R is a correct explanation for A.
    *   **Task:** Create a minimum of `30` distinct Assertion-Reasoning (A/R) type questions. Each question must:
        *   Be based *solely* on the information presented within "the Lesson." Do not use external knowledge.
        *   Consist of an Assertion (A) and a Reason (R).
        *   Be accompanied by the four standard options:
            *   (A) Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).
            *   (B) Both Assertion (A) and Reason (R) are true, but Reason (R) is not the correct explanation of Assertion (A).
            *   (C) Assertion (A) is true, but Reason (R) is false.
            *   (D) Assertion (A) is false, but Reason (R) is true.
    *   **Explanation/Solution (for each A/R question):**
        1.  State the correct option (A, B, C, or D).
        2.  Provide a detailed analysis:
            *   Evaluate the truthfulness of Assertion (A) with justification from "the Lesson."
            *   Evaluate the truthfulness of Reason (R) with justification from "the Lesson."
            *   Explain why Reason (R) correctly explains Assertion (A) or not, leading to the chosen option.
        *   Ensure explanations are clear and questions are diverse and challenging.
"""

social_studies_specific_instructions = """
**Subject:** CBSE NCERT Class {class_num} Social Studies
**Total Questions:** 120

**Question Distribution & Category Definitions:**

1.  **Knowledge-based MCQs (minimum 30 questions):**
    *   **Focus:** Key dates, names, events, definitions, concepts, geographical facts, or constitutional provisions explicitly stated in "the Lesson."
    *   **Task:** Test direct recall or understanding.
    *   **Explanation/Solution (termed 'Justification' for SS):** Brief justification for the correct answer, referencing concepts/facts from "the Lesson."

2.  **Case-based Questions (minimum 30 questions):**
    *   **Focus:** Interpretation, inference, or identification of key ideas from a provided short paragraph.
    *   **Task:** For each, first provide a "Case Paragraph" (3-5 sentences extracted or directly summarized from "the Lesson"). Then, formulate one MCQ related *only* to that paragraph.
    *   **Structure Variation:**
        *   `Question [Sequential Number]:`
        *   `Category: Case-based`
        *   `Case Paragraph: [A short paragraph (3-5 sentences) extracted or directly summarized from "the Lesson."]`
        *   `Question Text (related to Case Paragraph): [Your formulated MCQ text]`
        *   `Options:`
            *   `(A) [Text for Option A]`
            *   `(B) [Text for Option B]`
            *   `(C) [Text for Option C]`
            *   `(D) [Text for Option D]`
        *   `Correct Answer: [Specify A, B, C, or D]`
        *   `Justification: [Provide a brief justification, explaining how the Case Paragraph supports the correct answer.]`
    *   **Note:** The general `Explanation/Solution` field is replaced by `Justification` for all Social Studies questions.

3.  **Application-based Questions (minimum 20 questions):**
    *   **Focus:** Applying concepts, theories, or historical/geographical/civic/economic principles from "the Lesson" to understand textually described contemporary situations, hypothetical scenarios, or to compare different contexts discussed.
    *   **Task:** Identify and apply a relevant concept from "the Lesson" to the given scenario.
    *   **Justification:** Explain the application of the concept and how the answer is derived, referencing "the Lesson."

4.  **Critical Thinking Questions (minimum 20 questions):**
    *   **Focus:** Analysis of cause-and-effect, evaluation of different perspectives (if presented), interpretation of motives, understanding socio-economic processes, or assessing the impact of events/policies from "the Lesson." Include analytical and interpretative questions.
    *   **Task:** Reason beyond direct recall (e.g., identify significant causes/consequences, evaluate relationships, infer assumptions).
    *   **Justification:** Explain the critical reasoning or interpretation leading to the correct answer, referencing "the Lesson."

5.  **Assertion and Reasoning Questions (minimum 30 questions):**
    *   **Focus:** Assertion-Reasoning (A/R) questions require you to evaluate two statements - an Assertion (A) and a Reason (R) - both based on the information (historical events, geographical facts, civic principles, economic concepts, interpretations) presented within "the Lesson."
    *   **Task:** Create a minimum of `30` distinct Assertion-Reasoning (A/R) type questions. Each question must:
        *   Be based *solely* on the information presented within "the Lesson." Do not use any external knowledge.
        *   Consist of an Assertion (A) and a Reason (R).
        *   Be accompanied by the four standard options:
            *   (A) Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).
            *   (B) Both Assertion (A) and Reason (R) are true, but Reason (R) is not the correct explanation of Assertion (A).
            *   (C) Assertion (A) is true, but Reason (R) is false.
            *   (D) Assertion (A) is false, but Reason (R) is true.
    *   **Justification (for each A/R question):** For each A/R question, provide:
        1.  State the correct option (A, B, C, or D).
        2.  Provide a detailed analysis:
            *   Evaluate the truthfulness of Assertion (A), justifying with facts/interpretations from "the Lesson."
            *   Evaluate the truthfulness of Reason (R), justifying with facts/interpretations from "the Lesson."
            *   Explain why Reason (R) correctly explains Assertion (A) or not, leading to the chosen option.
        *   Ensure that assertions and reasons accurately reflect "the Lesson," and that the questions are diverse and challenging.
"""
assertion_and_reasoning_prompt = """
For assertion and reasoning questions:
1.  **Understand the Goal:** Your objective is to create a minimum of `{assr_num}` distinct Assertion-Reasoning (A/R) type questions. Each question must be based *solely* on the information presented within the Chapter. Do not use any external knowledge.

2.  **Structure of an Assertion-Reasoning Question:**
    Each question you create will consist of:
    *   An **Assertion (A)**: A declarative statement of fact, principle, or concept.
    *   A **Reason (R)**: A declarative statement that purports to explain, justify, or be the cause of the Assertion.
    *   **Standard Options:**
        (a) Both A and R are true, and R is the correct explanation of A.
        (b) Both A and R are true, but R is not the correct explanation of A.
        (c) A is true, but R is false.
        (d) A is false, but R is true.
    *   The **Correct Answer** (chosen from (a), (b), (c), or (d)).
    *   **Source Reference**: The page number(s) or specific section(s) from the Chapter that support the truth/falsity of A, the truth/falsity of R, and the explanatory link (or lack thereof) between them. (This is for your verification; you will not explicitly write out full source references for each part in the final output of step 3.4, but you must be able to justify your A, R, and answer choice based on them).

3.  **Process for Creating Each Question:**
    *   **Step 3.1: Identify Content for Assertion (A).**
        *   Read the Chapter carefully.
        *   Identify a specific statement, fact, concept, definition, or principle explicitly stated in the Chapter.
        *   Formulate this as a declarative statement. This is your Assertion (A).
        *   Verify that Assertion (A) is **true** *according to the Chapter*.

    *   **Step 3.2: Identify Content for Reason (R) - Aiming for Option (a) initially.**
        *   Find a statement in the Chapter that *directly explains why Assertion (A) is true* or *is the direct cause of Assertion (A)* as presented in the Chapter.
        *   Formulate this as a declarative statement. This is your Reason (R).
        *   Verify that Reason (R) is **true** *according to the Chapter*.
        *   Verify that Reason (R) is the **correct and direct explanation** for Assertion (A) *according to the Chapter*.
        *   If all these conditions are met, the correct answer for this question will be (a).

    *   **Step 3.3: Creating Variations for Other Options (b, c, d) – Do this for subsequent questions to ensure variety:**
        *   **To create a question where the answer is (b) (Both true, R not correct explanation):**
            *   Start with a true Assertion (A) from the Chapter (as in Step 3.1).
            *   Find another statement from the Chapter that is also **true** but is *not the direct explanation or cause* of Assertion (A). It might be a related fact, a consequence, or a different aspect of the same topic, but not the direct reason for A. Use this as your Reason (R).
        *   **To create a question where the answer is (c) (A true, R false):**
            *   Start with a true Assertion (A) from the Chapter (as in Step 3.1).
            *   Formulate a Reason (R) that is **false** *according to the Chapter*, or directly contradicted by the Chapter. This R might sound plausible but must be incorrect based on the Chapter's text.
        *   **To create a question where the answer is (d) (A false, R true):**
            *   Formulate an Assertion (A) that is **false** *according to the Chapter*, or directly contradicted by the Chapter.
            *   Find a statement from the Chapter that is **true** and use this as your Reason (R). This R may or may not be related to the topic of the false A.

    *   **Step 3.4: Record the Question.**
        Write down:
        *   "Question [Sequential Number]:"
        *   "Assertion (A): [Text of your Assertion]"
        *   "Reason (R): [Text of your Reason]"
        *   "Options:"
            "(a) Both A and R are true, and R is the correct explanation of A."
            "(b) Both A and R are true, but R is not the correct explanation of A."
            "(c) A is true, but R is false."
            "(d) A is false, but R is true."
        *   "Correct Answer: "[Correct_Answer_Choice]" (This must be one of (a), (b), (c), or (d))
4.  **Coverage and Variety:**
    *   Attempt to cover different concepts, facts, and sections from the entire Chapter.
    *   Strive to create a mix of questions where the correct answer is (a), (b), (c), and (d). Do not make all questions type (a).

5.  **Quantity:**
    *   Continue this process (Steps 3.1 to 3.4) until you have created at least `{assr_num}` complete Assertion-Reasoning questions.

6.  **Final Output:**
    *   Provide the complete list of generated questions, each formatted as specified in Step 3.4.
    *   Ensure all information is derived *exclusively* from the provided Chapter text.

Format requirements for Assertion and Reasoning questions:
    1. Each question must contain two statements: Assertion (A) and Reason (R)
    2. Each question must have exactly 4 options in this format:
       a) Both A and R are true and R is the correct explanation of A
       b) Both A and R are true but R is not the correct explanation of A
       c) A is true but R is false
       d) A is false but R is true
    3. Answer must be a, b, c, or d
    4. Both statements must be clear and related to the same topic
    5. No diagrams or visual references
This prompt is designed to be followed literally. Execute these instructions precisely as written.
"""

# --- Main Function ---
def get_prompt(subject, class_num, assr=False, assr_num=20, pdf:str="", special_instructions=None):
    """Get the appropriate prompt based on subject, class, and type (MCQ or A&R)."""

        # For MCQ type questions
    formatted_common = common_instructions_mcq.format(class_num=class_num)

    subject_lower = subject.lower()
    specific_instructions = ""

    if subject_lower == "math":
        specific_instructions = math_specific_instructions.format(class_num=class_num)
    elif subject_lower == "science":
        specific_instructions = science_specific_instructions.format(class_num=class_num)
    elif subject_lower == "social studies" or subject_lower == "ss":
        specific_instructions = social_studies_specific_instructions.format(class_num=class_num)
    else:
        return "Error: Unknown subject for MCQ prompt generation." # Or raise an error
    base_prompt = [
        specific_instructions, 
        assertion_and_reasoning_prompt.format(assr_num=20)
    ]
    if special_instructions:
        base_prompt+=["Here are some special instructions reguarding lesson:", special_instructions]
    base_prompt+=(["Here is the lesson content:", pdf])
    return formatted_common, formatted_common + "\n" + "\n".join(base_prompt)

# --- Verification Prompts ---
def get_verification_prompt(question, options):
    """Get the verification prompt for checking question answers"""
    return f"""Solve this question and verify if the given answer is correct:

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

def get_verification_system_prompt():
    """Get the system prompt for verification"""
    return "You are a precise question solver and verifier."

def get_validation_system_prompt():
    """Get the system prompt for validating question format and distribution"""
    return """You are a format validator. Check both FORMAT and QUESTION TYPE DISTRIBUTION requirements."""



def get_validation_prompt(questions_str:str):
    return f"""
    Format requirements for MCQ:
    1. Each question must have exactly 4 options (a, b, c, d) ((A), (B), (C), (D) is also fine)
    2. Each question must have an answer field with value a, b, c, or d ((A), (B), (C), (D) is also fine)
    3. Each question must be a single question (no sub-questions)
    4. No diagrams or visual references

    Format requirements for Assertion and Reasoning questions:
    1. Each question must contain two statements: Assertion (A) and Reason (R)
    2. Each question must have exactly 4 options in this format:
       a) Both A and R are true and R is the correct explanation of A
       b) Both A and R are true but R is not the correct explanation of A
       c) A is true but R is false
       d) A is false but R is true
    3. Answer must be a, b, c, or d
    4. Both statements must be clear and related to the same topic
    5. No diagrams or visual references

    DO NOT:
    - Judge if answers are correct
    - Evaluate question quality
    - Suggest content improvements
    - Check if options make sense

    Here are examples of valid and invalid formats:

    Valid format examples:

    MCQ format:
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

    Assertion and Reasoning format:
    Q1. Assertion (A): The Earth's atmosphere acts as a natural greenhouse, trapping heat and keeping our planet warm.
    Reason (R): The greenhouse effect is primarily caused by gases like carbon dioxide and methane that absorb and re-emit infrared radiation.
    a) Both A and R are true and R is the correct explanation of A
    b) Both A and R are true but R is not the correct explanation of A
    c) A is true but R is false
    d) A is false but R is true
    Answer: a


    Invalid format examples:

    For MCQ:
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

    For Assertion and Reasoning:
    Missing Assertion or Reason:
    Q1. Assertion (A): The Earth's atmosphere acts as a natural greenhouse.
    a) Both A and R are true and R is the correct explanation of A
    b) Both A and R are true but R is not the correct explanation of A
    c) A is true but R is false
    d) A is false but R is true
    Answer: a

    Wrong option format:
    Q1. Assertion (A): Plants release oxygen during photosynthesis.
    Reason (R): Chlorophyll is essential for photosynthesis.
    a) True, True
    b) True, False
    c) False, True
    d) False, False
    Answer: a

    Missing proper labeling:
    Q1. Statement 1: Water boils at 100°C at sea level.
    Statement 2: Atmospheric pressure affects boiling point.
    a) Both A and R are true and R is the correct explanation of A
    b) Both A and R are true but R is not the correct explanation of A
    c) A is true but R is false
    d) A is false but R is true
    Answer: a

    Question distribution requirements:
    1. Knowledge-based direct questions: 15 questions
    2. Problem-solving questions (or case-based questions): 15 questions
    3. Application-based questions: 10 questions
    4. Critical thinking questions : 10 questions
    5. Assertion and Reasoning Questions: 20 questions
    Total required: 70 questions
    There is a distribution issue only if the number of questions in each category is less than the required number. 
    Identify both format issues and distribution issues in your response.
    Here are the category codes for each type of questions:
    - Knowledge-based Direct Questions: 'A'
    - Problem-solving Questions: 'B'
    - Application-based Questions: 'C'
    - Critical Thinking Questions: 'D'
    - Assertion and Reasoning Questions: 'E'
    Analyze these questions and provide a JSON response with format and distribution issues:
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
            "missing": number,
            "category_code": "A/B/C/D/E"
        }}
    ],
    "is_valid": boolean (true if no format or distribution issues found)
}}

Questions to analyze:
{questions_str}"""

# --- Additional Questions Prompt ---
def get_fix_questions_prompt(previous_questions, pdf_file, format_issues, distribution_issues): 
    """Get the prompt for requesting additional questions"""
    prompt = f"""
    Lesson Content:
    {pdf_file}

    Based on the Lesson Content, fix existing questions, generate additional questions as needed.

Current questions for reference:
{previous_questions}
""" 
    if format_issues:
        if format_issues["skipped_questions"]:
            prompt += """
            ### Questions with format issues:
            """
            for category_code, skipped_questions in format_issues["skipped_questions"].items():
                prompt+= f"Category {category_code} - {category_codes[category_code.upper()]}\n"
                for question in skipped_questions:
                    prompt += f"Q. {question}\n"
            prompt += """
    These questions might include issues like : 
    1. question has sub questions. 
    2. question which has any indication of visual references in the question.  
    3. question that is not independent on its on, or if the question is dependent on any other document/text.
    Please fix these issues andd rewrite these questions into their respective categories.
    If no such issues found, simply rewrite these questions into their respective categories. \n
            """
            prompt += "\n--- \n"
        if format_issues["invalid_options"]:
            prompt += """
            ### Questions with invalid options (i.e questions which dont have exactly 4 options):
            """
            for category_code, invalid_options in format_issues["invalid_options"].items():
                prompt+= f"Category {category_code} - {category_codes[category_code.upper()]}\n"
                for question in invalid_options["invalid_options"][category_code]:
                    prompt += f"Q. {question}\n"
                prompt += """
                    Please fix these issues and rewrite these questions into their respective categories.
                    If no such issues found, simply rewrite these questions into their respective categories.
                    """
                prompt += "\n--- \n"
            prompt += "---\n\n"
        if format_issues["invalid_answers"]:
            prompt += """
            ### Questions with invalid answers (i.e questions which dont have a valid answer of an MCQ A, B, C, or D):
            """
            for category_code, invalid_answers in format_issues["invalid_answers"].items():
                prompt+= f"Category {category_code} - {category_codes[category_code.upper()]}\n"
                for question in format_issues["invalid_answers"][category_code]:
                    prompt += f"Q. {question}\n"
                prompt += """
                    Please fix these issues and rewrite these questions into their respective categories.
                    If no such issues found, simply rewrite these questions into their respective categories.
                    """
                prompt += "\n--- \n"
            prompt += "---\n\n"
    prompt += """
    Important Instructions:
*   Start generating questions immediately without any introductory text other than what is specified for each question's structure.
*   Ensure each question is strictly derived from the provided "Lesson."
*   Each question MUST have EXACTLY 4 options: (A), (B), (C), and (D).
*   Make options challenging and confusing. Distractors (incorrect options) should be plausible and potentially based on common misconceptions or slight, incorrect variations of correct information relevant to "the Lesson."

**Standard Structure for Each Question:**
*   `Question Number: [NUMBER]`
*   `Question Text: [Your formulated question text]`
*   `Options:`
    *   `(A) [Text for Option A]`
    *   `(B) [Text for Option B]`
    *   `(C) [Text for Option C]`
    *   `(D) [Text for Option D]`
*   `||Explanation/Solution: [Provide detailed step-by-step solution for problem-solving/numerical questions. For other types, provide a clear justification for the correct answer, referencing "the Lesson."]||`
*   `Correct Answer: [Specify A, B, C, or D]`
Clearly mark heading before starting each category of questions and use '---' to separate question category.
BEFORE BEGINNING EACH QUESTION CATEGORY, write category code for the category in json. like this : {{"category_code": "A"}}
Here are the category codes for each type of questions:
    - Knowledge-based Direct Questions: 'A'
    - Problem-solving Questions: 'B'
    - Application-based Questions: 'C'
    - Critical Thinking Questions: 'D'
    - Assertion and Reasoning Questions: 'E'

Always start question number of each category from 1

Explanation MUST start and end with 2 vertical bars (||)
    1. Only rewrite the questions with format issues, in their respective categories.
    3.  **Ensure new questions are unique:** They must not duplicate or rephrase any other question in the final list.
    4.  **Maintain consistency:** The entire list should have a consistent style, format, and difficulty.
    5.  **Ground all answers in the text:** All questions must be answerable using only the `Lesson Content`."""

    return prompt
    
    
def get_fix_questions_system_prompt():
    return """You are an expert assessment editor. Your task is to surgically correct and augment a list of questions based on a specific set of instructions.

**Your Core Directives:**

1.  **Targeted Output:** Your response must ONLY contain the questions you are explicitly asked to rewrite or generate. DO NOT return the full list, and DO NOT repeat any unchanged questions provided for context.
2.  **Strict Formatting:** Every question you output—whether rewritten or new—MUST strictly adhere to the provided format, starting with `@@`, containing all required fields (like `question_number`, `Explanation/Solution`, etc.), and ending with `@@`.
3.  **Execute Tasks Precisely:** You will be given a list of tasks divided into parts (e.g., rewriting for format, generating new questions). Execute these tasks exactly as specified.
4.  **Content Fidelity:** All content, including questions, options, and explanations, must be derived exclusively from the provided `Lesson Content`. Do not use external knowledge.
5.  **Uniqueness:** Ensure any newly generated questions are distinct and do not duplicate concepts already tested in the questions provided for context.
"""
def get_format_prompt(questions_str):
    return f"""Format these questions into JSON following this exact format:
    [
    {{"category_code": "A", 
    "questions":[{{
        "question_number": 1,
        "question": "What is the value of x in the equation 2x + 5 = 15?",
        "options": {{
            "a": "5",
            "b": "10",
            "c": "15",
            "d": "20"
        }},
        "answer": "a"
    }}]...
    }},
    {{
    "category_code": "B",
    "questions":[{{
        "question_number": 2,
        "question": "What is the value of x in the equation 2x + 5 = 15?",
        "options": {{
            "a": "5",
            "b": "10",
            "c": "15",
            "d": "20"
        }},
        "answer": "a"
    }}]...
    }}, ...
    ]
Questions to format:
{questions_str}
A few instructions:
1. Category codes are provided once in the questions, divided by '---'. The category codes are : A, B, C, D, & E. Use them properly.
2. IF some questions dont have options, leave the options field empty
3. IF some questions dont have answer, leave the answer field empty
4. Skip any question that has sub questions.
5. skip any question which has any indication of visual references in the question. 
6. Skip any question that is not independent on its on, or if the question is dependent on any other document/text.
7. Always start question number of each category from 1, reguardless of what given in the questions
"""


# --- Example Usage (for testing) ---
if __name__ == '__main__':
    # Example for Math MCQ
    math_prompt = get_prompt(subject="Math", class_num="10")
    print("--- MATH MCQ PROMPT ---")
    print(math_prompt)
    print("\n\n")
    print(len(math_prompt)/4)
