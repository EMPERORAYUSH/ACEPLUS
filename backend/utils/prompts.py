SOLUTION_GENERATION_PROMPT = """As an expert tutor, help a student understand a problem they got wrong. You have:

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

PERFORMANCE_ANALYSIS_PROMPT = """Analyze my exam performance and provide specific, actionable feedback.

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

    Reference these lessons in your analysis: {lesson_names}

    Important:
    - Identify topics from the questions to give better feedback
    - Don't give generic study tips
    - Focus on the specific topics where mistakes were made
    - Provide concrete examples based on the actual mistakes
    - Keep formatting consistent with the above structure
    - Use bullet points (•) for main points and (*) for sub-points
    """

IMAGE_ANALYSIS_PROMPT = """Analyze these images containing MCQ questions. Output your response in XML format with the following structure:

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