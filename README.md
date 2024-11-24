# Telegram Document Processing Bot

This Telegram bot allows users to upload documents in various formats (PDF, Excel, CSV, TXT, or images) and interact with them. The bot provides functionalities such as document summarization, generating and answering questions based on document content, and handling documents with watermarks.

## Features

- **Document Processing**: Upload and process PDF, Excel, CSV, TXT files, or images.
- **Summarization**: Automatically summarize the uploaded document.
- **Question Generation**: Generate questions from the document based on difficulty levels.
- **Answering Questions**: Answer questions related to the content of the uploaded document.
- **Read OCR images and pdfs**: Option to specify if the uploaded PDF contains a watermark.

## Project Structure

- `main.py`: The main file that runs the bot.
- `telegram_handler.py`: Contains functions to set up the Telegram bot and handle user interactions.
- `document_processor.py`: Processes documents based on file type and applies text extraction.
- `gemini_handler.py`: Handles text summarization and question-answer generation.
- `vector_db.py`: Manages a vector database for storing and retrieving relevant document chunks.
- `google_vision.py`: Manages a vector database for storing and retrieving relevant document chunks.

## Prerequisites

1. **Python 3.10+**
2. **Telegram Bot Token**: You will need to create a Telegram bot using [BotFather](https://core.telegram.org/bots#botfather) and get the bot token.
3. **Environment Variables**:
   - `TELEGRAM_BOT_TOKEN`: Telegram bot token obtained from BotFather.
   - `GOOGLE_API_KEY`: Gemini API key.
   - `GOOGLE_APPLICATION_CREDENTIALS`: Google vision json file.

   - Other required environment variables should be defined in a `.env` file.

## Install Required Packages

   ```bash
   pip install -r requirements.txt
   ```



## Run The Bot

   ```bash
   python main.py
   ```
