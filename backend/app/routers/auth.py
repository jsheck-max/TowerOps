from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, Organization
from app.schemas import LoginRequest, TokenResponse, UserResponse, OrgCreate
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register_organization(data: OrgCreate, db: Session = Depends(get_db)):
    """Register a new organization with an admin user."""
    existing = db.query(User).filter(User.email == data.admin_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    org = Organization(name=data.name)
    db.add(org)
    db.flush()

    user = User(
        org_id=org.id,
        email=data.admin_email,
        hashed_password=hash_password(data.admin_password),
        full_name=data.admin_name,
        role="admin",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login and receive JWT token."""
    logger.warning(f"LOGIN ATTEMPT: email={data.email!r} password_len={len(data.password)} password_repr={data.password!r}")
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        logger.warning("LOGIN FAIL: user not found")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.warning(f"USER FOUND: {user.email}, hash={user.hashed_password[:20]}...")
    try:
        result = verify_password(data.password, user.hashed_password)
        logger.warning(f"VERIFY RESULT: {result}")
    except Exception as e:
        logger.warning(f"VERIFY EXCEPTION: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not result:
        logger.warning("LOGIN FAIL: password mismatch")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "org_id": str(user.org_id)})
    logger.warning("LOGIN SUCCESS")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return current_user
