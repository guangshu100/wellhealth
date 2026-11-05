"""Conservative display policy, not a claim of clinical validation."""
import re
from .schemas import DISCLAIMER

RED_FLAGS = [
    r"(?:确诊|肯定是|一定是|你患了|你得了).{0,12}(?:糖尿病|高血压|癌症|心脏病|肾病)",
    r"(?:服用|吃|注射|使用).{0,12}\d+(?:\.\d+)?\s*(?:mg|毫克|片|粒|单位|毫升)",
    r"(?:自行|立即|马上)(?:停药|加药|减药|加量|减量)",
]


def display_result(result):
    """Unsafe expert text never enters events or the summarizer input."""
    text = str(result.get("content", "")).strip()
    if result.get("blocked") or not text or len(text) > 24000:
        return None
    if any(re.search(pattern, text, re.I) for pattern in RED_FLAGS):
        return None
    if DISCLAIMER not in text:
        text += "\n\n" + DISCLAIMER
    sources = []
    for item in result.get("sources", [])[:5]:
        if isinstance(item, dict) and item.get("title"):
            # Deliberately omit raw retrieved documents, hidden metadata and arbitrary URLs.
            sources.append({"title": str(item["title"])[:160]})
    return {"content":text, "sources":sources, "safety":{"level":"checked", "disclaimer":DISCLAIMER}}
