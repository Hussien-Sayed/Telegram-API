# Project Tree

## Telegram-API

uploads/
└── .gitkeep [x]
    ├── Functionality:
    │   - Ensure the uploads folder is tracked in git
    ├── Input:
    │   - None
    └── Output:
        - Empty file
api/
├── __init__.py [x]
├── main.py [x]
│   ├── function health_check() [x]
│   │   ├── Functionality:
│   │   │   - Return service status for health check
│   │   ├── Input:
│   │   │   - None
│   │   └── Output:
│   │       - dict with status information
│   └── function lifespan() [x]
│       ├── Functionality:
│       │   - Yield control to the app and shut down the client on exit
│       ├── Input:
│       │   - app: FastAPI
│       └── Output:
│           - None
├── models.py [x]
│   ├── class SendMessageRequest [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for send_message endpoint
│   │   │   - Include json_schema_extra examples for Swagger UI
│   │   ├── Input:
│   │   │   - chat_id: int
│   │   │   - text: str
│   │   │   - kwargs: Optional[Dict[str, Any]]
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class SendReplyKeyboardRequest [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for send_reply_keyboard endpoint
│   │   │   - Include json_schema_extra examples for Swagger UI
│   │   ├── Input:
│   │   │   - chat_id: int
│   │   │   - text: str
│   │   │   - keyboard: List[List[str]]
│   │   │   - resize_keyboard: bool = True
│   │   │   - one_time_keyboard: bool = False
│   │   │   - kwargs: Optional[Dict[str, Any]]
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class RemoveReplyKeyboardRequest [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for remove_reply_keyboard endpoint
│   │   │   - Include json_schema_extra examples for Swagger UI
│   │   ├── Input:
│   │   │   - chat_id: int
│   │   │   - text: str = "Keyboard removed."
│   │   │   - kwargs: Optional[Dict[str, Any]]
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class GetUpdatesRequest [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for get_updates endpoint
│   │   │   - Include json_schema_extra examples for Swagger UI
│   │   ├── Input:
│   │   │   - chat_id: Optional[int] = None
│   │   │   - limit: int = 10
│   │   │   - timeout: int = 0
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class GetChatIdsRequest [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for get_chat_ids endpoint
│   │   │   - Include json_schema_extra examples for Swagger UI
│   │   ├── Input:
│   │   │   - limit: int = 10
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class SendFileRequest [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for send_file endpoint
│   │   │   - Include json_schema_extra examples for Swagger UI
│   │   │   - Validate file_type is one of: document, photo, video, audio
│   │   ├── Input:
│   │   │   - chat_id: int
│   │   │   - filename: str
│   │   │   - caption: Optional[str] = None
│   │   │   - file_type: str
│   │   │   - kwargs: Optional[Dict[str, Any]] = None
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class MessageResponse [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for message operation responses
│   │   │   - Add split flag and message_ids list for split messages
│   │   ├── Input:
│   │   │   - success: bool
│   │   │   - message_id: Optional[int] = None
│   │   │   - message_ids: Optional[List[int]] = None
│   │   │   - split: bool = False
│   │   │   - error: Optional[str] = None
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class UpdatesResponse [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for get_updates responses
│   │   ├── Input:
│   │   │   - success: bool
│   │   │   - updates: List[UpdateEntry]
│   │   │   - error: Optional[str] = None
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class ChatIdsResponse [x]
│   │   ├── Functionality:
│   │   │   - Pydantic model for get_chat_ids responses
│   │   ├── Input:
│   │   │   - success: bool
│   │   │   - chat_ids: List[ChatIdEntry]
│   │   │   - error: Optional[str] = None
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   ├── class UpdateEntry [x]
│   │   ├── Functionality:
│   │   │   - Typed inner model for a single update
│   │   ├── Input:
│   │   │   - update_id: int
│   │   │   - chat_id: Optional[int] = None
│   │   │   - message_type: Optional[Literal["voice", "text"]] = None
│   │   │   - text: Optional[str] = None
│   │   │   - reply_to_message_id: Optional[int] = None
│   │   └── Output:
│   │       - Validated Pydantic model instance
│   └── class ChatIdEntry [x]
│       ├── Functionality:
│       │   - Typed inner model for a single chat ID entry
│       ├── Input:
│       │   - chat_id: int
│       │   - message_type: Optional[Literal["voice", "text"]] = None
│       │   - text: Optional[str] = None
│       └── Output:
│           - Validated Pydantic model instance
├── router.py [x]
│   ├── function create_router() [x]
│   │   ├── Functionality:
│   │   │   - Create an APIRouter with endpoints backed by the given TelegramClient
│   │   ├── Input:
│   │   │   - client: TelegramClient
│   │   └── Output:
│   │       - APIRouter instance
│   ├── function send_message() [x]
│   │   ├── Functionality:
│   │   │   - Send message endpoint
│   │   │   - Return split flag and message_ids when message is split
│   │   ├── Input:
│   │   │   - request: SendMessageRequest
│   │   └── Output:
│   │       - Dict[str, Any]
│   ├── function send_reply_keyboard() [x]
│   │   ├── Functionality:
│   │   │   - Send reply keyboard endpoint
│   │   ├── Input:
│   │   │   - request: SendReplyKeyboardRequest
│   │   └── Output:
│   │       - Dict[str, Any]
│   ├── function remove_reply_keyboard() [x]
│   │   ├── Functionality:
│   │   │   - Remove reply keyboard endpoint
│   │   ├── Input:
│   │   │   - request: RemoveReplyKeyboardRequest
│   │   └── Output:
│   │       - Dict[str, Any]
│   ├── function get_updates() [x]
│   │   ├── Functionality:
│   │   │   - Get updates endpoint
│   │   │   - Detect update.message.voice; if present, await transcribe_voice(voice, client.bot)
│   │   │   - Fall back to update.message.text for text messages
│   │   │   - Include message_type ("voice" | "text" | None) in each returned update
│   │   │   - Include reply_to_message_id when the message is a reply
│   │   │   - Text is None if neither voice nor text
│   │   ├── Input:
│   │   │   - request: GetUpdatesRequest
│   │   └── Output:
│   │       - Dict[str, Any]
│   └── function get_chat_ids() [x]
│       ├── Functionality:
│       │   - Get chat IDs endpoint
│       │   - Detect update.message.voice; if present, await transcribe_voice(voice, client.bot)
│       │   - Fall back to update.message.text for text messages
│       │   - Include message_type ("voice" | "text" | None) in each returned chat entry
│       │   - Text is None if neither voice nor text
│       ├── Input:
│       │   - limit: int
│       └── Output:
│           - Dict[str, Any]
│   └── function send_file() [x]
│       ├── Functionality:
│       │   - Send file endpoint
│       │   - Call client.send_file() with request parameters
│       │   - Return MessageResponse with success status, message_id, and error details
│       │   - Handle ValueError for validation errors (400 status)
│       │   - Handle TelegramError for API errors (500 status)
│       ├── Input:
│       │   - request: SendFileRequest
│       └── Output:
│           - Dict[str, Any]
└── README.md [*]
    ├── Functionality:
    │   - Document API endpoint reference
    │   - Document request/response schema
    │   - Provide concrete example requests for every route
    │   - Provide usage examples with curl or Python requests
    │   - Add /send_file endpoint documentation
    │   - Include request/response schema for send_file
    │   - Provide example requests for each file type
    ├── Input:
    │   - None
    └── Output:
        - Markdown documentation file
telegram_api/
├── __init__.py [x]
│   └── Functionality:
│       - Export TelegramClient from utils
│       - Define __all__ for package exports
├── utils.py [x]
│   ├── function _split_markdownv2_safely() [x]
│   │   ├── Functionality:
│   │   │   - Convert Markdown to Telegram MarkdownV2 and split into chunks safely
│   │   │   - Use telegramify_markdown.split_markdownv2 to avoid tearing entities
│   │   │   - Fall back to _split_text_safely if conversion fails
│   │   ├── Input:
│   │   │   - text: str
│   │   │   - limit: int = 4096
│   │   └── Output:
│   │       - List[str]: MarkdownV2-safe chunks
│   ├── function _split_text_safely() [x]
│   ├── function transcribe_voice() [*]
│   │   ├── Functionality:
│   │   │   - Async helper to transcribe voice messages using OpenAI Whisper
│   │   │   - Read WHISPER_MODEL (default "base") from env at module load time
│   │   │   - Load Whisper model once at module level (singleton pattern)
│   │   │   - Hardcode device to "cpu" in model load call
│   │   │   - Download voice file to /tmp/voice_{file_id}.ogg
│   │   │   - Use pre-loaded model to transcribe, return transcript text
│   │   │   - Delete temp file in finally block
│   │   │   - Return "transcription failed" on any exception
│   │   ├── Input:
│   │   │   - voice: Voice object from Telegram update
│   │   │   - bot: Bot instance for downloading files
│   │   └── Output:
│   │       - str: transcribed text or "transcription failed" on error
│   └── class TelegramClient [x]
│       ├── method __init__() [x]
│       │   ├── Functionality:
│       │   │   - Initialize TelegramClient with token from env or parameter
│       │   │   - Initialize Bot instance
│       │   │   - Load offset from file if offset_path provided
│       │   ├── Input:
│       │   │   - token: Optional[str]
│       │   │   - offset_path: Optional[str]
│       │   └── Output:
│       │       - None
│       │       - Raises ValueError if token is missing
│       ├── method send_message() [x]
│       │   ├── Functionality:
│       │   │   - Send text message to chat_id
│       │   │   - Forward extra kwargs to Bot.send_message
│       │   │   - Validate text is not empty
│       │   │   - Split text exceeding 4096 chars and return split metadata
│       │   │   - Use MarkdownV2-aware splitter so bold/italic/code entities are not torn across chunks
│       │   ├── Input:
│       │   │   - chat_id: int
│       │   │   - text: str
│       │   │   - **kwargs: Any
│       │   └── Output:
│       │       - Message object or dict with message_id, message_ids, split on success
│       │       - Raises ValueError if text is empty
│       │       - Raises TelegramError on API failure
│       ├── method send_reply_keyboard() [x]
│       │   ├── Functionality:
│       │   │   - Send message with reply keyboard
│       │   │   - Convert keyboard list to ReplyKeyboardMarkup
│       │   │   - Validate text and keyboard are not empty
│       │   ├── Input:
│       │   │   - chat_id: int
│       │   │   - text: str
│       │   │   - keyboard: List[List[str]]
│       │   │   - resize_keyboard: bool = True
│       │   │   - one_time_keyboard: bool = False
│       │   │   - **kwargs: Any
│       │   └── Output:
│       │       - Message object from Telegram API
│       │       - Raises ValueError if text or keyboard is empty
│       ├── method remove_reply_keyboard() [x]
│       │   ├── Functionality:
│       │   │   - Send message that removes reply keyboard
│       │   │   - Use ReplyKeyboardRemove markup
│       │   │   - Validate text is not empty
│       │   ├── Input:
│       │   │   - chat_id: int
│       │   │   - text: str = "Keyboard removed."
│       │   │   - **kwargs: Any
│       │   └── Output:
│       │       - Message object from Telegram API
│       │       - Raises ValueError if text is empty
│       ├── method get_updates() [x]
│       │   ├── Functionality:
│       │   │   - Fetch recent updates from Telegram
│       │   │   - Track last update ID to avoid duplicates
│       │   │   - Optionally filter by chat_id
│       │   │   - Save offset to file if offset_path provided
│       │   ├── Input:
│       │   │   - chat_id: Optional[int] = None
│       │   │   - limit: int = 10
│       │   │   - timeout: int = 0
│       │   └── Output:
│       │       - List[Update] from Telegram API
│       │       - Raises TelegramError on API failure
│       ├── method _match_chat() [x]
│       │   ├── Functionality:
│       │   │   - Static method to check if update matches chat_id
│       │   ├── Input:
│       │   │   - update: Update
│       │   │   - chat_id: Optional[int]
│       │   └── Output:
│       │       - bool
│       ├── method _load_offset() [x]
│       │   ├── Functionality:
│       │   │   - Load last update ID from offset file
│       │   ├── Input:
│       │   │   - None
│       │   └── Output:
│       │       - int (offset value, 0 if file missing or invalid)
│       ├── method _save_offset() [x]
│       │   ├── Functionality:
│       │   │   - Save last update ID to offset file
│       │   ├── Input:
│       │   │   - None
│       │   └── Output:
│       │       - None
│       │       - Logs warning if save fails
│       └── method shutdown() [x]
│           ├── Functionality:
│           │   - Clean up underlying bot session
│           ├── Input:
│           │   - None
│           └── Output:
│               - None
│       └── method send_file() [x]
│           ├── Functionality:
│           │   - Send file to Telegram chat
│           │   - Construct full file path from uploads folder and filename
│           │   - Validate file exists at the path
│           │   - Validate file_type is one of: document, photo, video, audio
│           │   - Use appropriate python-telegram-bot method based on file_type
│           │   - Pass file using InputFile from local path
│           │   - Handle file not found, invalid file type, and Telegram API errors
│           │   - Log file sending attempts and results
│           ├── Input:
│           │   - chat_id: int
│           │   - filename: str
│           │   - file_type: str
│           │   - caption: Optional[str] = None
│           │   - **kwargs: Any
│           └── Output:
│               - Message object from Telegram API
│               - Raises ValueError if file not found or invalid file_type
│               - Raises TelegramError on API failure
├── test.py [x]
│   └── function main()
│       ├── Functionality:
│       │   - Run mock smoke test if TELEGRAM_BOT_TOKEN not set
│       │   - Run real integration test if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID set
│       ├── Input:
│       │   - None (uses environment variables)
│       └── Output:
│           - None
│           - Prints test results to stdout
├── get_ids.py [x]
│   └── function main()
│       ├── Functionality:
│       │   - Fetch latest Telegram updates
│       │   - Print chat IDs and message text
│       │   - Help users discover their chat ID
│       ├── Input:
│       │   - None (uses TELEGRAM_BOT_TOKEN env var)
│       └── Output:
│           - None
│           - Prints chat IDs to stdout
└── README.md [x]
    ├── Functionality:
    │   - Document usage of TelegramClient
    │   - Provide examples for all methods
    ├── Input:
    │   - None
    └── Output:
        - Markdown documentation file
tests/
├── __init__.py [x]
├── test_api.py [x]
│   ├── function test_health_check() [x]
│   ├── function test_send_message() [x]
│   ├── function test_send_message_long_text_split() [x]
│   ├── function test_send_message_short_text_not_split() [x]
│   ├── function test_send_reply_keyboard() [x]
│   ├── function test_remove_reply_keyboard() [x]
│   ├── function test_get_updates() [x]
│   ├── function test_get_chat_ids() [x]
│   ├── function test_error_handling() [x]
│   ├── function test_send_file() [x]
│   ├── function test_send_file_not_found() [x]
│   ├── function test_send_file_invalid_type() [x]
│   ├── function test_send_file_document() [x]
│   ├── function test_send_file_photo() [x]
│   ├── function test_send_file_video() [x]
│   └── function test_send_file_audio() [x]
└── test_utils.py [x]
    ├── function test_split_text_safely_under_limit() [x]
    ├── function test_split_text_safely_over_limit() [x]
    ├── function test_split_text_safely_at_limit() [x]
    ├── function test_split_text_safely_no_safe_boundary() [x]
    ├── function test_split_markdownv2_safely_keeps_entities_intact() [x]
    ├── function test_send_message_long_text_splits_markdownv2_entities_safely() [x]
    ├── function test_telegram_client_send_message_long_text() [x]
    ├── function test_transcribe_voice_singleton() [ ]
    ├── function test_transcribe_voice_cpu_device() [ ]
    └── function test_transcribe_voice_model_from_env() [ ]
.dockerignore [x]
├── Functionality:
│   - Optionally exclude uploads folder contents from Docker image
├── Input:
│   - None
└── Output:
    - Updated .dockerignore file
Dockerfile [*]
├── Functionality:
│   - Add apt-get install -y ffmpeg before pip install
│   - ffmpeg is required for OpenAI Whisper audio processing
│   - Add RUN mkdir -p /app/uploads after WORKDIR command
│   - Add RUN chown -R appuser:appuser /app/uploads for permissions
│   - Add build ARG WHISPER_MODEL with default value "base"
│   - Replace single pip install with two separate RUN steps:
│   │   - First: install CPU-only torch from PyTorch CPU wheel index
│   │   - Second: install requirements.txt (torch already satisfied)
│   - Add RUN step to pre-download Whisper model at build time
│   - Fix ownership of /root/.cache/whisper so appuser can read it
├── Input:
│   - Build ARG WHISPER_MODEL (default: "base")
└── Output:
    - Updated Dockerfile with CPU-only torch and pre-baked Whisper model
docker-compose.yml [*]
├── Functionality:
│   - Define service configuration for Telegram API
│   - Remove WHISPER_DEVICE environment variable (CPU now hardcoded)
│   - Keep WHISPER_MODEL environment variable (matches build ARG)
│   - No named volume needed for Whisper cache (model baked into image)
├── Input:
│   - None
└── Output:
    - Updated docker-compose.yml without WHISPER_DEVICE
README.md [*]
├── Functionality:
│   - Update with FastAPI and Docker instructions
│   - Add local run instructions with uvicorn
│   - Add Docker build and run instructions
│   - Add API endpoint documentation with examples
│   - Add environment variable requirements
│   - Add WHISPER_MODEL and WHISPER_DEVICE env vars documentation
│   - Add voice transcription feature section
│   - Add file sending feature section
│   - Document uploads/ folder and Docker volume mounting
│   - Document UPLOADS_PATH environment variable
│   - Provide example docker-compose volume mount
│   - Provide example API request for sending a file
├── Input:
│   - None
└── Output:
    - Updated Markdown documentation file
requirements.txt [*]
├── Functionality:
│   - Add openai-whisper>=20231117 dependency
│   - Whisper is required for voice message transcription
├── Input:
│   - None
└── Output:
    - Updated requirements.txt with openai-whisper
.settings [ ]
    ├── Functionality:
    │   - Define non-secret environment variables for the project
    │   - Include UPLOADS_PATH with default value "uploads"
    ├── Input:
    │   - None
    └── Output:
        - Configuration file with environment variable definitions
