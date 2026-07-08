import os
from dotenv import load_dotenv

load_dotenv()

# ---- LLM settings ----
# Choose "anthropic", "openai", "openrouter", or "google"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash")

# ---- Storage ----
DB_PATH = os.getenv("DB_PATH", "storage/watchlists.db")
CACHE_DIR = os.getenv("CACHE_DIR", "storage/cache")

# ---- Defaults ----
DEFAULT_PERIOD = "1y"
DEFAULT_INTERVAL = "1d"
RISK_FREE_RATE = 0.04   # annual risk-free rate assumption, used in Sharpe ratio
TRADING_DAYS = 252      # trading days per year, used for annualizing returns/volatility
