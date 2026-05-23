"""
Generate rich assessment details including validation warnings,
migration scenarios, phase breakdowns, and PS role estimates.
"""
from models.inputs import AssessmentInputs
from models.outputs import MigrationScenario, PhaseDetail, PSRoleBreakdown


def generate_validation_warnings(inputs: AssessmentInputs) -> list[str]:
    """Generate validation warnings for extreme values and infrastructure concerns."""
    warnings = []

    # Team capacity warnings
    if inputs.apps_per_team > 50:
        warnings.append(f"{inputs.apps_per_team:.0f} apps per platform team is extremely high - consider reviewing team capacity")

    if inputs.mke_per_team > 3:
        warnings.append(f"{inputs.mke_per_team:.1f} MKE instances per team member is high - may need additional staffing")

    if inputs.msr_per_team > 0.5:
        warnings.append(f"{inputs.msr_per_team:.1f} MSR instances per team member - will have operational impact on upgrades and maintenance")

    if inputs.swarm_percent > 75 and inputs.k8s_experience < 3:
        warnings.append("High Swarm workload with limited Kubernetes experience - consider Mirantis Training Department courses")

    # MSR Infrastructure warnings (only if MSR is present)
    if inputs.num_msr_instances > 0:
        # PostgreSQL storage concerns
        if inputs.postgresql_storage == 'nfs':
            warnings.append("NFS storage for PostgreSQL may impact database performance - consider local SSD or cloud block storage for production")

        # Blob storage concerns
        if inputs.blob_storage_type == 'nfs':
            warnings.append("NFS for blob storage may limit scalability - consider S3-compatible or cloud blob storage for larger registries")
        if inputs.blob_storage_type == 'local':
            warnings.append("Local blob storage does not support HA - migration to cloud or distributed storage recommended")

        # Network performance concerns
        if inputs.network_performance == 'cross-datacenter':
            warnings.append("Cross-datacenter network may impact image pull performance - consider edge caching or registry replication")
        if inputs.network_performance == 'cross-region':
            warnings.append("Cross-region network latency will significantly impact registry operations - registry placement review required")

        # Self-managed external services
        if inputs.postgresql_deployment == 'external-self-managed':
            warnings.append("Self-managed external PostgreSQL requires dedicated DBA resources for backup, patching, and HA")
        if inputs.redis_deployment == 'external-self-managed':
            warnings.append("Self-managed external Redis requires operational expertise for clustering and persistence")

        # MSR location concerns
        if inputs.msr4_location == 'external':
            warnings.append("External MSR 4.0 deployment adds network dependency - ensure low-latency connectivity to MKE cluster")
        if inputs.msr4_location == 'different-cluster':
            warnings.append("MSR 4.0 on different cluster requires cross-cluster networking - validate connectivity and firewall rules")

    return warnings


