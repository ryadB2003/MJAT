"""
Output data models for assessment results.
"""
from typing import Literal
from pydantic import BaseModel, Field


class EngagementModel(BaseModel):
    """Engagement model recommendation"""
    model: Literal['advisory', 'hybrid', 'full', 'assessment-first']
    name: str
    approach: str
    description: str
    ps_effort_percent: float = Field(..., ge=0, le=100)
    duration_multiplier: float = Field(..., ge=0.5, le=2.0)  # FIXED: Allow <1.0 for expert teams (faster)


class Timeline(BaseModel):
    """Timeline estimation"""
    min_months: float
    max_months: float
    base_weeks: float
    multipliers_applied: dict[str, float]


class PhaseDetail(BaseModel):
    """Detailed phase breakdown"""
    number: int
    name: str
    description: str
    duration_weeks: str
    activities: list[str]


class PSRoleBreakdown(BaseModel):
    """Professional Services role breakdown"""
    role: str
    weeks: str
    description: str


class MigrationScenario(BaseModel):
    """Detailed migration scenario"""
    title: str
    strategy_steps: list[str]
    critical_timeline: str
    key_considerations: list[str]


class AssessmentResult(BaseModel):
    """Complete assessment result"""
    # Scores
    complexity_score: int = Field(..., ge=0, le=100)
    complexity_level: str
    readiness_score: int = Field(..., ge=0)  # Can exceed 100 with bonuses
    readiness_level: str

    # Engagement model
    engagement_model: EngagementModel

    # Timeline
    timeline: Timeline

    # Considerations (renamed from risk_factors for customer-friendly messaging)
    considerations: list[str]
    priority_actions: list[str]

    # Migration path
    migration_path: str
    migration_strategy: list[str]

    # Rich details
    validation_warnings: list[str] = Field(default_factory=list)
    migration_scenario: MigrationScenario
    phase_details: list[PhaseDetail]
    immediate_actions: list[str]
    ps_role_breakdown: list[PSRoleBreakdown]

    class Config:
        schema_extra = {
            "example": {
                "complexity_score": 23,
                "complexity_level": "Low-Medium",
                "readiness_score": 105,
                "readiness_level": "Good Readiness",
                "engagement_model": {
                    "model": "advisory",
                    "name": "Self-Sufficient Innovator",
                    "approach": "Enablement & Advisory",
                    "description": "Expert team with minimal guidance needed",
                    "ps_effort_percent": 27.5,
                    "duration_multiplier": 1.45
                },
                "timeline": {
                    "min_months": 2.7,
                    "max_months": 4.5,
                    "base_weeks": 10,
                    "multipliers_applied": {
                        "registry": 1.0,
                        "swarm": 1.0,
                        "engagement": 1.45,
                        "team_capacity": 1.0,
                        "readiness_discount": 0.80
                    }
                }
            }
        }
