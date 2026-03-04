from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.cost_entry import Integration, LaborRate
from app.utils.security import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


class IntegrationCreate(BaseModel):
    platform: str
    api_key: str
    api_url: str | None = None
    sync_frequency_minutes: int = 30


class IntegrationResponse(BaseModel):
    id: str
    platform: str
    is_active: bool
    sync_frequency_minutes: int
    last_sync_at: str | None = None
    api_url: str | None = None
    has_api_key: bool = False

    class Config:
        from_attributes = True


class LaborRateCreate(BaseModel):
    role: str
    hourly_rate: float
    overtime_multiplier: float = 1.5
    per_diem: float = 0.0


class LaborRateResponse(BaseModel):
    id: str
    role: str
    hourly_rate: float
    overtime_multiplier: float
    per_diem: float

    class Config:
        from_attributes = True


@router.get("/integrations", response_model=list[IntegrationResponse])
def list_integrations(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    integrations = db.query(Integration).filter(Integration.org_id == current_user.org_id).all()
    return [
        IntegrationResponse(
            id=str(i.id),
            platform=i.platform,
            is_active=i.is_active,
            sync_frequency_minutes=i.sync_frequency_minutes,
            last_sync_at=i.last_sync_at.isoformat() if i.last_sync_at else None,
            api_url=i.api_url,
            has_api_key=bool(i.api_key_encrypted),
        )
        for i in integrations
    ]


@router.post("/integrations", response_model=IntegrationResponse, status_code=201)
def create_integration(data: IntegrationCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = db.query(Integration).filter(
        Integration.org_id == current_user.org_id,
        Integration.platform == data.platform,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{data.platform} is already connected")

    integration = Integration(
        org_id=current_user.org_id,
        platform=data.platform,
        api_key_encrypted=data.api_key,
        api_url=data.api_url,
        sync_frequency_minutes=data.sync_frequency_minutes,
    )
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return IntegrationResponse(
        id=str(integration.id),
        platform=integration.platform,
        is_active=integration.is_active,
        sync_frequency_minutes=integration.sync_frequency_minutes,
        last_sync_at=None,
        api_url=integration.api_url,
        has_api_key=bool(integration.api_key_encrypted),
    )


@router.delete("/integrations/{integration_id}", status_code=204)
def delete_integration(integration_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.org_id == current_user.org_id,
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    db.delete(integration)
    db.commit()


@router.post("/integrations/{integration_id}/test")
def test_integration(integration_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    integration = db.query(Integration).filter(
        Integration.id == integration_id,
        Integration.org_id == current_user.org_id,
    ).first()
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    # Placeholder - would actually test the API connection
    return {"status": "ok", "message": f"Connection to {integration.platform} successful"}


@router.get("/labor-rates", response_model=list[LaborRateResponse])
def list_labor_rates(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rates = db.query(LaborRate).filter(LaborRate.org_id == current_user.org_id).all()
    return [
        LaborRateResponse(id=str(r.id), role=r.role, hourly_rate=r.hourly_rate,
                          overtime_multiplier=r.overtime_multiplier, per_diem=r.per_diem)
        for r in rates
    ]


@router.post("/labor-rates", response_model=LaborRateResponse, status_code=201)
def create_labor_rate(data: LaborRateCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    rate = LaborRate(org_id=current_user.org_id, **data.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return LaborRateResponse(id=str(rate.id), role=rate.role, hourly_rate=rate.hourly_rate,
                             overtime_multiplier=rate.overtime_multiplier, per_diem=rate.per_diem)