def generate_migration_scenario(inputs: AssessmentInputs) -> MigrationScenario:
    """Generate detailed migration scenario based on environment."""

    # Determine scenario type
    has_msr = inputs.num_msr_instances > 0

    if inputs.swarm_percent == 0:
        if has_msr:
            scenario_title = f"Pure Kubernetes Migration: MSR {inputs.msr_version} + MKE {inputs.mke_version}"
            strategy_steps = [
                "Validate current Kubernetes workloads compatibility",
                "Migrate MSR to MSR 4.0 (Harbor-based)",
                "Update CI/CD pipelines for MSR 4.0 API changes",
                "Upgrade MKE to version 4.0",
                "Final validation and performance optimization"
            ]
            key_considerations = [
                "MSR 4.0 uses Harbor backend - API changes require CI/CD updates",
                "Image promotion policies not available in MSR 4.0 - alternative workflows needed",
                "RBAC schema differs - permission mappings must be documented"
            ]
        else:
            # No MSR - MKE only migration
            scenario_title = f"MKE Platform Upgrade: MKE {inputs.mke_version} → MKE 4.0"
            strategy_steps = [
                "Validate current Kubernetes workloads compatibility",
                "Review MKE 4.0 feature changes and breaking changes",
                "Upgrade MKE to version 4.0",
                "Final validation and performance optimization"
            ]
            key_considerations = [
                "MKE 4.0 is Kubernetes-only - ensure no Swarm dependencies",
                "Review networking and storage configurations for compatibility",
                "Update any MKE-specific CLI/API integrations"
            ]
    elif inputs.swarm_percent < 50:
        scenario_title = f"Low Swarm Migration: MSR {inputs.msr_version} + MKE {inputs.mke_version} ({inputs.swarm_percent}% Swarm)"
        strategy_steps = [
            f"Convert remaining {inputs.swarm_percent}% Swarm workloads to Kubernetes",
            "Migrate MSR 2.9 → MSR 4.0 on MKE 3.x Kubernetes",
            "Validate all workloads with new MSR 4.0",
            "Upgrade MKE 3.x → MKE 4.0",
            "Final validation and optimization"
        ]
        key_considerations = [
            "Swarm workload conversion is customer responsibility",
            "Recommend parallel Kubernetes deployment for testing",
            "MSR 4.0 breaking changes require CI/CD pipeline updates"
        ]
    else:
        scenario_title = f"High Swarm Migration: MSR {inputs.msr_version} + MKE {inputs.mke_version} ({inputs.swarm_percent}% Swarm)"
        strategy_steps = [
            f"Plan conversion of {inputs.swarm_percent}% Swarm workloads to Kubernetes",
            "Establish Kubernetes best practices and patterns",
            "Execute phased Swarm-to-Kubernetes migration",
            "Migrate MSR after majority of workloads converted",
            "Upgrade MKE to version 4.0",
            "Final validation and knowledge transfer"
        ]
        key_considerations = [
            f"Significant Swarm workload conversion required ({inputs.swarm_percent}%)",
            "Consider application modernization opportunities during conversion",
            "Extended timeline due to workload transformation",
            "Mirantis Training Department courses recommended for team skills development"
        ]

    # MSR infrastructure risks are now handled separately in generate_validation_warnings()
    # Key considerations here focus on migration approach and best practices only

    # Calculate critical timeline
    # MSR 2.9 EOL is often 12-18 months from assessment
    avg_timeline_months = 6  # Simplified
    critical_timeline = f"{avg_timeline_months:.1f} months estimated (plan for urgency if approaching EOL)"

    return MigrationScenario(
        title=scenario_title,
        strategy_steps=strategy_steps,
        critical_timeline=critical_timeline,
        key_considerations=key_considerations
    )


