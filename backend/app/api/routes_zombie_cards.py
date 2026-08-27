from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.zombie_card_saver.schemas import (
    ZombieActionType,
    ZombieAnalysisResponse,
    ZombieCardSummary,
    ZombieStatisticsResponse,
)
from app.zombie_card_saver.service import zombie_card_saver_service

router = APIRouter(prefix="/api/v1/zombie-cards", tags=["Zombie Card Saver"])

@router.get("", response_model=List[ZombieCardSummary])
def get_zombie_cards(db: Session = Depends(get_db)):
    """
    Returns all evaluated cards with zombie lifecycle status,
    dependent active tokens, and authoritative risk score.
    """
    return zombie_card_saver_service.get_all_zombie_cards(db)

@router.get("/statistics", response_model=ZombieStatisticsResponse)
def get_zombie_statistics(db: Session = Depends(get_db)):
    """
    Returns summary statistics for the Zombie Card Saver dashboard.
    """
    return zombie_card_saver_service.get_statistics(db)

@router.get("/{card_id}/analysis", response_model=ZombieAnalysisResponse)
def get_card_zombie_analysis(card_id: str, db: Session = Depends(get_db)):
    """
    Returns deep-dive Zombie analysis for a specific card:
    Token dependency graph, recent transactions, merchant/customer impact,
    and recommended selective actions.
    """
    analysis = zombie_card_saver_service.get_card_analysis(db, card_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Card {card_id} not found.")
    return analysis

@router.post("/tokens/{token_id}/revoke")
async def revoke_zombie_token(token_id: str, db: Session = Depends(get_db)):
    """
    Selectively revokes a high-risk zombie payment token while preserving
    recurring merchant subscriptions.
    """
    result = await zombie_card_saver_service.execute_token_remediation(
        db, token_id=token_id, action=ZombieActionType.REVOKE_TOKEN
    )
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error"))
    return result
