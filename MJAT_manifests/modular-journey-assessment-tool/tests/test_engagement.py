"""
Unit tests for engagement model determination.
This is what makes the Python approach so much better - easy testing!
"""
import pytest
from models.inputs import AssessmentInputs
from logic.engagement import (
    determine_engagement_model,
    explain_engagement_decision,
    _is_distributed_chaos,
    _is_self_sufficient,
    _is_overwhelmed_org,
    _is_time_constrained
)


def test_acme_scenario():
    """
    Test the ACME scenario that was failing in JavaScript.

    ACME Profile:
    - Expert K8s team (5/5)
    - 10 MKE instances, 200 nodes (20 per MKE)
    - 300 apps, 10 team members
    - 0% Swarm, 100% Kubernetes
    - 80% automation, daily deployments
    - Dedicated full-time team
    - Some migration experience

    Expected Result: Advisory (Self-Sufficient Innovator)
    """
    acme = AssessmentInputs(
        company_name="ACME Corp",
        industry="Financial",
        msr_version="2.9",
        mke_version="3.8",
        num_mke_instances=10,
        num_msr_instances=1,
        total_nodes=200,
        app_count=300,
        swarm_percent=0,
        kubernetes_percent=100,
        platform_team_size=10,
        application_teams=30,
        k8s_experience=5,
        migration_exp='some',
        dedicated_team='yes',
        training_needs_count=0,
        automation_level=80,
        deploy_frequency='daily'
    )

    # Should NOT trigger Distributed Chaos
    assert not _is_distributed_chaos(acme), "ACME should not be Distributed Chaos"

    # Should be Self-Sufficient
    assert _is_self_sufficient(acme), "ACME should be Self-Sufficient Innovator"

    # Final result should be advisory
    result = determine_engagement_model(acme)
    assert result.model == 'advisory', f"Expected 'advisory', got '{result.model}'"
    assert result.name == 'Enablement & Advisory'
    # PS effort scales with app count: 300 apps = 1.15x multiplier
    # Base 27.5% * 1.15 = 31.625 ≈ 31.6%
    assert 30.0 <= result.ps_effort_percent <= 35.0, f"Expected PS effort 30-35% for 300 apps, got {result.ps_effort_percent}%"

    print("✅ ACME test PASSED!")
    print(f"   Model: {result.model}")
    print(f"   Name: {result.name}")
    print(f"   PS Effort: {result.ps_effort_percent}% (scaled for {acme.app_count} apps)")


def test_acme_detailed_breakdown():
    """Show detailed breakdown of why ACME qualifies for Advisory"""
    acme = AssessmentInputs(
        company_name="ACME Corp",
        industry="Financial",
        msr_version="2.9",
        mke_version="3.8",
        num_mke_instances=10,
        num_msr_instances=1,
        total_nodes=200,
        app_count=300,
        swarm_percent=0,
        kubernetes_percent=100,
        platform_team_size=10,
        application_teams=30,
        k8s_experience=5,
        migration_exp='some',
        dedicated_team='yes',
        training_needs_count=0,
        automation_level=80,
        deploy_frequency='daily'
    )

    explanation = explain_engagement_decision(acme)

    print("\n" + "="*60)
    print("ACME ENGAGEMENT MODEL DECISION BREAKDOWN")
    print("="*60)

    print("\n📊 Input Values:")
    print(f"   MKE Instances: {acme.num_mke_instances}")
    print(f"   Team Size: {acme.platform_team_size}")
    print(f"   MKE per Team: {acme.mke_per_team:.2f}")
    print(f"   Apps per Team: {acme.apps_per_team:.2f}")
    print(f"   K8s Experience: {acme.k8s_experience}/5")
    print(f"   Migration Exp: {acme.migration_exp}")
    print(f"   Swarm %: {acme.swarm_percent}%")
    print(f"   Automation: {acme.automation_level}%")

    print("\n⚠️  Assessment-First Checks:")
    for key, value in explanation['assessment_first_checks'].items():
        status = "❌ FAIL" if "True" in str(value) and key.startswith('condition') else "✅ PASS"
        print(f"   {status} {key}: {value}")

    print("\n✅ Self-Sufficient Checks:")
    for key, value in explanation['self_sufficient_checks'].items():
        if key == 'is_self_sufficient':
            status = "✅ PASS" if value else "❌ FAIL"
            print(f"   {status} FINAL: {value}")
        else:
            status = "✅" if "True" in str(value) or value is True else "❌"
            print(f"   {status} {key}: {value}")

    print(f"\n🎯 Final Model: {explanation['final_model']}")
    print("="*60)

    assert explanation['final_model'] == 'advisory'