def _generate_short_phases(inputs: AssessmentInputs, engagement_model: str, total_weeks: float, has_msr: bool, has_swarm: bool = False) -> list[PhaseDetail]:
    """
    Generate condensed 2-3 phase plan for short timelines (1-2 weeks).
    Used for simple MKE upgrades or minimal MSR migrations.
    Note: Short timelines typically don't include major Swarm conversion.
    """

    if total_weeks <= 1:
        # 1-week engagement: 2 phases (Prep + Execute/Validate)
        if engagement_model == 'advisory':
            return [
                PhaseDetail(
                    number=1,
                    name="Preparation & Planning",
                    description="Quick assessment and upgrade preparation",
                    duration_weeks="1-2 days",
                    activities=[
                        "Review current environment and upgrade prerequisites",
                        "Validate workload compatibility with MKE 4.0" if not has_msr else "Validate MSR and MKE upgrade path",
                        "Your team prepares environment; PS validates approach",
                        "Confirm rollback plan and maintenance window"
                    ]
                ),
                PhaseDetail(
                    number=2,
                    name="Upgrade & Validation",
                    description="Execute upgrade and validate functionality",
                    duration_weeks="3-4 days",
                    activities=[
                        "Your team executes MKE upgrade; PS available for support" if not has_msr else "Your team executes MSR then MKE upgrade; PS supports",
                        "Validate all workloads functioning correctly",
                        "Your team performs smoke testing; PS reviews results",
                        "Complete handoff and documentation updates"
                    ]
                )
            ]
        else:  # hybrid or full
            return [
                PhaseDetail(
                    number=1,
                    name="Preparation & Planning",
                    description="Joint assessment and upgrade preparation",
                    duration_weeks="1-2 days",
                    activities=[
                        "PS reviews environment and validates upgrade path",
                        "Joint validation of workload compatibility",
                        "PS prepares upgrade runbook; your team reviews",
                        "Confirm maintenance window and rollback plan"
                    ]
                ),
                PhaseDetail(
                    number=2,
                    name="Upgrade & Validation",
                    description="Execute upgrade and validate functionality",
                    duration_weeks="3-4 days",
                    activities=[
                        "PS leads MKE upgrade execution; your team supports" if not has_msr else "PS leads MSR then MKE upgrade; your team supports",
                        "Joint validation of all workloads",
                        "PS performs comprehensive testing with your team",
                        "Knowledge transfer and documentation handoff"
                    ]
                )
            ]
    else:
        # 2-week engagement: 3 phases (Plan + Execute + Validate)
        if engagement_model == 'advisory':
            return [
                PhaseDetail(
                    number=1,
                    name="Assessment & Planning",
                    description="Environment review and upgrade planning",
                    duration_weeks="2-3 days",
                    activities=[
                        "Your team inventories workloads; PS validates",
                        "Review MKE 4.0 changes and compatibility" if not has_msr else "Review MSR 4.0 and MKE 4.0 migration path",
                        "Your team creates upgrade runbook; PS reviews",
                        "Finalize maintenance windows and communication plan"
                    ]
                ),
                PhaseDetail(
                    number=2,
                    name="Upgrade Execution",
                    description="Execute platform upgrade" if not has_msr else "Execute registry and platform migration",
                    duration_weeks="4-5 days",
                    activities=[
                        "Your team executes MKE upgrade; PS available for escalations" if not has_msr else "Your team executes MSR migration; PS advises",
                        "Your team validates core functionality" if not has_msr else "Your team executes MKE upgrade after MSR",
                        "Your team updates CI/CD pipelines as needed",
                        "Your team performs integration testing; PS spot-checks"
                    ]
                ),
                PhaseDetail(
                    number=3,
                    name="Validation & Handoff",
                    description="Final validation and knowledge transfer",
                    duration_weeks="2-3 days",
                    activities=[
                        "Your team conducts comprehensive testing",
                        "PS provides final review and recommendations",
                        "Your team updates documentation and runbooks",
                        "PS delivers sign-off and optimization tips"
                    ]
                )
            ]
        else:  # hybrid or full
            ps_lead = "PS" if engagement_model == 'full' else "Joint"
            return [
                PhaseDetail(
                    number=1,
                    name="Assessment & Planning",
                    description="Environment review and upgrade planning",
                    duration_weeks="2-3 days",
                    activities=[
                        f"{ps_lead} assessment of current environment",
                        f"{ps_lead} review of upgrade path and compatibility",
                        "PS creates upgrade runbook; your team validates",
                        "Finalize maintenance windows and rollback plan"
                    ]
                ),
                PhaseDetail(
                    number=2,
                    name="Upgrade Execution",
                    description="Execute platform upgrade" if not has_msr else "Execute registry and platform migration",
                    duration_weeks="4-5 days",
                    activities=[
                        f"{ps_lead} MKE upgrade execution" if not has_msr else f"{ps_lead} MSR migration execution",
                        f"{ps_lead} validation of core functionality" if not has_msr else f"{ps_lead} MKE upgrade after MSR complete",
                        f"{ps_lead} CI/CD pipeline updates as needed",
                        f"{ps_lead} integration testing with knowledge transfer"
                    ]
                ),
                PhaseDetail(
                    number=3,
                    name="Validation & Handoff",
                    description="Final validation and knowledge transfer",
                    duration_weeks="2-3 days",
                    activities=[
                        f"{ps_lead} comprehensive testing and validation",
                        "PS provides optimization recommendations",
                        f"{ps_lead} documentation updates",
                        "PS delivers knowledge transfer and sign-off"
                    ]
                )
            ]


