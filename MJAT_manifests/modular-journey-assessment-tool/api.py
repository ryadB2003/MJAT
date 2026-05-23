"""
FastAPI REST API for migration assessment.
Simple endpoint that accepts JSON input and returns assessment results.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models.inputs import AssessmentInputs
from models.outputs import AssessmentResult, Timeline
from logic.engagement import determine_engagement_model, explain_engagement_decision
from logic.complexity import calculate_complexity_score
from logic.details_generator import (
    generate_validation_warnings,
    generate_migration_scenario,
    generate_phase_details,
    generate_ps_role_breakdown,
    generate_immediate_actions
)

app = FastAPI(
    title="Migration Assessment API",
    description="MKE/MSR Migration Assessment Tool",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/assess", response_model=AssessmentResult)
def assess_migration(inputs: AssessmentInputs):
    """
    Perform complete migration assessment.

    Returns complexity score, readiness score, engagement model,
    timeline estimate, and recommendations.
    """
    try:
        # Calculate complexity
        complexity_score, complexity_level = calculate_complexity_score(inputs)

        # Calculate readiness (simplified for now)
        readiness_score = _calculate_readiness(inputs)
        readiness_level = _get_readiness_level(readiness_score)

        # Determine engagement model
        engagement = determine_engagement_model(inputs)

        # Calculate timeline (simplified)
        timeline = _calculate_timeline(inputs, engagement)

        # Generate recommendations (renamed from risks to considerations)
        considerations = _identify_considerations(inputs)
        actions = _generate_actions(inputs, engagement)

        # Generate rich details
        validation_warnings = generate_validation_warnings(inputs)
        migration_scenario = generate_migration_scenario(inputs)
        total_weeks = (timeline.min_months + timeline.max_months) / 2 * 4.33
        phase_details = generate_phase_details(inputs, engagement.model, total_weeks)
        immediate_actions = generate_immediate_actions(inputs, engagement.model)

        avg_timeline_months = (timeline.min_months + timeline.max_months) / 2
        ps_role_breakdown = generate_ps_role_breakdown(engagement.model, engagement.ps_effort_percent, avg_timeline_months)

        return AssessmentResult(
            complexity_score=complexity_score,
            complexity_level=complexity_level,
            readiness_score=readiness_score,
            readiness_level=readiness_level,
            engagement_model=engagement,
            timeline=timeline,
            considerations=considerations,
            priority_actions=actions,
            migration_path="MKE Platform Upgrade" if inputs.num_msr_instances == 0 else ("Registry-First Migration" if inputs.swarm_percent == 0 else "Platform-First Migration"),
            migration_strategy=(
                ["Upgrade MKE 3.x → MKE 4.0", "Update applications", "Final validation"]
                if inputs.num_msr_instances == 0 else
                ["Migrate MSR 2.9 → MSR 4.0", "Update applications", "Upgrade MKE 3.x → MKE 4.0"]
            ),
            validation_warnings=validation_warnings,
            migration_scenario=migration_scenario,
            phase_details=phase_details,
            immediate_actions=immediate_actions,
            ps_role_breakdown=ps_role_breakdown
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/debug", response_model=dict)
def debug_engagement_model(inputs: AssessmentInputs):
    """
    Debug endpoint that shows detailed breakdown of engagement model decision.
    Useful for understanding why a particular model was chosen.
    """
    try:
        explanation = explain_engagement_decision(inputs)
        engagement = determine_engagement_model(inputs)

        return {
            "inputs": inputs.dict(),
            "explanation": explanation,
            "final_engagement_model": engagement.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_readiness(inputs: AssessmentInputs) -> int:
    """Simplified readiness calculation"""
    score = 50  # Base

    # K8s experience
    if inputs.k8s_experience >= 4:
        score += 20
    elif inputs.k8s_experience >= 3:
        score += 10

    # Migration experience
    if inputs.migration_exp == 'extensive':
        score += 25
    elif inputs.migration_exp == 'some':
        score += 15

    # Automation
    if inputs.automation_level >= 70:
        score += 15
    elif inputs.automation_level >= 50:
        score += 10

    # Deployment frequency bonus
    if inputs.deploy_frequency in ['multiple-daily', 'daily'] and inputs.automation_level >= 60:
        score += 5  # Mature DevOps

    return max(0, min(100, score))


def _get_readiness_level(score: int) -> str:
    """Determine readiness level from score (matches JavaScript version)"""
    if score < 30:
        return "Low Readiness"
    elif score < 60:
        return "Medium Readiness"
    else:
        return "Good Readiness"


def _swarm_conversion_weeks(swarm_percent: int, app_count: int) -> float:
    """
    Calculate Swarm conversion time with economy of scale.

    Uses power-law scaling (exponent 0.7) to model artifact reuse:
    - First apps: Full effort (create patterns, Helm templates, K8s manifests)
    - Later apps: Reduced effort (reuse patterns, customize configs)

    Per-app effort assumptions:
    - Simple service (stateless): ~0.5 day
    - Medium service (volumes, secrets): ~1 day
    - Complex service (stateful, networking): ~2 days
    - Average: ~1 day per app baseline, reduced by reuse

    Returns total weeks for Swarm conversion.
    """
    if swarm_percent == 0:
        return 0.0

    # Calculate actual number of Swarm apps to convert
    swarm_apps = int(app_count * (swarm_percent / 100))

    if swarm_apps == 0:
        return 0.0

    # Power-law scaling with economy of scale
    # Base: 3 days for initial setup (tooling, CI/CD, first patterns)
    # Per-app: swarm_apps^0.7 * 0.8 days (diminishing returns as count increases)
    #
    # Examples:
    #   10 apps:  3 + 10^0.7 * 0.8  = 3 + 4.0  = 7 days  = 1.4 weeks
    #   50 apps:  3 + 50^0.7 * 0.8  = 3 + 13.6 = 16.6 days = 3.3 weeks
    #   100 apps: 3 + 100^0.7 * 0.8 = 3 + 20.0 = 23 days = 4.6 weeks
    #   200 apps: 3 + 200^0.7 * 0.8 = 3 + 32.0 = 35 days = 7 weeks

    base_days = 3  # Initial tooling and pattern creation
    scaling_factor = 0.8  # Calibrated for ~1 day/app effective with reuse
    economy_exponent = 0.7  # Power law for diminishing marginal effort

    days = base_days + (swarm_apps ** economy_exponent) * scaling_factor

    # Convert to weeks (5 working days per week)
    weeks = days / 5

    # Minimum 1 week for any Swarm conversion
    return max(1.0, weeks)


def _calculate_timeline(inputs: AssessmentInputs, engagement) -> Timeline:
    """
    Aggressive but safe timeline calculation:
    - Reduced base weeks (assumes experienced PS team with parallel workstreams)
    - Additive model instead of multiplicative (more predictable, less scary)
    - Reduced buffer (PS team manages contingencies)
    - Tighter range (±10% instead of ±15%)
    - Fast-track for minimal engagements
    """
    # Check for MINIMAL ENGAGEMENT (fast-track to 1-2 weeks)
    is_minimal = (
        inputs.swarm_percent == 0 and           # Pure K8s
        inputs.num_mke_instances <= 2 and       # 1-2 MKE instances
        inputs.total_nodes <= 30 and            # Small environment
        inputs.k8s_experience >= 4 and          # Experienced team
        inputs.num_environments == 1 and        # Single environment
        engagement.model == 'advisory'          # Self-sufficient team
    )

    # Check if MSR migration is needed (any MSR instance requires migration to MSR 4.0)
    needs_msr_migration = inputs.num_msr_instances > 0
    num_msr = inputs.num_msr_instances
    num_mke = inputs.num_mke_instances

    # Base weeks calculation
    # No MSR = just MKE upgrade (simpler), With MSR = registry migration + MKE upgrade
    if is_minimal:
        # Minimal engagement: 1 week base, +1 week if MSR migration needed
        base_weeks = 2 if needs_msr_migration else 1
        swarm_weeks = 0.0  # No Swarm conversion for minimal engagements
    elif inputs.swarm_percent == 0:
        # Pure K8s: 1 week for MKE-only, 2 weeks if MSR migration needed
        base_weeks = 2 if needs_msr_migration else 1
        swarm_weeks = 0.0  # No Swarm conversion
    else:
        # Swarm conversion: Use tiered economy-of-scale calculation
        # Base is just MKE/MSR upgrade, Swarm conversion is separate
        base_weeks = 2 if needs_msr_migration else 1
        swarm_weeks = _swarm_conversion_weeks(inputs.swarm_percent, inputs.app_count)

    # ENGAGEMENT PACE MULTIPLIER: Who does the work affects conversion speed
    # PS team is experienced (faster), customer team is learning (slower)
    pace_multipliers = {
        'full': 0.70,           # PS-led: 30% faster (experienced team, dedicated focus)
        'hybrid': 0.85,         # Shared: 15% faster (PS guidance accelerates)
        'advisory': 1.0,        # Customer-led: baseline (they do the work)
        'assessment-first': 1.0 # TBD after assessment
    }
    pace_multiplier = pace_multipliers.get(engagement.model, 1.0)
    swarm_weeks *= pace_multiplier

    # INSTANCE SCALING: More MKE/MSR instances = more work
    # MKE instance adjustment: +0.5 week per MKE instance beyond first 2 (parallel work possible)
    mke_adjustment = max(0, (num_mke - 2)) * 0.5

    # MSR instance adjustment: +1 week per MSR instance beyond first (each needs migration)
    msr_adjustment = max(0, (num_msr - 1)) * 1.0 if needs_msr_migration else 0

    # ADDITIVE MODEL: More predictable than compounding multipliers
    # Each adjustment adds weeks instead of multiplying

    # Swarm adjustment: Now using economy-of-scale with engagement pace multiplier
    swarm_adjustment = swarm_weeks  # Includes economy of scale + pace adjustment

    # Engagement adjustment: PS involvement level (coordination overhead)
    # Keep minimal for simple environments - base weeks already account for work
    engagement_adjustments = {
        'advisory': 0,      # Customer-led, minimal PS overhead
        'hybrid': 1,        # Shared responsibility - light coordination
        'full': 1,          # PS-led - PS expertise speeds things up
        'assessment-first': 2  # Unknown complexity - needs discovery
    }
    engagement_adjustment = engagement_adjustments.get(engagement.model, 1)
    if not needs_msr_migration and engagement_adjustment > 0:
        engagement_adjustment -= 1  # Simpler scope without MSR

    # Environment adjustment: multi-env coordination overhead
    env_adjustment = max(0, (inputs.num_environments - 1)) * 1  # +1 week per additional env

    # Experience discount: reward K8s expertise
    experience_discounts = {
        5: -2,   # Expert: 2 weeks faster
        4: -1,   # Advanced: 1 week faster
        3: 0,    # Intermediate: baseline
        2: 0,    # Beginner: baseline
        1: 1     # Basic: 1 week slower
    }
    experience_adjustment = experience_discounts.get(inputs.k8s_experience, 0)

    # APPLICATION COUNT ADJUSTMENT: More apps = more validation/testing work
    # Applies to ALL migrations (K8s or Swarm) - not just Swarm conversion
    # Uses logarithmic scaling: significant early impact, diminishing returns for very large portfolios
    # Formula: log2(apps/50) for apps > 50, capped at reasonable maximum
    if inputs.app_count <= 50:
        app_adjustment = 0.0  # Baseline for small portfolios
    elif inputs.app_count <= 100:
        app_adjustment = 0.5  # +0.5 weeks for 51-100 apps
    elif inputs.app_count <= 200:
        app_adjustment = 1.0  # +1 week for 101-200 apps
    elif inputs.app_count <= 300:
        app_adjustment = 1.5  # +1.5 weeks for 201-300 apps
    elif inputs.app_count <= 500:
        app_adjustment = 2.5  # +2.5 weeks for 301-500 apps
    else:
        # Very large portfolios: 3 weeks + 0.5 week per 200 apps beyond 500
        app_adjustment = 3.0 + ((inputs.app_count - 500) / 200) * 0.5
        app_adjustment = min(app_adjustment, 6.0)  # Cap at 6 weeks for app validation

    # Apply pace multiplier to app adjustment (PS team validates faster)
    app_adjustment *= pace_multiplier

    # Calculate total weeks (additive)
    total_weeks = (base_weeks + mke_adjustment + msr_adjustment +
                   swarm_adjustment + engagement_adjustment + env_adjustment +
                   experience_adjustment + app_adjustment)

    # Track adjustments for transparency
    swarm_apps_count = int(inputs.app_count * (inputs.swarm_percent / 100)) if inputs.swarm_percent > 0 else 0
    adjustments = {
        'base': base_weeks,
        'mke_instances': round(mke_adjustment, 1),
        'msr_instances': round(msr_adjustment, 1),
        'swarm': round(swarm_adjustment, 1),
        'swarm_apps': swarm_apps_count,  # Number of Swarm apps being converted (economy of scale)
        'app_validation': round(app_adjustment, 1),  # App count affects validation/testing time
        'total_apps': inputs.app_count,  # Total applications being migrated
        'engagement': engagement_adjustment,
        'environments': env_adjustment,
        'experience': experience_adjustment,
        'minimal_engagement': is_minimal,
        'msr_migration': needs_msr_migration
    }

    # REDUCED BUFFER: 5-10% (PS team absorbs risk)
    buffer = 0.05  # Base 5% buffer

    # Small increases for specific risks
    if inputs.k8s_experience <= 2 and inputs.swarm_percent > 50:
        buffer += 0.03  # +3% for inexperience with heavy Swarm
    if inputs.automation_level < 40:
        buffer += 0.02  # +2% for very manual processes

    # Mission-critical workloads require more careful scheduling
    if inputs.mission_critical_percent > 75:
        buffer += 0.03  # +3% for very high mission-critical
    elif inputs.mission_critical_percent > 50:
        buffer += 0.02  # +2% for high mission-critical

    # Clamp buffer between 5% and 13%
    buffer = max(0.05, min(0.13, buffer))

    total_weeks *= (1 + buffer)

    # Ensure minimum viable timeline (lower floor for minimal engagements)
    # Minimal without MSR migration = 1 week, with MSR = 2 weeks
    if is_minimal:
        min_weeks = 2 if needs_msr_migration else 1
    else:
        min_weeks = 2
    total_weeks = max(total_weeks, min_weeks)

    months = total_weeks / 4.33

    # TIGHTER RANGE: ±10% instead of ±15%
    return Timeline(
        min_months=round(months * 0.90, 1),
        max_months=round(months * 1.10, 1),
        base_weeks=round(base_weeks, 1),
        multipliers_applied=adjustments  # Now shows additive adjustments
    )


def _identify_considerations(inputs: AssessmentInputs) -> list[str]:
    """
    Identify key considerations for the migration.

    Note: High Swarm % is a timeline/complexity factor, not inherently risky.
    It only becomes a consideration when combined with capability gaps or capacity issues.
    """
    considerations = []

    # Consideration: Swarm conversion with insufficient K8s expertise
    if inputs.swarm_percent > 60 and inputs.k8s_experience <= 2:
        considerations.append(f"High Swarm workload ({inputs.swarm_percent}%) with limited K8s expertise - additional training recommended")

    # Consideration: Large Swarm conversion with low automation
    if inputs.swarm_percent > 50 and inputs.automation_level < 40:
        considerations.append(f"Manual conversion of {inputs.swarm_percent}% Swarm workloads - automation improvements would accelerate migration")

    # Consideration: Swarm conversion with team capacity constraints
    if inputs.swarm_percent > 70 and inputs.apps_per_team > 50:
        considerations.append(f"Team capacity for {inputs.swarm_percent}% Swarm conversion at scale ({inputs.apps_per_team:.0f} apps/person) - phased approach recommended")

    # General K8s expertise consideration (when Swarm is low, so team will work in K8s primarily)
    if inputs.k8s_experience < 3 and inputs.swarm_percent <= 30:
        considerations.append("Kubernetes expertise development recommended to optimize migration velocity")

    # Low automation consideration
    if inputs.automation_level < 50:
        considerations.append("Automation improvements would reduce manual effort during migration")

    return considerations if considerations else ["No significant considerations identified"]


def _generate_actions(inputs: AssessmentInputs, engagement) -> list[str]:
    """Generate priority actions"""
    actions = []

    if engagement.model == 'advisory':
        actions.append("Begin migration planning with expert advisory support")
        actions.append("Set up regular check-ins for validation and guidance")
    elif engagement.model == 'assessment-first':
        actions.append("Complete comprehensive environment assessment (2-4 weeks)")
        actions.append("Document all dependencies and integration points")

    if inputs.swarm_percent > 0:
        actions.append(f"Plan Swarm to Kubernetes conversion for {inputs.swarm_percent}% of workloads")

    return actions


@app.get("/")
def root():
    """API root endpoint"""
    return {
        "message": "Migration Assessment API",
        "version": "1.0.0",
        "endpoints": {
            "/api/assess": "POST - Perform complete assessment",
            "/api/debug": "POST - Debug engagement model decision",
            "/docs": "GET - Interactive API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Migration Assessment API...")
    print("API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
