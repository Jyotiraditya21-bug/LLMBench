from typing import Optional

try:
    from google import genai
    from google.genai import types

    HAS_GOOGLE_GENAI = True
except ImportError:
    genai = None
    types = None
    HAS_GOOGLE_GENAI = False


async def generate_google_text(
    *,
    api_key: str,
    model: str,
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_output_tokens: Optional[int] = None,
    json_output: bool = False,
) -> str:
    if not HAS_GOOGLE_GENAI:
        raise RuntimeError("google-genai is not installed")

    config_values = {
        "temperature": temperature,
        "system_instruction": system_prompt,
    }
    if max_output_tokens is not None:
        config_values["max_output_tokens"] = max_output_tokens
    if json_output:
        config_values["response_mime_type"] = "application/json"

    client = genai.Client(api_key=api_key)
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_values),
        )
        return response.text or ""
    finally:
        await client.aio.aclose()
