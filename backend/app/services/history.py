"""History helpers for converting database models to API responses."""

from pathlib import Path
from typing import Dict, Iterable, Optional

from sqlmodel import Session, select

from ..db.models import Description


def _image_url(relative_path: Optional[str]) -> Optional[str]:
    if not relative_path:
        return None
    return f"/static/{Path(relative_path).as_posix()}"


def history_item_from_db(description: Description) -> Dict[str, str | None]:
    return {
        "id": str(description.id),
        "timestamp": description.timestamp.isoformat(),
        "source": description.source,
        "style": description.style,
        "summary": description.content[:200] + ("..." if len(description.content) > 200 else ""),
        "full_description": description.content,
        "image_url": _image_url(description.image_path),
    }


def get_history_for_user(session: Session, user_id: int, limit: int = 20) -> Iterable[Dict[str, str]]:
    statement = (
        select(Description)
        .where(Description.user_id == user_id)
        .order_by(Description.timestamp.desc())
        .limit(limit)
    )
    return [history_item_from_db(desc) for desc in session.exec(statement)]
