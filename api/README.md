# Telegram API Microservice

FastAPI HTTP wrapper around the Telegram Bot API. The service exposes every `TelegramClient` method as a REST endpoint.

## Multi-Bot Support

The service supports multiple Telegram bots simultaneously. Each bot is identified by a unique name configured via environment variables (`TELEGRAM_BOT_TOKEN_<BOT_NAME>`). Bot names are used in the API path to route requests to the correct bot instance.

## Endpoints

Base path: `/api/v1`

Interactive Swagger UI: `http://localhost:8000/docs`

**Note:** Replace `{bot_name}` in the endpoint paths with your configured bot name (e.g., `production`, `staging`, `dev`).

### List configured bots

- `GET /api/v1/bots`
- Response:
  ```json
  {
    "success": true,
    "bot_names": ["production", "staging", "dev"],
    "error": null
  }
  ```
- This endpoint lists all configured bot names without exposing their tokens.

### Health check

- `GET /`
- Response: `{"status": "ok", "service": "telegram-api"}`

### Get chat IDs

Use this after sending a message to your bot to discover the `chat_id` you need for the other endpoints.

- `GET /api/v1/{bot_name}/get_chat_ids?limit=10`
- Response:
  ```json
  {
    "success": true,
    "chat_ids": [
      {"chat_id": 123456789, "text": "Hi bot"}
    ],
    "error": null
  }
  ```

### Send a message

- `POST /api/v1/{bot_name}/send_message`
- Body:
  ```json
  {
    "chat_id": 123456789,
    "text": "Hello from the bot!"
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "message_id": 42,
    "error": null
  }
  ```

### Send a reply keyboard

- `POST /api/v1/{bot_name}/send_reply_keyboard`
- Body:
  ```json
  {
    "chat_id": 123456789,
    "text": "Pick an option",
    "keyboard": [["Yes", "No"], ["Cancel"]],
    "resize_keyboard": true,
    "one_time_keyboard": false
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "message_id": 42,
    "error": null
  }
  ```

### Remove a reply keyboard

- `POST /api/v1/{bot_name}/remove_reply_keyboard`
- Body:
  ```json
  {
    "chat_id": 123456789,
    "text": "Keyboard removed."
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "message_id": 42,
    "error": null
  }
  ```

### Get updates

- `POST /api/v1/{bot_name}/get_updates`
- Body:
  ```json
  {
    "chat_id": 123456789,
    "limit": 10,
    "timeout": 0
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "updates": [
      {"update_id": 1, "chat_id": 123456789, "text": "Hello"}
    ],
    "error": null
  }
  ```

### Send a file

- `POST /api/v1/{bot_name}/send_file`
- Body:
  ```json
  {
    "chat_id": 123456789,
    "filename": "document.pdf",
    "file_type": "document",
    "caption": "Here is the document"
  }
  ```
- Supported `file_type` values: `document`, `photo`, `video`, `audio`
- Response:
  ```json
  {
    "success": true,
    "message_id": 42,
    "error": null
  }
  ```

## Error responses

- `400` — Validation error (e.g., empty text, empty keyboard, missing `chat_id`).
- `500` — Telegram API error.

## Example usage with curl

```bash
# Set your bot name (e.g., production, staging, dev)
BOT_NAME="production"

# 1. Health check
curl "http://localhost:8000/"

# 2. List configured bots
curl "http://localhost:8000/api/v1/bots"

# 3. Send a message to your bot first, then get your chat ID
curl "http://localhost:8000/api/v1/${BOT_NAME}/get_chat_ids?limit=10"

# 4. Send a message
curl -X POST "http://localhost:8000/api/v1/${BOT_NAME}/send_message" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "text": "Hello!"}'

# 5. Send a reply keyboard
curl -X POST "http://localhost:8000/api/v1/${BOT_NAME}/send_reply_keyboard" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "text": "Pick an option",
    "keyboard": [["Yes", "No"], ["Cancel"]]
  }'

# 6. Remove a reply keyboard
curl -X POST "http://localhost:8000/api/v1/${BOT_NAME}/remove_reply_keyboard" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "text": "Keyboard removed."}'

# 7. Get updates
curl -X POST "http://localhost:8000/api/v1/${BOT_NAME}/get_updates" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": 123456789, "limit": 10, "timeout": 0}'

# 8. Send a file
curl -X POST "http://localhost:8000/api/v1/${BOT_NAME}/send_file" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": 123456789,
    "filename": "document.pdf",
    "file_type": "document",
    "caption": "Here is the document"
  }'
```
