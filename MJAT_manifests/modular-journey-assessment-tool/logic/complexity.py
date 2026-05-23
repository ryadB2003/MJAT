"""
Complexity score calculation.
Measures how difficult the migration will be based on environment factors.
"""
from models.inputs import AssessmentInputs


def calculate_complexity_score(inputs: AssessmentInputs) -> tuple[int, str]:
    """
    Calculate complexity score (0-100) and level.

    Returns:
        tuple: (score, level) where level is one of:
               "Low" (0-30), "Low-Medium" (31-45), "Medium" (46-60),
               "Significant" (61+)
    """
    score = 0.0

    # MSR Version complexity (biggest factor)
    score += _msr_version_complexity(inputs.msr_version)

    # MKE Version complexity
    score += _mke_version_complexity(inputs.mke_version)

    # Air-gapped environment complexity
    score += _air_gapped_complexity(inputs.air_gapped)

    # MKE instance count (context-aware)
    score += _mke_complexity(inputs)

    # Node count (per-MKE basis)
    score += _node_complexity(inputs)

    # Swarm percentage (conversion complexity)
    score += _swarm_complexity(inputs.swarm_percent)

    # Application count
    score += _app_complexity(inputs.app_count)

    # Deployment frequency (maturity indicator)
    score += _deployment_frequency_complexity(inputs)

    # Cap at 100
    score = max(0, min(100, round(score)))

    # Determine level
    if score <= 30:
        level = "Low"
    elif score <= 45:
        level = "Low-Medium"
    elif score <= 60:
        level = "Medium"
    else:
        level = "Significant"

    return score, level


def _air_gapped_complexity(air_gapped: bool) -> float:
    """Air-gapped environment complexity - requires offline mirrors, manual transfers"""
    return 5 if air_gapped else 0


def _msr_version_complexity(version: str) -> float:
    """MSR version upgrade complexity"""
    # Parse full version (e.g., "2.9" -> 2.9, not just "2")
    try:
        full_version = float(version)
    except ValueError:
        # Handle versions like "3.1-k8s" by taking numeric prefix
        full_version = float(version.split('-')[0])

    if full_version <= 2.8:
        return 25  # MSR 2.8 or earlier to 4.0
    elif full_version < 3.0:
        return 20  # MSR 2.9 to 4.0
    else:
        return 10  # MSR 3.x to 4.0


def _mke_version_complexity(version: str) -> float:
    """MKE version upgrade complexity"""
    # Parse full version (e.g., "3.8" -> 3.8, not just "3")
    try:
        full_version = float(version)
    except ValueError:
        # Handle versions with suffixes by taking numeric prefix
        full_version = float(version.split('-')[0])

    if full_version <= 3.5:
        return 10  # MKE 3.5 or earlier
    elif full_version <= 3.7:
        return 5   # MKE 3.6-3.7
    return 3  # MKE 3.8+


def _mke_complexity(inputs: AssessmentInputs) -> float:
    """
    Context-aware MKE instance count complexity.

    Penalizes only if:
    - Understaffed (>2 MKE instances per person)
    - Complex workloads (>30% Swarm)

    Rewards if:
    - Well-managed (≤1.5 MKE instances per person)
    - Expert team (K8s exp ≥4)
    - Pure K8s (0% Swarm)
    """
    has_staffing_issues = inputs.mke_per_team > 2
    has_complex_workloads = inputs.swarm_percent > 30

    # Penalize if understaffed or complex
    if has_staffing_issues or has_complex_workloads:
        if inputs.num_mke_instances > 15:
            return 10
        elif inputs.num_mke_instances > 10:
            return 5
        elif inputs.num_mke_instances > 5:
            return 3

    # Reward well-managed environments
    elif (inputs.swarm_percent == 0 and
          inputs.k8s_experience >= 4 and
          inputs.mke_per_team <= 1.5):
        return -5  # Bonus for excellent management

    return 0


def _node_complexity(inputs: AssessmentInputs) -> float:
    """Node count complexity based on nodes-per-MKE"""
    nodes_per_mke = inputs.nodes_per_mke

    if nodes_per_mke > 100:
        return 15  # Very large MKE instances
    elif nodes_per_mke > 50:
        return 10  # Large MKE instances
    elif nodes_per_mke > 30:
        return 5   # Medium MKE instances

    return 0  # Small MKE instances are easier


def _swarm_complexity(swarm_percent: int) -> float:
    """Swarm conversion complexity"""
    if swarm_percent == 0:
        return 0  # Pure K8s = no conversion
    elif swarm_percent <= 20:
        return 5  # Minimal Swarm
    elif swarm_percent <= 50:
        return 10  # Balanced
    elif swarm_percent <= 75:
        return 15  # Heavy Swarm
    else:
        return 20  # Almost all Swarm


def _app_complexity(app_count: int) -> float:
    """Application count complexity"""
    if app_count <= 50:
        return 0
    elif app_count <= 100:
        return 3
    elif app_count <= 300:
        return 5
    elif app_count <= 500:
        return 8
    else:
        return 10


def _deployment_frequency_complexity(inputs: AssessmentInputs) -> float:
    """
    Deployment frequency as maturity indicator.

    High frequency + high automation = mature DevOps = REDUCES complexity
    High frequency + low automation = manual chaos = INCREASES complexity
    """
    freq = inputs.deploy_frequency
    automation = inputs.automation_level

    # Multiple-daily or daily deployments
    if freq in ['multiple-daily', 'daily']:
        if automation >= 60:
            return -3  # Well-automated = mature = easier migration
        else:
            return 5  # Manual chaos = harder migration

    # Weekly with good automation
    elif freq == 'weekly' and automation >= 70:
        return -1  # Good practices

    # Infrequent deployments
    elif freq in ['monthly', 'quarterly']:
        return 3  # Rusty processes = higher risk

    return 0
