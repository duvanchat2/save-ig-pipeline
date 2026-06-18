import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

BASE_DIR = Path(__file__).parent

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_RAW_SAVES_DB_ID = os.getenv("NOTION_RAW_SAVES_DB_ID", "")
NOTION_CONTENT_IDEAS_DB_ID = os.getenv("NOTION_CONTENT_IDEAS_DB_ID", "")

# Instagram
IG_USERNAME = os.getenv("IG_USERNAME", "")
IG_SESSION_FILE = Path(os.getenv("IG_SESSION_FILE", str(BASE_DIR / "ig_session.json")))

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# AssemblyAI
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "34d09095781945cabf5d95a87998d336")

# Pipeline settings
INSTAGRAM_COLLECTIONS = [
    c.strip()
    for c in os.getenv("INSTAGRAM_COLLECTIONS", "Content Ideas,Inspiration").split(",")
    if c.strip()
]
CONTENT_NICHE = os.getenv("CONTENT_NICHE", "beginner AI solo founders")
CONTENT_PILLARS = [
    p.strip()
    for p in os.getenv("CONTENT_PILLARS", "Outreach,Proof,Tools,Process").split(",")
    if p.strip()
]

STATE_FILE = BASE_DIR / "state.json"
