"""
Comprehensive test scenarios for engagement model validation.
Tests all four engagement models across various conditions.
Updated to match current input model and account for app-count scaling.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.inputs import AssessmentInputs
from logic.engagement import determine_engagement_model, explain_engagement_decision


def test_distributed_chaos_condition1():
    """
    Test Distributed Chaos - Condition 1:
    Hybrid infrastructure triggers assessment-first
    """
    inputs = AssessmentInputs(
        company_name="MegaCorp",
        industry="technology",
        company_size="enterprise",
        msr_version="3.1",
        mke_version="3.7",
        infra_location='hybrid',  # Hybrid triggers assessment-first
        num_mke_instances=20,
        num_msr_instances=2,
        total_nodes=100,
        app_count=200,
        swarm_percent=40,
        kubernetes_percent=60,
        mission_critical_percent=30,
        business_critical_percent=40,
        platform_team_size=5,
        application_teams=20,
        k8s_experience=3,
        migration_exp='some',
        dedicated_team='partial',
        training_needs_count=2,
        automation_level=60,
        deploy_frequency='weekly',
        msr4_location='same-cluster',
        network_performance='same-datacenter',
        postgresql_deployment='in-cluster',
        redis_deployment='in-cluster-zalando',
        postgresql_storage='nfs',
        blob_storage_type='nfs',
        auth_method='ldap',
        features_required=[]
    )

    result = determine_engagement_model(inputs)
    explanation = explain_engagement_decision(inputs)

    print("\n=== TEST: Distributed Chaos - Condition 1 (Hybrid Infrastructure) ===")
    print(f"Infrastructure: {inputs.infra_location}")
    print(f"Expected: assessment-first")
    print(f"Actual: {result.model}")
    print(f"Model Name: {result.name}")
    print(f"Debug: {explanation['assessment_first_checks']}")

    assert result.model == 'assessment-first', f"Expected 'assessment-first', got '{result.model}'"
    print("✅ PASSED")
    return True


def test_distributed_chaos_condition2():
    """
    Test Distributed Chaos - Condition 2:
    Multi-cloud infrastructure triggers assessment-first
    """
    inputs = AssessmentInputs(
        company_name="MultiRegistry Inc",
        industry="financial",
        company_size="large",
        msr_version="3.1",
        mke_version="3.7",
        infra_location='multi',  # Multi-cloud triggers assessment-first
        num_mke_instances=5,
        num_msr_instances=8,
        total_nodes=50,
        app_count=100,
        swarm_percent=30,
        kubernetes_percent=70,
        mission_critical_percent=40,
        business_critical_percent=30,
        platform_team_size=10,
        application_teams=10,
        k8s_experience=3,
        migration_exp='some',
        dedicated_team='yes',
        training_needs_count=1,
        automation_level=65,
        deploy_frequency='weekly',
        msr4_location='same-cluster',
        network_performance='same-datacenter',
        postgresql_deployment='in-cluster',
        redis_deployment='in-cluster-zalando',
        postgresql_storage='nfs',
        blob_storage_type='nfs',
        auth_method='ldap',
        features_required=[]
    )

    result = determine_engagement_model(inputs)
    explanation = explain_engagement_decision(inputs)

    print("\n=== TEST: Distributed Chaos - Condition 2 (Multi-Cloud Infrastructure) ===")
    print(f"Infrastructure: {inputs.infra_location}")
    print(f"Expected: assessment-first")
    print(f"Actual: {result.model}")
    print(f"Debug: {explanation['assessment_first_checks']}")

    assert result.model == 'assessment-first', f"Expected 'assessment-first', got '{result.model}'"
    print("✅ PASSED")
    return True


def test_overwhelmed_organization():
    """
    Test Overwhelmed Organization:
    Minimal K8s, no migration exp, no dedicated team, small team,
    many training needs, heavy Swarm OR low automation
    """
    inputs = AssessmentInputs(
        company_name="Struggling Startup",
        industry="retail",
        company_size="small",
        msr_version="2.9",
        mke_version="3.6",
        num_mke_instances=2,
        num_msr_instances=1,
        total_nodes=10,
        app_count=30,  # Small app count = base PS effort (no scaling)
        swarm_percent=80,  # >= 75
        kubernetes_percent=20,
        mission_critical_percent=50,
        business_critical_percent=30,
        platform_team_size=2,  # <= 2 (trigger condition)
        application_teams=3,
        k8s_experience=1,  # <= 2
        migration_exp='none',  # 'none'
        dedicated_team='no',  # 'no' or 'partial'
        training_needs_count=4,  # >= 3
        automation_level=25,  # < 30
        deploy_frequency='monthly',
        msr4_location='same-cluster',
        network_performance='same-datacenter',
        postgresql_deployment='in-cluster',
        redis_deployment='in-cluster-zalando',
        postgresql_storage='nfs',
        blob_storage_type='nfs',
        auth_method='local',
        features_required=[]
    )

    result = determine_engagement_model(inputs)

    print("\n=== TEST: Overwhelmed Organization ===")
    print(f"K8s Experience: {inputs.k8s_experience}")
    print(f"Migration Exp: {inputs.migration_exp}")
    print(f"Dedicated Team: {inputs.dedicated_team}")
    print(f"Team Size: {inputs.platform_team_size}")
    print(f"Training Needs: {inputs.training_needs_count}")
    print(f"Swarm %: {inputs.swarm_percent}")
    print(f"Automation: {inputs.automation_level}")
    print(f"Expected: full")
    print(f"Actual: {result.model}")
    print(f"PS Effort: {result.ps_effort_percent}%")

    assert result.model == 'full', f"Expected 'full', got '{result.model}'"
    # PS effort scales with app count: 30 apps = 1.0x, so base 87.5%
    assert 85.0 <= result.ps_effort_percent <= 90.0, f"Expected PS effort 85-90%, got {result.ps_effort_percent}%"
    print("✅ PASSED")
    return True


def test_self_sufficient_innovator():
    """
    Test Self-Sufficient Innovator (ACME scenario):
    Advanced K8s (4-5), extensive migration exp OR (some + minimal Swarm + high automation),
    dedicated team, well-staffed (>=8), minimal training, high automation, mostly K8s
    """
    inputs = AssessmentInputs(
        company_name="ACME Corp",
        industry="technology",
        company_size="large",
        msr_version="3.1",
        mke_version="3.7",
        num_mke_instances=3,
        num_msr_instances=2,
        total_nodes=50,
        app_count=120,  # 120 apps = 1.10x scaling (101-200 range)
        swarm_percent=10,  # <= 30 (mostly K8s)
        kubernetes_percent=90,
        mission_critical_percent=40,
        business_critical_percent=35,
        platform_team_size=12,  # >= 8 (well-staffed)
        application_teams=15,
        k8s_experience=5,  # >= 4 (advanced/expert)
        migration_exp='extensive',  # 'extensive'
        dedicated_team='yes',  # 'yes'
        training_needs_count=0,  # <= 1 (minimal training)
        automation_level=85,  # >= 70 (high automation)
        deploy_frequency='daily',
        msr4_location='same-cluster',
        network_performance='same-datacenter',
        postgresql_deployment='in-cluster',
        redis_deployment='in-cluster-zalando',
        postgresql_storage='nfs',
        blob_storage_type='nfs',
        auth_method='oidc',
        features_required=[]
    )

    result = determine_engagement_model(inputs)
    explanation = explain_engagement_decision(inputs)

    print("\n=== TEST: Self-Sufficient Innovator (ACME) ===")
    print(f"K8s Experience: {inputs.k8s_experience}/5")
    print(f"Migration Exp: {inputs.migration_exp}")
    print(f"Dedicated Team: {inputs.dedicated_team}")
    print(f"Team Size: {inputs.platform_team_size}")
    print(f"Training Needs: {inputs.training_needs_count}")
    print(f"Swarm %: {inputs.swarm_percent}")
    print(f"Automation: {inputs.automation_level}%")
    print(f"Expected: advisory")
    print(f"Actual: {result.model}")
    print(f"PS Effort: {result.ps_effort_percent}%")
    print("\nSelf-Sufficient Checks:")
    for key, value in explanation['self_sufficient_checks'].items():
        print(f"  {key}: {value}")

    assert result.model == 'advisory', f"Expected 'advisory', got '{result.model}'"
    # PS effort scales with app count: 120 apps = 1.10x, base 27.5% * 1.10 = 30.25%
    assert 27.0 <= result.ps_effort_percent <= 35.0, f"Expected PS effort 27-35%, got {result.ps_effort_percent}%"
    print("✅ PASSED")
    return True


def test_skilled_time_constrained():
    """
    Test Skilled but Time-Constrained:
    Intermediate K8s (3), some migration exp, can't fully dedicate,
    medium team (4-8), some training gaps, good automation, balanced workload
    """
    inputs = AssessmentInputs(
        company_name="Busy Enterprise",
        industry="healthcare",
        company_size="medium",
        msr_version="3.1",
        mke_version="3.7",
        num_mke_instances=4,
        num_msr_instances=2,
        total_nodes=40,
        app_count=80,  # 80 apps = 1.05x scaling (51-100 range)
        swarm_percent=50,  # 20-75 (balanced, within time-constrained range)
        kubernetes_percent=50,
        mission_critical_percent=35,
        business_critical_percent=40,
        platform_team_size=5,  # 4-8 (medium-sized)
        application_teams=10,
        k8s_experience=3,  # 3-4 (intermediate)
        migration_exp='some',  # 'some'
        dedicated_team='partial',  # not 'yes'
        training_needs_count=2,  # <= 2
        automation_level=55,  # >= 50
        deploy_frequency='weekly',
        msr4_location='same-cluster',
        network_performance='same-datacenter',
        postgresql_deployment='in-cluster',
        redis_deployment='in-cluster-zalando',
        postgresql_storage='nfs',
        blob_storage_type='nfs',
        auth_method='ldap',
        features_required=[]
    )

    result = determine_engagement_model(inputs)

    print("\n=== TEST: Skilled but Time-Constrained ===")
    print(f"K8s Experience: {inputs.k8s_experience}/5")
    print(f"Migration Exp: {inputs.migration_exp}")
    print(f"Dedicated Team: {inputs.dedicated_team}")
    print(f"Team Size: {inputs.platform_team_size}")
    print(f"Training Needs: {inputs.training_needs_count}")
    print(f"Swarm %: {inputs.swarm_percent}")
    print(f"Automation: {inputs.automation_level}%")
    print(f"Expected: hybrid")
    print(f"Actual: {result.model}")
    print(f"PS Effort: {result.ps_effort_percent}%")

    assert result.model == 'hybrid', f"Expected 'hybrid', got '{result.model}'"
    # PS effort scales with app count: 80 apps = 1.05x, base 62.5% * 1.05 = 65.6%
    assert 60.0 <= result.ps_effort_percent <= 70.0, f"Expected PS effort 60-70%, got {result.ps_effort_percent}%"
    print("✅ PASSED")
    return True


def test_alternative_self_sufficient():
    """
    Test Self-Sufficient with alternative path:
    Some migration exp + minimal Swarm (<=20%) + high automation (>=70%)
    """
    inputs = AssessmentInputs(
        company_name="Tech Leaders Inc",
        industry="technology",
        company_size="medium",
        msr_version="3.1",
        mke_version="3.8",
        num_mke_instances=4,
        num_msr_instances=1,
        total_nodes=60,
        app_count=100,  # 100 apps = 1.05x scaling (51-100 range)
        swarm_percent=15,  # <= 20
        kubernetes_percent=85,
        mission_critical_percent=30,
        business_critical_percent=40,
        platform_team_size=10,  # >= 6 (relaxed from 8)
        application_teams=12,
        k8s_experience=4,  # >= 4
        migration_exp='some',  # 'some' (not extensive, but qualifies via alternative)
        dedicated_team='yes',  # 'yes'
        training_needs_count=1,  # <= 2 (relaxed from 1)
        automation_level=80,  # >= 60 (relaxed from 70)
        deploy_frequency='daily',
        msr4_location='same-cluster',
        network_performance='same-datacenter',
        postgresql_deployment='in-cluster',
        redis_deployment='in-cluster-zalando',
        postgresql_storage='nfs',
        blob_storage_type='nfs',
        auth_method='oidc',
        features_required=[]
    )

    result = determine_engagement_model(inputs)
    explanation = explain_engagement_decision(inputs)

    print("\n=== TEST: Self-Sufficient (Alternative Path) ===")
    print(f"K8s Experience: {inputs.k8s_experience}/5")
    print(f"Migration Exp: {inputs.migration_exp} (alternative path)")
    print(f"Swarm %: {inputs.swarm_percent} (<= 20)")
    print(f"Automation: {inputs.automation_level}% (>= 70)")
    print(f"Expected: advisory")
    print(f"Actual: {result.model}")
    print(f"Migration exp check: {explanation['self_sufficient_checks']['migration_exp_ok']}")

    assert result.model == 'advisory', f"Expected 'advisory', got '{result.model}'"
    print("✅ PASSED")
    return True


def run_all_tests():
    """Run all engagement model tests"""
    print("=" * 80)
    print("ENGAGEMENT MODEL VALIDATION TEST SUITE")
    print("=" * 80)

    tests = [
        ("Distributed Chaos - Condition 1", test_distributed_chaos_condition1),
        ("Distributed Chaos - Condition 2", test_distributed_chaos_condition2),
        ("Overwhelmed Organization", test_overwhelmed_organization),
        ("Self-Sufficient Innovator", test_self_sufficient_innovator),
        ("Skilled but Time-Constrained", test_skilled_time_constrained),
        ("Self-Sufficient Alternative", test_alternative_self_sufficient),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR in {name}: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 80)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
