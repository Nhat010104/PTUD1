"""FastAPI application entrypoint."""

from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi.staticfiles import StaticFiles

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image, UnidentifiedImageError

from .config import get_settings
from .db.models import Description, User
from .db.session import engine, get_session, init_db
from .schemas import (
    DescriptionResponse,
    ExportRequest,
    GenerateTextRequest,
    HistoryItem,
    TokenResponse,
    UserCreate,
    UserOut,
)
from .services import auth, content, exporters, history as history_service, seo, templates
from sqlmodel import Session, select


app = FastAPI(title="AI Product Description Service")

STATIC_DIR = Path("static/images")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_admin_user()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> JSONResponse:
    """Simple health-check endpoint."""
    return JSONResponse({"status": "ok"})


def seed_admin_user() -> None:
    with Session(engine) as session:
        email = "admin@example.com"
        existing = session.exec(select(User).where(User.email == email)).first()
        if not existing:
            admin = User(email=email, hashed_password=auth.hash_password("123456"))
            session.add(admin)
            session.commit()


def get_current_user(
    token: str = Depends(auth.oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    email = auth.decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Không tìm thấy người dùng")
    return user


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: UserCreate, session: Session = Depends(get_session)) -> TokenResponse:
    email = payload.email.strip().lower()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    user = User(email=email, hashed_password=auth.hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    token = auth.create_access_token(user.email)
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: UserCreate, session: Session = Depends(get_session)) -> TokenResponse:
    email = payload.email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không chính xác")
    token = auth.create_access_token(user.email)
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=current_user.id, email=current_user.email, created_at=current_user.created_at.isoformat())


@app.post("/api/descriptions/image", response_model=DescriptionResponse)
async def generate_description_from_image(
    file: UploadFile = File(...),
    style: str = Form("Marketing"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DescriptionResponse:
    settings = get_settings()

    try:
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Tệp hình ảnh không hợp lệ") from exc

    filename = f"{current_user.id}_{session.exec(select(Description).count())}_{file.filename or 'upload' }"
    image_path: Optional[Path] = None
    try:
        image_path = STATIC_DIR / filename
        image.save(image_path)
    except Exception:  # noqa: BLE001
        image_path = None

    description = content.generate_from_image(settings.gemini_api_key, image, style)
    if not description:
        raise HTTPException(status_code=502, detail="Không tạo được mô tả từ hình ảnh")

    score, factors = seo.calculate_seo_score(description)
    db_entry = Description(
        user_id=current_user.id,
        source="image",
        style=style,
        content=description,
        image_path=str(image_path) if image_path else None,
    )
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    entry = history_service.history_item_from_db(db_entry)

    return DescriptionResponse(
        description=description,
        seo_score=score,
        seo_factors=factors,
        history_id=entry["id"],
        timestamp=entry["timestamp"],
        style=entry["style"],
        source=entry["source"],
    )


@app.post("/api/descriptions/text", response_model=DescriptionResponse)
async def generate_description_from_text(
    payload: GenerateTextRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DescriptionResponse:
    settings = get_settings()

    description = content.generate_from_text(settings.gemini_api_key, payload.product_info, payload.style)
    if not description:
        raise HTTPException(status_code=502, detail="Không tạo được mô tả từ văn bản")

    score, factors = seo.calculate_seo_score(description)
    db_entry = Description(user_id=current_user.id, source="text", style=payload.style, content=description)
    session.add(db_entry)
    session.commit()
    session.refresh(db_entry)
    entry = history_service.history_item_from_db(db_entry)

    return DescriptionResponse(
        description=description,
        seo_score=score,
        seo_factors=factors,
        history_id=entry["id"],
        timestamp=entry["timestamp"],
        style=entry["style"],
        source=entry["source"],
    )


@app.get("/api/history", response_model=list[HistoryItem])
def get_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[HistoryItem]:
    """Return recent description history."""
    entries = history_service.get_history_for_user(session, current_user.id, limit)
    return [HistoryItem(**entry) for entry in entries]


@app.get("/api/templates")
def get_templates() -> JSONResponse:
    """Return the list of predefined templates."""
    return JSONResponse(templates.TEMPLATES)


@app.get("/api/styles")
def get_styles() -> JSONResponse:
    """Return supported writing styles."""
    return JSONResponse(sorted(content.STYLE_PROMPTS.keys()))


@app.post("/api/export/docx")
def download_docx(payload: ExportRequest) -> StreamingResponse:
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="Nội dung mô tả không được để trống")
    buffer = exporters.export_docx(payload.description)
    headers = {
        "Content-Disposition": "attachment; filename=description.docx"
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


@app.post("/api/export/pdf")
def download_pdf(payload: ExportRequest) -> StreamingResponse:
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="Nội dung mô tả không được để trống")
    buffer = exporters.export_pdf(payload.description)
    headers = {
        "Content-Disposition": "attachment; filename=description.pdf"
    }
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers=headers,
    )
