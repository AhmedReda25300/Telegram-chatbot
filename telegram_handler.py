import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup_bot(token):
    return telebot.TeleBot(token)

def create_initial_options_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Summarize تلخيص", callback_data="summarize"),
        InlineKeyboardButton("New topic موضوع جديد", callback_data="new_conversation")
    )
    keyboard.row(
        InlineKeyboardButton("Q&A عمل اسئله", callback_data="generate_questions"),
        InlineKeyboardButton("Help مساعدة", callback_data="help")
    )
    return keyboard

def choose_document_type_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Yes", callback_data="True"),
        InlineKeyboardButton("No", callback_data="False")

    )
    return keyboard



def create_difficulty_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Easy\n سهل", callback_data="easy"),
        InlineKeyboardButton("Medium\n متوسط", callback_data="medium"),
        InlineKeyboardButton("Hard\n صعب", callback_data="hard")
    )
    return keyboard

def show_answers_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Show Answers\n ...عرض الاجابات", callback_data="show_answers"),
        InlineKeyboardButton("Start New Conversation\n ...ابدا محادثه جديده", callback_data="new_conversation")
        )
    return keyboard



def create_number_of_questions_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("5", callback_data="5"),
        InlineKeyboardButton("10", callback_data="10"),
        InlineKeyboardButton("15", callback_data="15")
    )
    return keyboard


