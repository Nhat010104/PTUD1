"""FastAPI application entrypoint."""

import re
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi.staticfiles import StaticFiles

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from .config import get_settings
from .db.models import Description, PasswordResetToken, User
from .db.session import engine, get_session, init_db
from .schemas import (
    DescriptionResponse,
    GenerateTextRequest,
    HistoryItem,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserOut,
)
from .services import auth, content, history as history_service, seo
from sqlmodel import Session, select


def is_email(identifier: str) -> bool:
    """Kiểm tra xem identifier có phải là email không."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, identifier))


def is_phone_number(identifier: str) -> bool:
    """Kiểm tra xem identifier có phải là số điện thoại không."""
    phone_pattern = r'^[0-9]{10,11}$'
    return bool(re.match(phone_pattern, identifier))


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
            admin = User(email=email, phone_number=None, hashed_password=auth.hash_password("123456"))
            session.add(admin)
            session.commit()


def get_current_user(
    token: str = Depends(auth.optional_oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    if not token:
        raise HTTPException(status_code=401, detail="Yêu cầu đăng nhập")
    identifier = auth.decode_access_token(token)
    if not identifier:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    
    # Tìm user bằng email hoặc số điện thoại
    user = None
    if is_email(identifier):
        user = session.exec(select(User).where(User.email == identifier)).first()
    elif is_phone_number(identifier):
        user = session.exec(select(User).where(User.phone_number == identifier)).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Không tìm thấy người dùng")
    return user


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: UserCreate, session: Session = Depends(get_session)) -> TokenResponse:
    identifier = payload.identifier.strip()
    
    # Xác định loại identifier
    if is_email(identifier):
        email = identifier.lower()
        phone_number = None
        existing = session.exec(select(User).where(User.email == email)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email đã tồn tại")
    elif is_phone_number(identifier):
        email = None
        phone_number = identifier
        existing = session.exec(select(User).where(User.phone_number == phone_number)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Số điện thoại đã tồn tại")
    else:
        raise HTTPException(status_code=400, detail="Vui lòng nhập email hoặc số điện thoại hợp lệ")
    
    user = User(email=email, phone_number=phone_number, hashed_password=auth.hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    
    token_subject = email if email else phone_number
    token = auth.create_access_token(token_subject)
    return TokenResponse(access_token=token)


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: UserCreate, session: Session = Depends(get_session)) -> TokenResponse:
    identifier = payload.identifier.strip()
    
    # Tìm user bằng email hoặc số điện thoại
    user = None
    if is_email(identifier):
        user = session.exec(select(User).where(User.email == identifier.lower())).first()
    elif is_phone_number(identifier):
        user = session.exec(select(User).where(User.phone_number == identifier)).first()
    
    if not user or not auth.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không chính xác")
    
    token_subject = user.email if user.email else user.phone_number
    token = auth.create_access_token(token_subject)
    return TokenResponse(access_token=token)


@app.post("/auth/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> ForgotPasswordResponse:
    identifier = payload.identifier.strip()
    message = "Nếu tài khoản tồn tại, mã đặt lại đã được tạo."
    reset_token: Optional[str] = None

    # Tìm user bằng email hoặc số điện thoại
    user = None
    if is_email(identifier):
        user = session.exec(select(User).where(User.email == identifier.lower())).first()
    elif is_phone_number(identifier):
        user = session.exec(select(User).where(User.phone_number == identifier)).first()
    
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
    identifier = payload.identifier.strip()
    token_value = payload.token.strip()
    
    # Tìm user bằng email hoặc số điện thoại
    user = None
    if is_email(identifier):
        user = session.exec(select(User).where(User.email == identifier.lower())).first()
    elif is_phone_number(identifier):
        user = session.exec(select(User).where(User.phone_number == identifier)).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Tài khoản hoặc mã đặt lại không hợp lệ")

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
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        phone_number=current_user.phone_number,
        created_at=current_user.created_at.isoformat()
    )


def get_current_user_optional(
    token: Optional[str] = Depends(auth.optional_oauth2_scheme),
    session: Session = Depends(get_session),
) -> Optional[User]:
    if not token:
        return None
    identifier = auth.decode_access_token(token)
    if not identifier:
        return None
    
    # Tìm user bằng email hoặc số điện thoại
    user = None
    if is_email(identifier):
        user = session.exec(select(User).where(User.email == identifier)).first()
    elif is_phone_number(identifier):
        user = session.exec(select(User).where(User.phone_number == identifier)).first()
    
    return user


@app.post("/api/descriptions/image", response_model=DescriptionResponse)
async def generate_description_from_image(
    file: UploadFile = File(...),
    style: str = Form("Tiếp thị"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session),
) -> DescriptionResponse:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")

    try:
        image_bytes = await file.read()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=400, detail="Tệp hình ảnh không hợp lệ") from exc

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png"}:
        suffix = ".jpg"
    filename = f"{uuid4().hex}{suffix}"
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
        user_id=current_user.id if current_user else None,
        source="image",
        style=style,
        content=description,
        image_path=relative_image_path.as_posix() if image_path else None,
    )
    history_payload = None
    if current_user:
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        history_payload = history_service.history_item_from_db(db_entry)

    return DescriptionResponse(
        description=description,
        seo_score=score,
        seo_factors=factors,
        history_id=history_payload["id"] if history_payload else "",
        timestamp=history_payload["timestamp"] if history_payload else datetime.utcnow().isoformat(),
        style=style,
        source="image",
        image_url=history_payload.get("image_url") if history_payload else None,
    )


@app.post("/api/descriptions/text", response_model=DescriptionResponse)
async def generate_description_from_text(
    payload: GenerateTextRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session),
) -> DescriptionResponse:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Gemini API key not configured.")

    description = content.generate_from_text(settings.gemini_api_key, payload.product_info, payload.style)
    if not description:
        raise HTTPException(status_code=502, detail="Không tạo được mô tả từ văn bản")

    score, factors = seo.calculate_seo_score(description)
    db_entry = Description(user_id=current_user.id if current_user else None, source="text", style=payload.style, content=description)

    history_payload = None
    if current_user:
        session.add(db_entry)
        session.commit()
        session.refresh(db_entry)
        history_payload = history_service.history_item_from_db(db_entry)

    return DescriptionResponse(
        description=description,
        seo_score=score,
        seo_factors=factors,
        history_id=history_payload["id"] if history_payload else "",
        timestamp=history_payload["timestamp"] if history_payload else datetime.utcnow().isoformat(),
        style=payload.style,
        source="text",
        image_url=history_payload.get("image_url") if history_payload else None,
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


@app.get("/api/styles")
def get_styles() -> JSONResponse:
    """Return supported writing styles."""
    return JSONResponse(sorted(content.STYLE_PROMPTS.keys()))