def generate_phase_details(inputs: AssessmentInputs, engagement_model: str, total_weeks: float = 14.0) -> list[PhaseDetail]:
    """
    Generate detailed 5-phase breakdown with dynamic durations based on total timeline.

    Phase distribution (proportional to total_weeks):
    - Phase 1: ~12% (Assessment) - min 1 week
    - Phase 2: ~12% (Training) - overlaps with Phase 1, min 1 week
    - Phase 3: ~35% (Transformation) - main work, min 2 weeks
    - Phase 4: ~30% (Execution) - overlaps with Phase 3, min 2 weeks
    - Phase 5: ~10% (Validation) - concurrent with Phase 4, min 1 week
    """

    def format_duration(weeks: float, overlap_note: str = "") -> str:
        """Format week duration with optional overlap note."""
        min_w = max(1, int(weeks * 0.85))
        max_w = max(min_w + 1, int(weeks * 1.15) + 1)
        base = f"{min_w}-{max_w} weeks" if min_w != max_w else f"{min_w} week"
        return f"{base} {overlap_note}".strip() if overlap_note else base

    if engagement_model == 'assessment-first':
        p1_weeks = max(2, total_weeks * 0.20)
        return [
            PhaseDetail(
                number=1,
                name="Comprehensive Assessment",
                description="Deep environment analysis to size remaining phases",
                duration_weeks=format_duration(p1_weeks),
                activities=[
                    "Detailed inventory of all workloads and dependencies",
                    "Performance and capacity baseline",
                    "Risk assessment and mitigation planning",
                    "Sizing of phases 2-5 based on findings"
                ]
            ),
            PhaseDetail(
                number=2,
                name="TBD - Pending Assessment",
                description="Scope determined after Phase 1 completes",
                duration_weeks="TBD",
                activities=["To be determined based on assessment findings"]
            )
        ]

    # Check if MSR migration is needed and if Swarm conversion is needed
    has_msr = inputs.num_msr_instances > 0
    has_swarm = inputs.swarm_percent > 0

    # For short timelines (1-2 weeks), use condensed 2-3 phase plan
    if total_weeks <= 2:
        return _generate_short_phases(inputs, engagement_model, total_weeks, has_msr, has_swarm)

    # Dynamic phase durations based on total timeline (3+ weeks = full 5 phases)
    p1_weeks = max(1, total_weeks * 0.12)  # Assessment: ~12%
    p2_weeks = max(1, total_weeks * 0.12)  # Training: ~12%
    p3_weeks = max(2, total_weeks * 0.35)  # Transformation: ~35%
    p4_weeks = max(2, total_weeks * 0.30)  # Execution: ~30%
    p5_weeks = max(1, total_weeks * 0.10)  # Validation: ~10%

    # Define activities based on engagement model (who does what)
    # Activities differ based on MSR migration and Swarm conversion needs
    if engagement_model == 'advisory':
        # Advisory: Customer-led with PS validation (27.5% PS effort)
        p1_activities = [
            "Your team inventories workloads with PS validation",
            "Your team documents architecture; PS reviews for gaps",
            "Your team identifies risks; PS provides mitigation strategies",
            "Your team creates runbook; PS validates approach"
        ]
        if has_msr and has_swarm:
            # MSR + Swarm conversion
            p2_activities = [
                "PS provides enablement on advanced migration patterns (formal training via Mirantis Training Department)",
                "Your team completes MSR 4.0 self-paced learning materials",
                "PS conducts hands-on workshop on Swarm-to-Kubernetes conversion",
                "Your team establishes standards with PS guidance"
            ]
            p3_activities = [
                "Your team converts Swarm workloads to Kubernetes; PS reviews",
                "Your team updates CI/CD pipelines; PS spot-checks",
                "Your team sets up MSR 4.0 infrastructure; PS advises",
                "Your team runs performance tests; PS validates results"
            ]
            p4_activities = [
                "Your team executes image migration; PS available for escalations",
                "Your team migrates authentication; PS reviews configuration",
                "Your team updates applications; PS validates critical paths",
                "Your team validates integrations; PS confirms readiness"
            ]
        elif has_msr:
            # MSR only (pure Kubernetes)
            p2_activities = [
                "PS provides enablement on MSR 4.0 features (formal training via Mirantis Training Department)",
                "Your team completes MSR 4.0 self-paced learning materials",
                "PS conducts hands-on workshop on registry migration best practices",
                "Your team establishes standards with PS guidance"
            ]
            p3_activities = [
                "Your team prepares Kubernetes workloads for MSR 4.0; PS reviews",
                "Your team updates CI/CD pipelines for new registry; PS spot-checks",
                "Your team sets up MSR 4.0 infrastructure; PS advises",
                "Your team runs performance tests; PS validates results"
            ]
            p4_activities = [
                "Your team executes image migration; PS available for escalations",
                "Your team migrates authentication; PS reviews configuration",
                "Your team updates applications; PS validates critical paths",
                "Your team validates integrations; PS confirms readiness"
            ]
        elif has_swarm:
            # Swarm conversion only (no MSR)
            p2_activities = [
                "PS provides enablement on MKE 4.0 features (formal training via Mirantis Training Department)",
                "Your team reviews Swarm-to-Kubernetes conversion patterns",
                "PS conducts hands-on workshop on workload conversion best practices",
                "Your team establishes operational standards with PS guidance"
            ]
            p3_activities = [
                "Your team converts Swarm workloads to Kubernetes; PS reviews",
                "Your team updates CI/CD pipelines for MKE 4.0; PS spot-checks",
                "Your team validates converted workloads; PS advises",
                "Your team runs pre-upgrade tests; PS validates results"
            ]
            p4_activities = [
                "Your team executes MKE upgrade; PS available for escalations",
                "Your team validates authentication post-upgrade; PS reviews",
                "Your team updates applications; PS validates critical paths",
                "Your team validates integrations; PS confirms readiness"
            ]
        else:
            # MKE upgrade only (pure Kubernetes, no MSR)
            p2_activities = [
                "PS provides enablement on MKE 4.0 features (formal training via Mirantis Training Department)",
                "Your team reviews MKE 4.0 migration documentation",
                "PS conducts hands-on workshop on upgrade best practices",
                "Your team establishes operational standards with PS guidance"
            ]
            p3_activities = [
                "Your team prepares workloads for MKE 4.0; PS reviews",
                "Your team updates CI/CD pipelines for MKE 4.0; PS spot-checks",
                "Your team validates Kubernetes compatibility; PS advises",
                "Your team runs pre-upgrade tests; PS validates results"
            ]
            p4_activities = [
                "Your team executes MKE upgrade; PS available for escalations",
                "Your team validates authentication post-upgrade; PS reviews",
                "Your team updates applications; PS validates critical paths",
                "Your team validates integrations; PS confirms readiness"
            ]
        p5_activities = [
            "Your team conducts comprehensive testing",
            "Your team performs optimization; PS provides recommendations",
            "Your team updates documentation and runbooks",
            "PS delivers final optimization review and sign-off"
        ]
    elif engagement_model == 'hybrid':
        # Hybrid: Shared responsibility (62.5% PS effort)
        p1_activities = [
            "Joint assessment - PS leads with your team participation",
            "PS documents architecture with your team input",
            "Collaborative risk identification and mitigation planning",
            "PS creates runbook; your team validates for operational fit"
        ]
        if has_msr and has_swarm:
            # MSR + Swarm conversion
            p2_activities = [
                "PS delivers hands-on enablement with your team practicing",
                "Joint MSR 4.0 and Kubernetes conversion knowledge transfer",
                "PS demonstrates Swarm-to-K8s migration tools; your team practices",
                "Collaborative establishment of standards and practices"
            ]
            p3_activities = [
                "Joint Swarm-to-Kubernetes conversion with PS leading complex workloads",
                "Shared CI/CD pipeline updates with PS leading patterns",
                "PS sets up MSR 4.0 infrastructure; your team learns alongside",
                "Joint performance testing with knowledge transfer"
            ]
            p4_activities = [
                "Shared execution - PS leads critical paths, you handle routine",
                "Joint authentication migration with clear role splits",
                "PS updates complex applications; your team handles standard ones",
                "Collaborative integration validation"
            ]
        elif has_msr:
            # MSR only (pure Kubernetes)
            p2_activities = [
                "PS delivers hands-on MSR 4.0 enablement with your team",
                "Joint MSR 4.0 administration knowledge transfer and labs",
                "PS demonstrates registry migration tools; your team practices",
                "Collaborative establishment of standards and practices"
            ]
            p3_activities = [
                "Joint preparation of Kubernetes workloads for MSR 4.0",
                "Shared CI/CD pipeline updates for new registry",
                "PS sets up MSR 4.0 infrastructure; your team learns alongside",
                "Joint performance testing with knowledge transfer"
            ]
            p4_activities = [
                "Shared image migration - PS leads critical paths, you handle routine",
                "Joint authentication migration with clear role splits",
                "PS updates complex applications; your team handles standard ones",
                "Collaborative integration validation"
            ]
        elif has_swarm:
            # Swarm conversion only (no MSR)
            p2_activities = [
                "PS delivers hands-on MKE 4.0 enablement with your team",
                "Joint Swarm-to-Kubernetes conversion knowledge transfer",
                "PS demonstrates workload conversion; your team practices",
                "Collaborative establishment of operational standards"
            ]
            p3_activities = [
                "Joint Swarm-to-Kubernetes conversion with PS leading complex workloads",
                "Shared CI/CD pipeline updates for MKE 4.0",
                "PS validates converted workloads; your team prepares environment",
                "Joint pre-upgrade testing with knowledge transfer"
            ]
            p4_activities = [
                "Shared MKE upgrade execution - PS leads, you support",
                "Joint post-upgrade validation with clear role splits",
                "PS validates complex workloads; your team handles standard ones",
                "Collaborative integration validation"
            ]
        else:
            # MKE upgrade only (pure Kubernetes, no MSR)
            p2_activities = [
                "PS delivers hands-on MKE 4.0 enablement with your team",
                "Joint review of MKE 4.0 features and changes",
                "PS demonstrates upgrade process; your team practices",
                "Collaborative establishment of operational standards"
            ]
            p3_activities = [
                "Joint workload preparation for MKE 4.0 compatibility",
                "Shared CI/CD pipeline updates for MKE 4.0",
                "PS validates upgrade prerequisites; your team prepares environment",
                "Joint pre-upgrade testing with knowledge transfer"
            ]
            p4_activities = [
                "Shared MKE upgrade execution - PS leads, you support",
                "Joint post-upgrade validation with clear role splits",
                "PS validates complex workloads; your team handles standard ones",
                "Collaborative integration validation"
            ]
        p5_activities = [
            "Joint comprehensive testing and validation",
            "Collaborative performance tuning with knowledge transfer",
            "PS and your team co-author documentation together",
            "Joint knowledge transfer sessions and operational readiness"
        ]
    else:  # 'full' engagement model
        # Full: PS-led execution (87.5% PS effort)
        p1_activities = [
            "PS conducts comprehensive assessment with your team oversight",
            "PS documents architecture; your team provides context",
            "PS identifies risks and plans mitigation; your team reviews",
            "PS creates detailed runbook; your team learns the approach"
        ]
        if has_msr and has_swarm:
            # MSR + Swarm conversion
            p2_activities = [
                "PS enables your team while handling migration complexity (formal training via Mirantis Training Department)",
                "PS delivers comprehensive MSR 4.0 and K8s conversion enablement",
                "PS demonstrates Swarm-to-K8s tools and procedures; your team observes",
                "PS establishes standards and practices; your team learns"
            ]
            p3_activities = [
                "PS converts Swarm workloads to Kubernetes; your team observes",
                "PS updates CI/CD pipelines; your team reviews changes",
                "PS sets up MSR 4.0 infrastructure; your team shadows",
                "PS conducts performance testing; your team validates results"
            ]
            p4_activities = [
                "PS executes migration end-to-end with your team supporting",
                "PS migrates authentication; your team provides access/approvals",
                "PS updates applications; your team validates functionality",
                "PS validates integrations; your team confirms operational fit"
            ]
        elif has_msr:
            # MSR only (pure Kubernetes)
            p2_activities = [
                "PS enables your team on MSR 4.0 features and operations (formal training via Mirantis Training Department)",
                "PS delivers comprehensive MSR 4.0 enablement program",
                "PS demonstrates registry migration tools; your team observes",
                "PS establishes standards and practices; your team learns"
            ]
            p3_activities = [
                "PS prepares Kubernetes workloads for MSR 4.0; your team observes",
                "PS updates CI/CD pipelines for new registry; your team reviews",
                "PS sets up MSR 4.0 infrastructure; your team shadows",
                "PS conducts performance testing; your team validates results"
            ]
            p4_activities = [
                "PS executes image migration end-to-end with your team supporting",
                "PS migrates authentication; your team provides access/approvals",
                "PS updates applications; your team validates functionality",
                "PS validates integrations; your team confirms operational fit"
            ]
        elif has_swarm:
            # Swarm conversion only (no MSR)
            p2_activities = [
                "PS enables your team on MKE 4.0 and Kubernetes conversion (formal training via Mirantis Training Department)",
                "PS delivers Swarm-to-Kubernetes enablement program",
                "PS demonstrates workload conversion procedures; your team observes",
                "PS establishes operational standards; your team learns"
            ]
            p3_activities = [
                "PS converts Swarm workloads to Kubernetes; your team observes",
                "PS updates CI/CD pipelines; your team reviews changes",
                "PS validates converted workloads; your team shadows",
                "PS conducts pre-upgrade testing; your team validates results"
            ]
            p4_activities = [
                "PS executes MKE upgrade end-to-end with your team supporting",
                "PS validates authentication; your team provides access/approvals",
                "PS updates applications; your team validates functionality",
                "PS validates integrations; your team confirms operational fit"
            ]
        else:
            # MKE upgrade only (pure Kubernetes, no MSR)
            p2_activities = [
                "PS enables your team on MKE 4.0 features and operations (formal training via Mirantis Training Department)",
                "PS delivers MKE 4.0 administration enablement",
                "PS demonstrates upgrade procedures; your team observes",
                "PS establishes operational standards; your team learns"
            ]
            p3_activities = [
                "PS prepares workloads for MKE 4.0; your team observes",
                "PS updates CI/CD pipelines; your team reviews changes",
                "PS validates upgrade prerequisites; your team shadows",
                "PS conducts pre-upgrade testing; your team validates results"
            ]
            p4_activities = [
                "PS executes MKE upgrade end-to-end with your team supporting",
                "PS validates authentication; your team provides access/approvals",
                "PS updates applications; your team validates functionality",
                "PS validates integrations; your team confirms operational fit"
            ]
        p5_activities = [
            "PS validates and optimizes with your team participation",
            "PS performs tuning; your team learns optimization techniques",
            "PS creates documentation; your team reviews for operational needs",
            "PS transfers operational knowledge and provides certification"
        ]

    # Phase 3 name/description depends on what work is being done
    if has_swarm:
        p3_name = "Transformation & Preparation"
        p3_desc = "Convert Swarm workloads to Kubernetes and prepare environment"
    elif has_msr:
        p3_name = "Preparation & Setup"
        p3_desc = "Prepare environment and registry infrastructure"
    else:
        p3_name = "Preparation"
        p3_desc = "Prepare environment for platform upgrade"

    # Phase 4 description based on scope
    if has_msr and has_swarm:
        p4_desc = "Execute registry and platform migration"
    elif has_msr:
        p4_desc = "Execute registry migration and platform upgrade"
    elif has_swarm:
        p4_desc = "Execute MKE platform upgrade"
    else:
        p4_desc = "Execute MKE platform upgrade"

    phases = [
        PhaseDetail(
            number=1,
            name="Assessment & Planning",
            description="Complete detailed current state analysis and migration plan",
            duration_weeks=format_duration(p1_weeks),
            activities=p1_activities
        ),
        PhaseDetail(
            number=2,
            name="Enablement & Training",
            description="Build team capabilities for migration and ongoing operations",
            duration_weeks=format_duration(p2_weeks, "(overlaps with Phase 1)"),
            activities=p2_activities
        ),
        PhaseDetail(
            number=3,
            name=p3_name,
            description=p3_desc,
            duration_weeks=format_duration(p3_weeks, "(begins during Phase 2)"),
            activities=p3_activities
        ),
        PhaseDetail(
            number=4,
            name="Migration Execution",
            description=p4_desc,
            duration_weeks=format_duration(p4_weeks, "(overlaps with Phase 3)"),
            activities=p4_activities
        ),
        PhaseDetail(
            number=5,
            name="Validation & Optimization",
            description="Final validation and knowledge transfer",
            duration_weeks=format_duration(p5_weeks, "(concurrent with Phase 4)"),
            activities=p5_activities
        )
    ]

    return phases


