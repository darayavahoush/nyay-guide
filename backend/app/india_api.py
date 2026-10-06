import logging
from typing import Any, Literal, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .india import Facts, advise, CATALOGUE
from .india.intake import extract
from .india import slm
from .india.agent import step, forget

router = APIRouter(prefix="/api/india", tags=["india-family-law"])

Law = Literal["hindu", "muslim", "christian", "parsi", "special_marriage"]
Place = Optional[str]


class FactsIn(BaseModel):
    law: Law = Field(description="hindu (incl. Sikh, Jain, Buddhist) | muslim | christian | parsi | special_marriage")
    claimant: Literal["wife", "husband", "child", "parent"] = "wife"
    needs: list[Literal["divorce", "maintenance", "protection"]] = []
    mutual_consent: bool = False
    ground: Optional[str] = Field(default=None, max_length=80)
    marriage_years: Optional[float] = Field(default=None, ge=0, le=100)
    separated_months: Optional[float] = Field(default=None, ge=0, le=1200)
    marriage_place: Optional[str] = Field(default=None, max_length=80)
    last_cohabitation_place: Optional[str] = Field(default=None, max_length=80)
    petitioner_residence: Optional[str] = Field(default=None, max_length=80)
    respondent_residence: Optional[str] = Field(default=None, max_length=80)
    respondent_abroad: bool = False
    claimant_can_self_maintain: bool = False
    respondent_has_means: bool = True
    claimant_living_in_adultery: bool = False
    claimant_refuses_cohabitation_without_cause: bool = False
    separated_by_mutual_consent: bool = False
    domestic_violence: bool = False
    child_minor: bool = True
    child_disabled: bool = False
    divorce_status: Optional[Literal["none", "pending", "decreed", "filed"]] = Field(
        default=None, description="none | pending | decreed | filed (filed = pending or decreed, unknown which)")
    divorce_pending_or_decreed: bool = Field(default=False, description="legacy; prefer divorce_status")


@router.post("/advise")
def advise_route(body: FactsIn):
    try:
        return advise(Facts(**body.model_dump()))
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/catalogue")
def catalogue():
    return CATALOGUE


class IntakeIn(BaseModel):
    text: str = Field(max_length=4000)


@router.post("/intake")
def intake(body: IntakeIn):
    return slm.augment(body.text, extract(body.text))


class AnswerIn(BaseModel):
    slot: str = Field(max_length=40)
    value: Any = None


class AgentIn(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    text: Optional[str] = Field(default=None, max_length=4000)
    answer: Optional[AnswerIn] = None
    lang: Optional[str] = Field(default=None, pattern="^(en|hi|ta)$")
    snapshot: Optional[dict] = None     # sent back by the browser so a restarted server can rebuild the session


@router.post("/agent")
def agent(body: AgentIn):
    try:
        return step(body.session_id, body.text, body.answer.model_dump() if body.answer else None, lang=body.lang, snap=body.snapshot)
    except ValueError as e:
        a = body.answer
        logging.getLogger("uvicorn.error").warning("agent 422: %s (slot=%s)", e, a.slot if a else None)   # never logs the person's text or answers
        raise HTTPException(422, str(e))


@router.delete("/session/{session_id}", status_code=204)
def delete_session(session_id: str):
    """Forget a session and everything typed into it."""
    forget(session_id)
