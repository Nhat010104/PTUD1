"""FastAPI application entrypoint."""

from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi.staticfiles import StaticFiles

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image, UnidentifiedImageError

from .config import get_settings
from .db.models import AgentMessage as AgentMessageModel
from .db.models import AgentSession as AgentSessionModel
from .db.models import Description, PasswordResetToken, User
from .db.session import engine, get_session, init_db
from .schemas import (
    DescriptionResponse,
    ExportRequest,
    GenerateTextRequest,
    HistoryItem,
    AgentRequest,
    AgentMessagePayload,
    AgentResponsePayload,
    AgentSessionDetail,
    AgentSessionSummary,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserOut,
)
from .services import agent as agent_service
from .services import auth, content, exporters, history as history_service, seo, templates
from sqlmodel import Session, select


app = FastAPI(title="AI Product Description Service")

BASE_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
IMAGES_DIR = BASE_STATIC_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=BASE_STATIC_DIR), name="static")


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


@app.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> ForgotPasswordResponse:
    email = payload.email.strip().lower()
    message = "Nếu email tồn tại, mã đặt lại đã được tạo."
    reset_token: Optional[str] = None

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return ForgotPasswordResponse(message=message, reset_token=reset_token)

    existing_tokens = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.used.is_(False))
    ).all()
    for token in existing_tokens:
        token.used = True
        session.add(token)

    raw_token, token_hash = auth.generate_reset_token()
    reset_entry = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=30),
    )
    session.add(reset_entry)
    session.commit()

    message = "Mã đặt lại mật khẩu đã được tạo."
    reset_token = raw_token

    return ForgotPasswordResponse(message=message, reset_token=reset_token)


@app.post("/auth/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    session: Session = Depends(get_session),
) -> MessageResponse:
    email = payload.email.strip().lower()
    token_value = payload.token.strip()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Email hoặc mã đặt lại không hợp lệ")

    tokens = session.exec(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at >= datetime.utcnow(),
        )
    ).all()

    matched_token = None
    for token in tokens:
        if auth.match_reset_token(token_value, token.token_hash):
            matched_token = token
            break

    if not matched_token:
        raise HTTPException(status_code=400, detail="Mã đặt lại không hợp lệ hoặc đã hết hạn")

    user.hashed_password = auth.hash_password(payload.new_password)
    matched_token.used = True
    session.add(user)
    session.add(matched_token)
    session.commit()

    return MessageResponse(message="Mật khẩu đã được cập nhật. Vui lòng đăng nhập lại.")


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

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        suffix = ".jpg"
    filename = f"{current_user.id}_{uuid4().hex}{suffix}"
    relative_image_path = Path("images") / filename
    image_path: Optional[Path] = None
    try:
        image_path = IMAGES_DIR / filename
        save_kwargs = {}
        if suffix in {".jpg", ".jpeg"}:
            save_kwargs["format"] = "JPEG"
        elif suffix == ".png":
            save_kwargs["format"] = "PNG"
        image.save(image_path, **save_kwargs)
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
        image_path=relative_image_path.as_posix() if image_path else None,
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
        image_url=entry.get("image_url"),
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
        image_url=entry.get("image_url"),
    )


@app.post("/api/agent/chat", response_model=AgentResponsePayload)
def agent_chat(
    payload: AgentRequest,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AgentResponsePayload:
    settings = get_settings()

    if not payload.messages:
        raise HTTPException(status_code=400, detail="Thiếu hội thoại đầu vào")

    latest_message = payload.messages[-1]
    if latest_message.role != "user":
        raise HTTPException(status_code=400, detail="Tin nhắn cuối phải thuộc về người dùng")

    agent_session: Optional[AgentSessionModel] = None
    if payload.session_id is not None:
        agent_session = session.get(AgentSessionModel, payload.session_id)
        if not agent_session or agent_session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Không tìm thấy phiên agent")
    else:
        title = agent_service.generate_session_title(latest_message.content)
        agent_session = AgentSessionModel(user_id=current_user.id, title=title)
        session.add(agent_session)
        session.commit()
        session.refresh(agent_session)

    stored_messages = session.exec(
        select(AgentMessageModel)
        .where(AgentMessageModel.session_id == agent_session.id)
        .order_by(AgentMessageModel.created_at.asc())
    ).all()

    conversation = [
        agent_service.AgentMessage(role=message.role, content=message.content)
        for message in stored_messages
    ]
    conversation.append(agent_service.AgentMessage(role=latest_message.role, content=latest_message.content))

    result = agent_service.run_agent(settings.gemini_api_key, conversation)

    session.add(
        AgentMessageModel(session_id=agent_session.id, role="user", content=latest_message.content)
    )
    session.add(
        AgentMessageModel(session_id=agent_session.id, role="assistant", content=result.reply)
    )

    agent_session.updated_at = datetime.utcnow()

    history_id = None
    timestamp = None
    image_url = None
    source = "agent"

    if result.finished and result.description:
        db_entry = Description(
            user_id=current_user.id,
            source=source,
            style=result.style or "Marketing",
            content=result.description,
            image_path=None,
        )
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        entry = history_service.history_item_from_db(db_entry)
        history_id = entry["id"]
        timestamp = entry["timestamp"]
        image_url = entry.get("image_url")

    session.commit()

    return AgentResponsePayload(
        reply=result.reply,
        finished=result.finished,
        description=result.description,
        seo_score=result.seo_score,
        seo_factors=result.seo_factors,
        history_id=history_id,
        timestamp=timestamp,
        style=result.style,
        source=source if result.finished else None,
        image_url=image_url,
        session_id=agent_session.id,
        session_title=agent_session.title,
    )


@app.get("/api/agent/sessions", response_model=list[AgentSessionSummary])
def list_agent_sessions(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[AgentSessionSummary]:
    sessions = session.exec(
        select(AgentSessionModel)
        .where(AgentSessionModel.user_id == current_user.id)
        .order_by(AgentSessionModel.updated_at.desc())
    ).all()
    return [
        AgentSessionSummary(id=item.id, title=item.title, updated_at=item.updated_at.isoformat())
        for item in sessions
    ]


@app.get("/api/agent/sessions/{session_id}", response_model=AgentSessionDetail)
def get_agent_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> AgentSessionDetail:
    agent_session = session.get(AgentSessionModel, session_id)
    if not agent_session or agent_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên agent")

    messages = session.exec(
        select(AgentMessageModel)
        .where(AgentMessageModel.session_id == session_id)
        .order_by(AgentMessageModel.created_at.asc())
    ).all()

    payload = [
        AgentMessagePayload(role=message.role, content=message.content)
        for message in messages
    ]

    return AgentSessionDetail(
        id=agent_session.id,
        title=agent_session.title,
        updated_at=agent_session.updated_at.isoformat(),
        messages=payload,
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
