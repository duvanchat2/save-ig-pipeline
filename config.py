import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

BASE_DIR = Path(__file__).parent

# Notion
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_RAW_SAVES_DB_ID = os.getenv("NOTION_RAW_SAVES_DB_ID", "")
NOTION_CONTENT_IDEAS_DB_ID = os.getenv("NOTION_CONTENT_IDEAS_DB_ID", "")

# Meta / Instagram Graph API
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("IG_USER_ID", "")

# Claude API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# AssemblyAI
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY", "")

# Pipeline settings
CONTENT_NICHE = os.getenv("CONTENT_NICHE", "beginner AI solo founders")
CONTENT_PILLARS = [
    p.strip()
    for p in os.getenv("CONTENT_PILLARS", "Outreach,Proof,Tools,Process").split(",")
    if p.strip()
]

STATE_FILE = BASE_DIR / "state.json"
