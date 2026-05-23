"""
Engagement model determination logic.
This is the core logic that was causing issues in the JavaScript version.
"""
from models.inputs import AssessmentInputs
from models.outputs import EngagementModel


def _calculate_app_scale_factor(app_count: int) -> float:
    """
    Calculate PS effort scaling factor based on application count.
    More apps = more PS effort needed for coordination, validation, and support.

    Returns a multiplier (1.0 = baseline, up to 1.5 for very large portfolios)
    """
    if app_count <= 50:
        return 1.0  # Baseline
    elif app_count <= 100:
        return 1.05  # +5% for 51-100 apps
    elif app_count <= 200:
        return 1.10  # +10% for 101-200 apps
    elif app_count <= 300:
        return 1.15  # +15% for 201-300 apps
    elif app_count <= 500:
        return 1.25  # +25% for 301-500 apps
    else:
        # Large portfolios: cap at 1.5x (50% more PS effort)
        return min(1.5, 1.25 + ((app_count - 500) / 1000) * 0.25)


def determine_engagement_model(inputs: AssessmentInputs) -> EngagementModel:
    """
    Determine the appropriate engagement model based on team capabilities
    and environment complexity.

    Order of evaluation:
    1. Distributed Chaos (assessment-first)
    2. Overwhelmed Organization (full)
    3. Self-Sufficient Innovator (advisory)
    4. Skilled but Time-Constrained (hybrid)
    5. Default (hybrid)
    """
    # Calculate app-based scaling factor for PS effort
    app_scale = _calculate_app_scale_factor(inputs.app_count)

    # Check for DISTRIBUTED CHAOS first
    # Assessment needed when environment complexity exceeds team capabilities
    is_distributed = _is_distributed_chaos(inputs)
    if is_distributed:
        return EngagementModel(
            model='assessment-first',
            name='Comprehensive Assessment Required',
            approach='Assessment First, Then Services',
            description='Complex environment with scale challenges - comprehensive assessment needed',
            ps_effort_percent=0.0,  # TBD after assessment
            duration_multiplier=1.0  # TBD after assessment
        )

    # Check for OVERWHELMED ORGANIZATION
    # Profile: Minimal K8s exp, no migration exp, heavy Swarm, small team
    is_overwhelmed = _is_overwhelmed_org(inputs)
    if is_overwhelmed:
        # Scale PS effort: base 87.5% * app_scale, capped at 100%
        scaled_ps_effort = min(100.0, 87.5 * app_scale)
        return EngagementModel(
            model='full',
            name='Full Managed Migration',
            approach='Full Managed Migration (5-Phase Approach)',
            description='75%+ Swarm workloads, limited Kubernetes expertise, no dedicated migration resources',
            ps_effort_percent=round(scaled_ps_effort, 1),
            duration_multiplier=1.20  # FIXED: Struggling teams need more time (20% longer) due to learning curve
        )

    # Check for SELF-SUFFICIENT INNOVATOR
    # Profile: Expert K8s, minimal Swarm, high automation, strong team
    is_self_sufficient = _is_self_sufficient(inputs)
    if is_self_sufficient:
        # Scale PS effort: base 27.5% * app_scale
        scaled_ps_effort = 27.5 * app_scale
        return EngagementModel(
            model='advisory',
            name='Enablement & Advisory',
            approach='Enablement & Advisory (Self-Guided with Expert Support)',
            description='Mostly Kubernetes workloads, high automation, strong team needs validation and guidance',
            ps_effort_percent=round(scaled_ps_effort, 1),
            duration_multiplier=0.85  # FIXED: Expert teams with automation should be FASTER (15% faster), not slower
        )

    # Check for SKILLED BUT TIME-CONSTRAINED
    # Profile: Good capabilities but can't fully dedicate team
    is_time_constrained = _is_time_constrained(inputs)
    if is_time_constrained:
        # Scale PS effort: base 62.5% * app_scale, capped at 90%
        scaled_ps_effort = min(90.0, 62.5 * app_scale)
        return EngagementModel(
            model='hybrid',
            name='Hybrid Migration Approach',
            approach='Hybrid Approach (Guided 5-Phase Implementation)',
            description='Balanced Swarm/Kubernetes workloads, capable team lacks bandwidth for full ownership',
            ps_effort_percent=round(scaled_ps_effort, 1),
            duration_multiplier=1.25
        )

    # DEFAULT: Hybrid if no other pattern matches
    # Scale PS effort: base 62.5% * app_scale, capped at 90%
    scaled_ps_effort = min(90.0, 62.5 * app_scale)
    return EngagementModel(
        model='hybrid',
        name='Hybrid Migration Approach',
        approach='Hybrid Approach (Guided 5-Phase Implementation)',
        description='Balanced capabilities - your team leads with expert guidance and support',
        ps_effort_percent=round(scaled_ps_effort, 1),
        duration_multiplier=1.25
    )


