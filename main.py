import ast
import os
import json
import textwrap
import time
import logging
from dotenv import load_dotenv
from telegram_handler import setup_bot, create_initial_options_keyboard, create_difficulty_keyboard, create_number_of_questions_keyboard, show_answers_keyboard, choose_document_type_keyboard
from document_processor import process_document
from gemini_handler import answer_question, Summarize, generate_qa_for_chunks
from vector_db import add_document_to_db, get_relevant_chunks, clear_vector_db, get_chunks
from telebot.apihelper import ApiTelegramException

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Telegram Bot
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = setup_bot(BOT_TOKEN)

# Dictionary to store user-specific data
user_data = {}

# File to store user data
USER_DATA_FILE = 'user_data.json'

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    return {'allowed_users': [], 'admin_users': []}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f)

# Load user data
user_data_auth = load_user_data()
ALLOWED_USERS = set(user_data_auth['allowed_users'])
ADMIN_USERS = set(user_data_auth['admin_users'])

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USERS:
        user_data[user_id] = {'current_document': None, 'questions': None, 'difficulty': None, 'watermark': False}
        send_help_message(user_id)
        bot.reply_to(message, "Welcome! Send me a PDF, Excel, CSV, or TXT file to process.\nارسل ملف pdf, excel, csv, txt")
    else:
        bot.reply_to(message, "Sorry, you are not authorized to use this bot.")
    
    logger.info(f"User attempt: ID {user_id}")

@bot.message_handler(commands=['myid'])
def send_user_id(message):
    user_id = message.from_user.id
    bot.reply_to(message, f"Your Telegram user ID is: {user_id}")

@bot.message_handler(commands=['adduser'])
def add_user(message):
    admin_id = message.from_user.id
    if admin_id not in ADMIN_USERS:
        bot.reply_to(message, "Sorry, you don't have permission to add users.")
        return
    
    try:
        new_user_id = int(message.text.split()[1])
        ALLOWED_USERS.add(new_user_id)
        user_data_auth['allowed_users'] = list(ALLOWED_USERS)
        save_user_data(user_data_auth)
        bot.reply_to(message, f"User {new_user_id} has been added to the allowed users list.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a valid user ID. Usage: /adduser USER_ID")

@bot.message_handler(commands=['removeuser'])
def remove_user(message):
    admin_id = message.from_user.id
    if admin_id not in ADMIN_USERS:
        bot.reply_to(message, "Sorry, you don't have permission to remove users.")
        return
    
    try:
        user_id_to_remove = int(message.text.split()[1])
        if user_id_to_remove in ALLOWED_USERS:
            ALLOWED_USERS.remove(user_id_to_remove)
            user_data_auth['allowed_users'] = list(ALLOWED_USERS)
            save_user_data(user_data_auth)
            bot.reply_to(message, f"User {user_id_to_remove} has been removed from the allowed users list.")
        else:
            bot.reply_to(message, f"User {user_id_to_remove} is not in the allowed users list.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Please provide a valid user ID. Usage: /removeuser USER_ID")

@bot.message_handler(commands=['listusers'])
def list_users(message):
    admin_id = message.from_user.id
    if admin_id not in ADMIN_USERS:
        bot.reply_to(message, "Sorry, you don't have permission to list users.")
        return
    
    user_list = "\n".join(f"- {user_id}" for user_id in ALLOWED_USERS)
    bot.reply_to(message, f"Allowed Users:\n{user_list}")

@bot.message_handler(content_types=['document', 'photo'])
def handle_document(message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'current_document': None, 'questions': None, 'difficulty': None, 'watermark': False}
        print(user_data[user_id], user_id)

    try:
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        file_extension = os.path.splitext(file_name)[1].lower()

        if file_extension == '.pdf':
            markup = choose_document_type_keyboard()
            bot.reply_to(message, "Does this PDF have a watermark?\nهل يحتوي هذا الملف على علامة مائية؟", reply_markup=markup)
            
            bot.set_state(user_id, 'waiting_for_watermark_answer', message.chat.id)
            with bot.retrieve_data(user_id, message.chat.id) as data:
                data['file_info'] = file_info
                data['file_name'] = file_name
            print('PDF processed.')
        else:
            process_file(message, file_info, file_name, file_extension, watermark=False)

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

