"""
Response generation via the OpenAI GPT-4o API.

The skeleton's personality is injected as the system prompt.
All responses are in Slovak and kept to 1-2 sentences.
"""

from typing import Optional

from openai import OpenAI

from config import GPT_MODEL, OPENAI_API_KEY, load_personality
from utils.logger import get_logger

log = get_logger()

_client = OpenAI(api_key=OPENAI_API_KEY)

_INSTRUCTION_SUFFIX = (
    "\n\nDolezite pravidla: Vzdy odpovedaj v slovenskom jazyku. "
    "Odpoved musi byt kratka -- maximalne 1 az 2 vety. "
    "Zostan v postave za kazdych okolnosti."
)


def generate_response(user_text: str) -> Optional[str]:
    """
    Generate a short in-character Slovak response to user_text.

    Returns the response string, or None on failure.
    """
    system_prompt = load_personality() + _INSTRUCTION_SUFFIX

    try:
        completion = _client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            max_tokens=120,
            temperature=0.85,
        )
        response = completion.choices[0].message.content.strip()
        log.info("Response: %s", response)
        return response if response else None

    except Exception as exc:
        log.error("GPT response generation failed: %s", exc)
        return None