def _is_distributed_chaos(inputs: AssessmentInputs) -> bool:
    """
    Check if environment qualifies as "Distributed Chaos" requiring assessment first.

    Profile: Multi-location, mixed versions, unclear current state.
    Triggers when infrastructure spans multiple environments (hybrid or multi-cloud).
    """
    return inputs.infra_location in ['hybrid', 'multi']


def _is_overwhelmed_org(inputs: AssessmentInputs) -> bool:
    """
    Check if organization needs Full Managed Migration.

    Triggers when:
    - Skill gap: Minimal K8s expertise, no migration experience, small team
    - Scale overwhelm: Too many MKE instances/apps for team size
    - Registry complexity: Multiple MSR instances without adequate team
    """
    # Original: Skill gap + very small team + heavy Swarm
    skill_gap = (
        inputs.k8s_experience <= 2 and
        inputs.migration_exp == 'none' and
        inputs.dedicated_team in ['no', 'partial'] and
        inputs.platform_team_size <= 2 and  # Changed from 3 to 2
        inputs.training_needs_count >= 3 and
        (inputs.swarm_percent >= 75 or inputs.automation_level < 30)
    )

    # Scale overwhelm: Team can't handle the infrastructure size (ratio-based)
    scale_overwhelm = (
        (inputs.mke_per_team > 3) or  # More than 3 MKE instances per person
        (inputs.platform_team_size > 20 and inputs.apps_per_team > 40 and inputs.swarm_percent > 30) or
        (inputs.num_mke_instances >= 10 and inputs.k8s_experience <= 2 and inputs.swarm_percent > 50)
    )

    # Registry complexity: Too many MSR instances for team
    # Threshold: 1 person can reasonably manage 2 MSR instances
    # So 10 MSRs needs at least 5 people (ratio > 2.0 triggers overwhelm)
    registry_overwhelm = inputs.num_msr_instances >= 5 and inputs.msr_per_team > 2.0

    return skill_gap or scale_overwhelm or registry_overwhelm


def _is_self_sufficient(inputs: AssessmentInputs) -> bool:
    """
    Check if team qualifies as "Self-Sufficient Innovator".

    Uses a scoring system (relaxed from requiring ALL conditions):
    - Qualify if score >= 5 out of 7 possible points
    - Core requirements still weighted higher
    """
    score = 0

    # K8s expertise: Advanced to Expert (4-5) - worth 2 points (core requirement)
    if inputs.k8s_experience >= 4:
        score += 2

    # Migration experience: Extensive OR (Some + easy migration) - worth 1 point
    has_migration_exp = (
        inputs.migration_exp == 'extensive' or
        (inputs.migration_exp == 'some' and
         inputs.swarm_percent <= 20 and
         inputs.automation_level >= 70)
    )
    if has_migration_exp:
        score += 1

    # Dedicated full-time team - worth 1 point
    if inputs.dedicated_team == 'yes':
        score += 1

    # Well-staffed: At least 6 people (relaxed from 8) - worth 1 point
    if inputs.platform_team_size >= 6:
        score += 1

    # Minimal training needs (relaxed to <= 2) - worth 1 point
    if inputs.training_needs_count <= 2:
        score += 1

    # Good automation (relaxed to >= 60%) - worth 1 point
    if inputs.automation_level >= 60:
        score += 1

    # Mostly Kubernetes (relaxed to <= 40%) - worth 1 point
    if inputs.swarm_percent <= 40:
        score += 1

    # Qualify if score >= 5 out of 8 possible points
    return score >= 5


