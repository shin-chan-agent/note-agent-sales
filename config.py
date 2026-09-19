# Geminiモデル設定
GEMINI_MODEL_ARTICLE = "gemini-2.5-flash"
GEMINI_MODEL_EVALUATION = "gemini-2.5-flash"
GEMINI_MODEL_REWRITE = "gemini-2.5-flash"
GEMINI_MODEL_SNS = "gemini-2.5-flash"
GEMINI_MODEL_LATEST = "gemini-2.5-flash"


# 品質チェック設定
MIN_SCORE = 90
MIN_SEO_SCORE = 90
MAX_REWRITE = 3
MAX_ARTICLE_LENGTH = 20000


# APIリトライ設定
MAX_RETRY = 3
GOOGLE_SEARCH_RETRY_WAIT = 5
GEMINI_RETRY_WAIT = 30
EVALUATION_RETRY_WAIT = 5


# AI知識DB更新設定
KNOWLEDGE_UPDATE_INTERVAL_DAYS = 7
MAX_KNOWLEDGE_AGE_DAYS = 14
MISSING_LIMIT = 2


AI_SERVICES = {
    "chatgpt": {
        "name": "ChatGPT",
        "enabled": True,
        "official_domains": [
            "openai.com",
            "platform.openai.com",
            "help.openai.com",
        ],
    },

    "gemini": {
        "name": "Gemini",
        "enabled": True,
        "official_domains": [
            "ai.google.dev",
            "cloud.google.com",
            "deepmind.google",
            "developers.googleblog.com",
        ],
    },

    "claude": {
        "name": "Claude",
        "enabled": True,
        "official_domains": [
            "anthropic.com",
            "docs.anthropic.com",
        ],
    },

    "canva": {
        "name": "Canva",
        "enabled": True,
        "official_domains": [
            "canva.com",
            "canva.dev",
        ],
    },

    "capcut": {
        "name": "CapCut",
        "enabled": True,
        "official_domains": [
            "capcut.com",
            "support.capcut.com",
        ],
    },
}


# ============================================================
# テーマごとの最新情報取得対象サービス
# ============================================================

THEME_SERVICES = {
    "AI副業・収益化": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "ショート動画": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "SNS運用": [
        "chatgpt",
        "gemini",
        "canva",
        "capcut",
    ],

    "コンテンツ販売": [
        "chatgpt",
        "gemini",
    ],

    "生成AI実践活用": [
        "chatgpt",
        "gemini",
        "claude",
        "canva",
        "capcut",
    ],
}