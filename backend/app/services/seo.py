"""Utilities for calculating simple SEO heuristics."""

from typing import List, Tuple


KEYWORDS = ['chất lượng', 'tươi', 'ngon', 'sạch', 'dinh dưỡng', 'vitamin', 'tự nhiên']
CTA_WORDS = ['đặt hàng', 'mua ngay', 'gọi ngay', 'liên hệ']
EMOJIS = ['🍎', '🍊', '🍇', '🍌', '🍓', '✨', '💎', '🌟']


def calculate_seo_score(text: str) -> Tuple[int, List[str]]:
    """Apply heuristic scoring similar to the original Streamlit implementation."""
    score = 0
    factors: List[str] = []

    word_count = len(text.split())
    if 100 <= word_count <= 500:
        score += 30
        factors.append("✅ Độ dài phù hợp")
    else:
        factors.append(f"⚠️ Độ dài: {word_count} từ (nên 100-500)")

    found_keywords = sum(1 for kw in KEYWORDS if kw.lower() in text.lower())
    score += min(found_keywords * 5, 25)
    factors.append(f"✅ Từ khóa: {found_keywords}/{len(KEYWORDS)}")

    hashtag_count = text.count('#')
    if hashtag_count >= 3:
        score += 15
        factors.append("✅ Có hashtags")
    else:
        factors.append("⚠️ Thiếu hashtags")

    if any(cta in text.lower() for cta in CTA_WORDS):
        score += 15
        factors.append("✅ Có call-to-action")
    else:
        factors.append("⚠️ Thiếu call-to-action")

    if any(char in text for char in EMOJIS):
        score += 15
        factors.append("✅ Có emoji")
    else:
        factors.append("⚠️ Thiếu emoji")

    return score, factors