def _is_time_constrained(inputs: AssessmentInputs) -> bool:
    """
    Check if team is skilled but time-constrained.

    Profile: Intermediate-advanced K8s, some migration exp, can't fully dedicate,
    medium-sized capable team, some training gaps, good automation, balanced workload.
    """
    return (
        3 <= inputs.k8s_experience <= 4 and
        inputs.migration_exp == 'some' and
        inputs.dedicated_team != 'yes' and
        4 <= inputs.platform_team_size <= 8 and
        inputs.training_needs_count <= 2 and
        inputs.automation_level >= 50 and
        20 <= inputs.swarm_percent <= 75  # Widened from 30-70 to 20-75
    )


# Debugging helper
def explain_engagement_decision(inputs: AssessmentInputs) -> dict:
    """
    Returns detailed breakdown of why an engagement model was chosen.
    Useful for debugging and understanding the decision.
    """
    # Assessment-first: Hybrid/Multi-cloud infrastructure
    assessment_first_checks = {
        'infra_location': f"{inputs.infra_location} in ['hybrid', 'multi'] = {inputs.infra_location in ['hybrid', 'multi']}",
        'is_distributed_chaos': _is_distributed_chaos(inputs)
    }

    # Full managed: Overwhelmed, inexperienced, or under-capacity
    overwhelmed_checks = {
        'skill_gap': f"k8s_exp={inputs.k8s_experience}<=2 and migration='none' and small team = {inputs.k8s_experience <= 2 and inputs.migration_exp == 'none' and inputs.platform_team_size <= 3}",
        'scale_overwhelm_mke': f"{inputs.mke_per_team:.2f} > 3 = {inputs.mke_per_team > 3}",
        'scale_overwhelm_apps': f"team>{20} and apps/team>{40} and swarm>{30} = {inputs.platform_team_size > 20 and inputs.apps_per_team > 40 and inputs.swarm_percent > 30}",
        'scale_overwhelm_inexperience': f"mke>=10 and k8s<=2 and swarm>50 = {inputs.num_mke_instances >= 10 and inputs.k8s_experience <= 2 and inputs.swarm_percent > 50}",
        'registry_overwhelm': f"{inputs.num_msr_instances} >= 5 and {inputs.msr_per_team:.2f} > 2.0 = {inputs.num_msr_instances >= 5 and inputs.msr_per_team > 2.0}",
        'is_overwhelmed': _is_overwhelmed_org(inputs)
    }

    # Advisory: Self-sufficient experts
    self_sufficient_checks = {
        'k8s_expertise': f"{inputs.k8s_experience} >= 4 = {inputs.k8s_experience >= 4}",
        'migration_exp_ok': inputs.migration_exp == 'extensive' or (inputs.migration_exp == 'some' and inputs.swarm_percent <= 20 and inputs.automation_level >= 70),
        'dedicated_team': f"{inputs.dedicated_team} == 'yes' = {inputs.dedicated_team == 'yes'}",
        'well_staffed': f"{inputs.platform_team_size} >= 8 = {inputs.platform_team_size >= 8}",
        'minimal_training': f"{inputs.training_needs_count} <= 1 = {inputs.training_needs_count <= 1}",
        'high_automation': f"{inputs.automation_level} >= 70 = {inputs.automation_level >= 70}",
        'mostly_k8s': f"{inputs.swarm_percent} <= 30 = {inputs.swarm_percent <= 30}",
        'is_self_sufficient': _is_self_sufficient(inputs)
    }

    return {
        'assessment_first_checks': assessment_first_checks,
        'overwhelmed_checks': overwhelmed_checks,
        'self_sufficient_checks': self_sufficient_checks,
        'time_constrained': _is_time_constrained(inputs),
        'final_model': determine_engagement_model(inputs).model
    }