def generate_ps_role_breakdown(engagement_model_type: str, ps_effort_percent: float, avg_timeline_months: float) -> list[PSRoleBreakdown]:
    """
    Generate PS role breakdown based on engagement model.

    CRITICAL FIX: Distribute ps_effort_percent across roles instead of multiplying timeline by each role.

    Previous error: Roles were calculated as percentages of total timeline, leading to 250-270%
    over-estimation. For a 20-week timeline at 87.5% PS effort, this incorrectly calculated 54 weeks
    (2.85x over-estimate) instead of the correct 17.5 weeks.

    Fixed approach: Calculate total PS weeks first (timeline × ps_effort_percent), then distribute
    across roles based on engagement model needs.
    """

    if engagement_model_type == 'assessment-first':
        return [
            PSRoleBreakdown(
                role="PS Lead Architect",
                weeks="2-4 weeks",
                description="Comprehensive environment assessment and remaining phase sizing"
            ),
            PSRoleBreakdown(
                role="Remaining Roles",
                weeks="TBD",
                description="Determined after assessment phase completes"
            )
        ]

    total_weeks = avg_timeline_months * 4.33
    ps_weeks = total_weeks * (ps_effort_percent / 100)  # Total PS effort budget

    if engagement_model_type == 'full':
        # Full model: Distribute 87.5% PS effort across roles
        # Lead: 45%, Engineer: 35%, PM: 20% of PS budget
        return [
            PSRoleBreakdown(
                role="PS Lead Architect",
                weeks=f"{ps_weeks * 0.40:.0f}-{ps_weeks * 0.50:.0f} weeks",
                description="Technical leadership and decision-making throughout entire migration"
            ),
            PSRoleBreakdown(
                role="PS Migration Engineer",
                weeks=f"{ps_weeks * 0.30:.0f}-{ps_weeks * 0.40:.0f} weeks",
                description="Hands-on migration execution and technical implementation"
            ),
            PSRoleBreakdown(
                role="PS Project Manager",
                weeks=f"{ps_weeks * 0.15:.0f}-{ps_weeks * 0.25:.0f} weeks",
                description="Project coordination, risk management, and stakeholder communication"
            )
        ]
    elif engagement_model_type == 'hybrid':
        # Hybrid model: Distribute 62.5% PS effort across roles
        # Lead: 50%, Engineer: 35%, PM: 15% of PS budget
        return [
            PSRoleBreakdown(
                role="PS Lead Architect",
                weeks=f"{ps_weeks * 0.45:.0f}-{ps_weeks * 0.55:.0f} weeks",
                description="Technical guidance and critical decision support"
            ),
            PSRoleBreakdown(
                role="PS Migration Engineer",
                weeks=f"{ps_weeks * 0.30:.0f}-{ps_weeks * 0.40:.0f} weeks",
                description="Complex migration tasks and technical validation"
            ),
            PSRoleBreakdown(
                role="PS Project Manager",
                weeks=f"{ps_weeks * 0.10:.0f}-{ps_weeks * 0.20:.0f} weeks",
                description="Planning oversight and milestone tracking"
            )
        ]
    else:  # advisory
        # Advisory model: Distribute 27.5% PS effort across roles
        # Advisor: 70%, Specialist: 30% of PS budget
        return [
            PSRoleBreakdown(
                role="PS Technical Advisor",
                weeks=f"{ps_weeks * 0.60:.0f}-{ps_weeks * 0.80:.0f} weeks",
                description="Strategic guidance and architecture review"
            ),
            PSRoleBreakdown(
                role="PS Specialist (on-demand)",
                weeks=f"{ps_weeks * 0.20:.0f}-{ps_weeks * 0.40:.0f} weeks",
                description="Targeted support for complex scenarios"
            )
        ]


