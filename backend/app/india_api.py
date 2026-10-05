from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .india import Facts, advise, CATALOGUE
from .india.intake import extract
from .india.agent import step

router = APIRouter(prefix="/api/india", tags=["india-family-law"])


class FactsIn(BaseModel):
    law: str = Field(description="hindu | muslim | christian | parsi | special_marriage")
    claimant: str = "wife"
    needs: list[str] = []
    mutual_consent: bool = False
    ground: Optional[str] = None
    marriage_years: Optional[float] = None
    separated_months: Optional[float] = None
    marriage_place: Optional[str] = None
    last_cohabitation_place: Optional[str] = None
    petitioner_residence: Optional[str] = None
    respondent_residence: Optional[str] = None
    respondent_abroad: bool = False
    claimant_can_self_maintain: bool = False
    respondent_has_means: bool = True
    claimant_living_in_adultery: bool = False
    claimant_refuses_cohabitation_without_cause: bool = False
    separated_by_mutual_consent: bool = False
    domestic_violence: bool = False
    child_minor: bool = True
    child_disabled: bool = False
    divorce_pending_or_decreed: bool = False


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
    return extract(body.text)


class AgentIn(BaseModel):
    session_id: Optional[str] = None
    text: Optional[str] = Field(default=None, max_length=4000)
    answer: Optional[dict] = None
    lang: Optional[str] = Field(default=None, pattern="^(en|hi|ta)$")


@router.post("/agent")
def agent(body: AgentIn):
    return step(body.session_id, body.text, body.answer, lang=body.lang)
