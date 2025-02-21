# Telegram Auto-Translator Bot

This bot automatically translates messages between English and Portuguese in Telegram chats using DeepL's translation API.

## Features
- Automatically detects language
- Translates English → Portuguese
- Translates Portuguese → English
- No configuration needed - just start chatting!

## Deployment on Railway

1. Fork this repository

2. Create a new project on [Railway](https://railway.app)

3. Connect your GitHub repository

4. Add these environment variables in Railway:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   DEEPL_API_KEY=your_deepl_api_key
   ```

5. Railway will automatically deploy your bot!

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your tokens:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   DEEPL_API_KEY=your_deepl_api_key
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```
     GOOGLE_APPLICATION_CREDENTIALS=path_to_your_credentials.json
     ```

## Usage

1. Add the bot to your Telegram group
2. Give it admin rights to read messages
3. Start sending messages - they'll be automatically translated!

## Features

- Automatic language detection
- Instant translations
- Group chat support
- Preserves original message formatting