def test_distributed_chaos_triggers():
    """Test conditions that should trigger Distributed Chaos (Assessment-First)"""

    # Condition: Hybrid infrastructure triggers assessment-first
    chaos1 = AssessmentInputs(
        company_name="Chaos1",
        msr_version="2.9",
        mke_version="3.8",
        infra_location='hybrid',  # Hybrid triggers assessment-first
        num_mke_instances=20,
        total_nodes=100,
        app_count=100,
        swarm_percent=0,
        kubernetes_percent=100,
        platform_team_size=5,
        k8s_experience=3,
        migration_exp='some',
        dedicated_team='yes',
        automation_level=70,
        deploy_frequency='daily'
    )
    assert _is_distributed_chaos(chaos1), "Should trigger on hybrid infrastructure"

    # Condition: Multi-cloud triggers assessment-first
    chaos4 = AssessmentInputs(
        company_name="Chaos4",
        msr_version="2.9",
        mke_version="3.8",
        infra_location='multi',  # Multi-cloud triggers assessment-first
        num_mke_instances=12,
        total_nodes=100,
        app_count=100,
        swarm_percent=60,
        kubernetes_percent=40,
        platform_team_size=10,
        k8s_experience=2,
        migration_exp='none',
        dedicated_team='partial',
        automation_level=40,
        deploy_frequency='monthly'
    )
    assert _is_distributed_chaos(chaos4), "Should trigger on multi-cloud infrastructure"


def test_overwhelmed_org():
    """Test Overwhelmed Organization pattern"""
    overwhelmed = AssessmentInputs(
        company_name="Overwhelmed",
        msr_version="2.9",
        mke_version="3.5",
        num_mke_instances=3,
        total_nodes=20,
        app_count=50,
        swarm_percent=80,  # Heavy Swarm
        kubernetes_percent=20,
        platform_team_size=2,  # Very small team
        k8s_experience=1,  # Minimal K8s
        migration_exp='none',  # No experience
        dedicated_team='no',  # Can't dedicate
        training_needs_count=5,  # Extensive training needed
        automation_level=20,  # Low automation
        deploy_frequency='quarterly'
    )

    assert _is_overwhelmed_org(overwhelmed)
    result = determine_engagement_model(overwhelmed)
    assert result.model == 'full'


def test_hybrid_default():
    """Test that reasonable middle-ground scenarios get Hybrid"""
    hybrid = AssessmentInputs(
        company_name="Hybrid",
        msr_version="2.9",
        mke_version="3.7",
        num_mke_instances=5,
        total_nodes=80,
        app_count=150,
        swarm_percent=40,
        kubernetes_percent=60,
        platform_team_size=6,
        k8s_experience=3,
        migration_exp='some',
        dedicated_team='partial',
        training_needs_count=2,
        automation_level=60,
        deploy_frequency='weekly'
    )

    result = determine_engagement_model(hybrid)
    assert result.model == 'hybrid'


if __name__ == "__main__":
    print("Running ACME engagement model tests...\n")

    # Run main ACME test
    test_acme_scenario()

    # Show detailed breakdown
    test_acme_detailed_breakdown()

    # Run other tests
    print("\n" + "="*60)
    print("Running additional test cases...")
    print("="*60 + "\n")

    test_distributed_chaos_triggers()
    print("✅ Distributed Chaos tests passed")

    test_overwhelmed_org()
    print("✅ Overwhelmed Organization tests passed")

    test_hybrid_default()
    print("✅ Hybrid default tests passed")

    print("\n" + "="*60)
    print("ALL TESTS PASSED! ✅")
    print("="*60)
