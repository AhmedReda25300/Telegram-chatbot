import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai import GenerativeModel
import random

load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = GenerativeModel('gemini-pro')

def set_minimal_safety_settings():
    return [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]

safety_settings = set_minimal_safety_settings()

def answer_question(context, question):
    prompt = f"Context: {context}\n\nQuestion: {question}\n\n fill any missings @ or .\n Answer:"
    response = model.generate_content(prompt, safety_settings=safety_settings)
    return response.text

def Summarize(chunks):
    summaries = []
    print('number of chunks:', len(chunks))
    for chunk in chunks:
#         prompt = f"""can you summarize extensively and describtivly this text and keep the original language of it 
#         And be very descriptive with the summarization detailed don't wrap it up, and ensure that no unsafe or sexually explicit content is included in the summary. Maintain the same language as the original text. and tell it like you are telling a story: \n\n{chunk}"""
        prompt = f"""
        Please provide a detailed summary of the following text, **strictly adhering to its original language and style**. The summary should be comprehensive, avoiding excessive brevity or generalization. 

        **Key points to consider:**
        * **Preserve the original language:** Use *exactly* the same words, phrasing, and tone as the source text.
        * **Tell a story:** Present the information in a narrative format, as if you were recounting a tale.
        * **Avoid unsafe or explicit content:** Ensure the summary is appropriate for all audiences.
        * **Maintain the same language:** Use the same language as the original text.
        * ** Use the same language of the text under *Text to summarize*\n\n
        **Text to summarize:**\n
        {chunk}
        """
        response = model.generate_content(prompt, safety_settings=safety_settings)
        print('response.prompt_feedback:', response.prompt_feedback)
        summaries.append(response.text)
    print('length of summaries:', len(summaries))
    return summaries

def generate_qa_for_chunks(chunks, difficulty, number_of_questions=10, cached_questions=None):
    all_questions = []
    all_qa_pairs = {}
    
    if cached_questions is None:
        cached_questions = [[] for _ in chunks]
    
    for i, chunk in enumerate(chunks):
        # Use cached questions if available, otherwise generate new ones
        if cached_questions[i]:
            questions = cached_questions[i]
        else:
            # Generate questions
            prompt_questions = f"""Generate questions based on the text below with the same text language don't generate the answers but make sure that each question has an answer. 
            Format them as follows:

            -
            -
            -

            Generate {difficulty} questions
            don't write anything else other than the questions
            \n{chunk}"""

            print(f"Generating questions for chunk {i + 1}/{len(chunks)}...")
            
            try:
                response = model.generate_content(prompt_questions, safety_settings=safety_settings)
                questions_text = response.text.strip()
                generated_questions = questions_text.splitlines()

                questions = []
                for question in generated_questions:
                    question = question.strip()
                    if question and question.startswith('-'):
                        questions.append(question[1:].strip())
                
                # Cache the generated questions
                cached_questions[i] = questions
            
            except Exception as e:
                print(f"An error occurred for chunk {i + 1}: {e}")
                continue  # Ignore the error and move on to the next chunk
        
        all_questions.extend(questions)
    
    # Randomly select the required number of questions from all generated questions
    selected_questions = random.sample(all_questions, min(number_of_questions, len(all_questions)))
    
    # Generate answers for the selected questions
    for question in selected_questions:
        # Find the chunk that contains the answer to this question
        for i, chunk in enumerate(chunks):
            if question in cached_questions[i]:
                prompt_answer = f'Answer the following question:\n\n{question}\n\nusing the following text:\n\n{chunk}\n\n'
                response = model.generate_content(prompt_answer, safety_settings=safety_settings)
                answer = response.text.strip()
                all_qa_pairs[question] = answer
                break
    
    return all_qa_pairs, cached_questions