def generate_immediate_actions(inputs: AssessmentInputs, engagement_model_type: str) -> list[str]:
    """Generate immediate action items."""
    actions = []

    if inputs.dedicated_team in ['no', 'partial']:
        actions.append("Allocate dedicated team resources for migration project")

    if inputs.k8s_experience < 3:
        actions.append("Enroll team in Mirantis Training Department Kubernetes courses")

    # If training needs are indicated, recommend Mirantis Training Department
    if inputs.training_needs_count > 0:
        training_areas = []
        if inputs.k8s_experience < 4:
            training_areas.append("Kubernetes")
        if inputs.swarm_percent > 30:
            training_areas.append("container modernization")
        if inputs.num_msr_instances > 0:
            training_areas.append("MSR 4.0 administration")
        if training_areas:
            actions.append(f"Schedule Mirantis Training Department courses for: {', '.join(training_areas)}")
        else:
            actions.append("Schedule Mirantis Training Department courses for team skill development")

    if inputs.swarm_percent > 50:
        actions.append("Start planning Swarm-to-Kubernetes conversion strategy")

    if inputs.automation_level < 50:
        actions.append("Assess and improve CI/CD automation before migration")

    if engagement_model_type == 'assessment-first':
        actions.append("Schedule comprehensive assessment engagement within 2 weeks")

    if not actions:
        actions.append("Review and approve migration plan with stakeholders")
        actions.append("Schedule kick-off meeting with Professional Services team")

    return actions