def process_file(message, file_info, file_name, file_extension, watermark):
    user_id = message.chat.id
    print(user_id)

    bot.send_message(message.chat.id, 'Please wait ....\nيرجى الانتظار ....')
    
    try:
        downloaded_file = bot.download_file(file_info.file_path)
        temp_file_name = f"temp_{user_id}{file_extension}"
        with open(temp_file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        text = process_document(temp_file_name, watermark)
        clear_vector_db(user_id)
        add_document_to_db(text, file_extension[1:], user_id)
        user_data[user_id]['current_document'] = file_name

        os.remove(temp_file_name)
        
        bot.send_message(message.chat.id, 'File processed successfully.\nتم معالجة الملف بنجاح.', reply_markup=create_initial_options_keyboard())
    except Exception as e:
        bot.send_message(message.chat.id, f"An error occurred while processing the file: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_question(message):
    user_id = message.chat.id
    if user_id in user_data and user_data[user_id]['current_document']:
        question = message.text
        try:
            relevant_chunks = get_relevant_chunks(question, user_id)
            context = " ".join(relevant_chunks)
            answer = answer_question(context, question)
            bot.reply_to(message, answer, reply_markup=create_initial_options_keyboard())
        except Exception as e:
            bot.reply_to(message, f"An error occurred while answering your question: {str(e)}")
    else:
        bot.reply_to(message, "Please upload a document first to ask questions about it.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if user_id not in user_data:
        user_data[user_id] = {'current_document': None, 'questions': None, 'difficulty': None, 'watermark': False}

    if call.data in ['True', 'False']:
        user_data[user_id]['watermark'] = call.data == 'True'
        bot.answer_callback_query(call.id, "Processing your file...")
        
        with bot.retrieve_data(user_id, chat_id) as data:
            file_info = data['file_info']
            file_name = data['file_name']

        file_extension = os.path.splitext(file_name)[1].lower()
        process_file(call.message, file_info, file_name, file_extension, user_data[user_id]['watermark'])

    elif call.data == "summarize":
        bot.send_message(chat_id, 'Please wait ....\nيرجى الانتظار ....')
        try:
            chunks = get_chunks(user_id)
            summary = Summarize(chunks)
            send_long_message(chat_id, summary)
            bot.send_message(chat_id, "Summarization complete.\nتم انشاء ملخص", reply_markup=create_initial_options_keyboard())
        except Exception as e:
            bot.send_message(chat_id, f"An error occurred during summarization: {str(e)}")

    elif call.data == "generate_questions":
        bot.send_message(chat_id, "Choose the difficulty level:", reply_markup=create_difficulty_keyboard())

    elif call.data in ['easy', 'medium', 'hard']:
        user_data[user_id]['difficulty'] = call.data
        bot.send_message(chat_id, 'How many questions would you like to generate?', reply_markup=create_number_of_questions_keyboard())

    elif call.data in ['5', '10', '15']:
        chunks = get_chunks(user_id)
        n_questions = int(call.data)
        difficulty = user_data[user_id]['difficulty']
        bot.send_message(chat_id, 'Please wait ....\nيرجى الانتظار ....')
        # Use the updated combined function
        qa_pairs, cached_questions = generate_qa_for_chunks(chunks, difficulty, n_questions, user_data[user_id].get('cached_questions'))
        
        # Store the cached questions for future use
        user_data[user_id]['cached_questions'] = cached_questions
        
        # Store the Q&A pairs
        user_data[user_id]['qa_pairs'] = qa_pairs
        
        # Create an ordered list of questions
        ordered_questions = '\n'.join([f"{i+1}. {q}" for i, q in enumerate(qa_pairs.keys())])
        
        bot.send_message(chat_id, f'Here are your questions:\n{ordered_questions}', reply_markup=show_answers_keyboard())

    elif call.data == "show_answers":
        bot.send_message(chat_id, 'Please wait ....\nيرجى الانتظار ....')
        
        qa_pairs = user_data[user_id]['qa_pairs']
        
        for i, (question, answer) in enumerate(qa_pairs.items(), 1):
            message = f"Q{i}: {question}\nA: {answer}\n"
            bot.send_message(chat_id, message)
        
        bot.send_message(chat_id, f'done! تم الانتهاء', reply_markup=create_initial_options_keyboard())

    elif call.data == "new_conversation":
        start_new_conversation(call)

    elif call.data == "help":
        send_help_message(chat_id)

def start_new_conversation(call):
    user_id = call.from_user.id
    user_data[user_id] = {'current_document': None, 'questions': None, 'difficulty': None, 'watermark': False}
    clear_vector_db(user_id)

    try:
        bot.answer_callback_query(call.id, "New conversation started.")
    except Exception as e:
        print(f"Error answering callback query: {str(e)}")

    bot.send_message(call.message.chat.id, "Ready for a new document. Please upload a PDF, Excel, CSV, or TXT file.\nجاهز لملف جديد يرجى تحميل ملف pdf, excel, csv, txt")

def send_long_message(chat_id, text, max_retries=3, retry_delay=5):
    total_characters = sum(len(string) for string in text)
    print('total characters:', total_characters)
    if total_characters <= 1600:
        messages = [text]
        print('message length is smaller than 4096, text length: ', total_characters)
    else:
        messages = ' '.join(text)
        messages = textwrap.wrap(messages, width=1600, break_long_words=False)
        print('number of messages:', len(messages))

    for message in messages:
        for attempt in range(max_retries):
            try:
                bot.send_message(chat_id, message)
                print(f"\nMessage sent: {message}")
                break 
            except ApiTelegramException as e:
                print(f"Error sending message: {str(e)}")
                if e.error_code == 429: 
                    retry_after = e.result_json['parameters']['retry_after']
                    time.sleep(retry_after)
                    continue
                elif attempt == max_retries - 1: 
                    raise  
            except Exception as e:
                print(f"Error sending message: {str(e)}")
                if attempt == max_retries - 1: 
                    raise 
                time.sleep(retry_delay)

def send_help_message(chat_id):
    help_message = """
    Available commands:
    - summarize - Summarize the document
    - generate_questions - Generate questions from the document you uploaded
    - show_answers - Show answers of the generated questions
    - new_conversation - Start a new conversation
    - help - Show this help message

    You can upload a PDF, Excel, CSV, or TXT file or an image.
                     
    Use the buttons to interact with the bot.
    The bot can summarize the document, generate questions and answer them or interact with images or excel files.
    If you want the bot to solve a list of question or exam please provide the questions in a form of a text file.
    
    If you uploaded a pdf with a watermark make sure to choose the watermark option.
    ________________________________________________
    الأوامر المتاحة:

    تلخيص: تلخيص المستند.
    توليد_أسئلة: توليد أسئلة من المستند الذي قمت بتحميله.
    إظهار_الإجابات: إظهار إجابات الأسئلة المتولدة.
    محادثة_جديدة: بدء محادثة جديدة.
    مساعدة: عرض رسالة المساعدة هذه.
    يمكنك تحميل ملف بصيغة PDF، Excel، CSV، TXT أو صورة.

    استخدم الأزرار للتفاعل مع الروبوت. يمكن للروبوت تلخيص المستند، توليد الأسئلة وإجاباتها أو التفاعل مع الصور أو ملفات Excel. إذا كنت ترغب في أن يقوم الروبوت بحل قائمة من الأسئلة أو الامتحان، يرجى توفير الأسئلة في شكل ملف نصي.

    إذا قمت بتحميل ملف PDF يحتوي على علامة مائية، تأكد من اختيار خيار العلامة المائية.
    /start: بدء محادثة جديدة.
    """
    bot.send_message(chat_id, help_message)

def run_bot():
    while True:
        try:
            logger.info("Starting bot polling...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except ApiTelegramException as e:
            logger.error(f"ApiTelegramException: {e}")
            if e.error_code == 429:  # Too Many Requests
                retry_after = e.result_json.get('parameters', {}).get('retry_after', 30)
                logger.info(f"Sleeping for {retry_after} seconds due to rate limiting")
                time.sleep(retry_after)
            else:
                logger.info("Restarting bot polling in 10 seconds...")
                time.sleep(10)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info("Restarting bot polling in 10 seconds...")
            time.sleep(10)



if __name__ == "__main__":
    run_bot()