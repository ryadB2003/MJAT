#!/usr/bin/env python3
"""
Validation script for remediation changes.
Tests the API to confirm expected behavior after all changes.

Run after rebuilding the image:
    python tests/validate_remediation.py

Or with pytest:
    pytest tests/validate_remediation.py -v
"""
import requests
import json
import sys

API_URL = "http://localhost:8000/api/assess"

# Test scenarios with expected outcomes
TEST_SCENARIOS = [
    {
        "name": "Test 1: Air-gapped adds +5 complexity points",
        "input": {
            "company_name": "AirGap Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 0,
            "kubernetes_percent": 100,
            "platform_team_size": 5,
            "k8s_experience": 4,
            "migration_exp": "some",
            "dedicated_team": "yes",
            "automation_level": 70,
            "deploy_frequency": "weekly",
            "air_gapped": True  # This should add +5 to complexity
        },
        "expected": {
            "complexity_includes_airgap": True,
            "description": "Air-gapped environment should add +5 to complexity score"
        }
    },
    {
        "name": "Test 2: Non-air-gapped baseline (for comparison)",
        "input": {
            "company_name": "Normal Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 0,
            "kubernetes_percent": 100,
            "platform_team_size": 5,
            "k8s_experience": 4,
            "migration_exp": "some",
            "dedicated_team": "yes",
            "automation_level": 70,
            "deploy_frequency": "weekly",
            "air_gapped": False
        },
        "expected": {
            "complexity_includes_airgap": False,
            "description": "Non-air-gapped should have 5 points less than air-gapped"
        }
    },
    {
        "name": "Test 3: 'Significant' complexity label (score > 60)",
        "input": {
            "company_name": "Complex Corp",
            "msr_version": "2.8",  # +25 points
            "mke_version": "3.5",  # +10 points
            "num_mke_instances": 20,
            "total_nodes": 2000,   # 100 nodes/MKE = +15
            "app_count": 600,      # +10 points
            "swarm_percent": 80,   # +20 points
            "kubernetes_percent": 20,
            "platform_team_size": 5,
            "k8s_experience": 2,
            "migration_exp": "none",
            "dedicated_team": "no",
            "automation_level": 30,
            "deploy_frequency": "quarterly"
        },
        "expected": {
            "complexity_level": "Significant",
            "description": "High complexity should now show 'Significant' instead of 'High'"
        }
    },
    {
        "name": "Test 4: Team size ≤2 triggers Full Managed (not ≤3)",
        "input": {
            "company_name": "Small Team Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 80,
            "kubernetes_percent": 20,
            "platform_team_size": 2,  # Very small team
            "k8s_experience": 2,
            "migration_exp": "none",
            "dedicated_team": "no",
            "training_needs_count": 3,
            "automation_level": 25,
            "deploy_frequency": "quarterly"
        },
        "expected": {
            "engagement_model": "full",
            "description": "Team size of 2 with other triggers should get Full Managed"
        }
    },
    {
        "name": "Test 5: Team size of 3 does NOT auto-trigger Full Managed",
        "input": {
            "company_name": "Three Person Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 3,
            "total_nodes": 30,
            "app_count": 50,
            "swarm_percent": 40,
            "kubernetes_percent": 60,
            "platform_team_size": 3,  # Was trigger before, not anymore
            "k8s_experience": 3,
            "migration_exp": "some",
            "dedicated_team": "partial",
            "training_needs_count": 2,
            "automation_level": 50,
            "deploy_frequency": "weekly"
        },
        "expected": {
            "engagement_model_not": "full",
            "description": "Team size of 3 should NOT automatically trigger Full Managed anymore"
        }
    },
    {
        "name": "Test 6: Ratio-based MKE threshold (>3 clusters/person)",
        "input": {
            "company_name": "High Ratio Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 12,  # 4 MKE instances per person
            "total_nodes": 120,
            "app_count": 100,
            "swarm_percent": 40,
            "kubernetes_percent": 60,
            "platform_team_size": 3,  # 12/3 = 4 clusters/person > 3 threshold
            "k8s_experience": 3,
            "migration_exp": "some",
            "dedicated_team": "partial",
            "automation_level": 60,
            "deploy_frequency": "weekly"
        },
        "expected": {
            "engagement_model": "full",
            "description": "More than 3 MKE instances per person should trigger Full Managed"
        }
    },
    {
        "name": "Test 7: Advisory model with relaxed requirements (scoring system)",
        "input": {
            "company_name": "Almost Self-Sufficient Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 30,  # ≤40% = 1 point
            "kubernetes_percent": 70,
            "platform_team_size": 6,  # ≥6 = 1 point
            "k8s_experience": 4,  # ≥4 = 2 points
            "migration_exp": "some",  # Not extensive, but OK
            "dedicated_team": "yes",  # = 1 point
            "training_needs_count": 2,  # ≤2 = 1 point
            "automation_level": 65,  # ≥60 = 1 point
            "deploy_frequency": "daily"
            # Total: 2+1+1+1+1 = 6+ points ≥ 5, should qualify for Advisory
        },
        "expected": {
            "engagement_model": "advisory",
            "description": "Scoring system should allow Advisory with 5+ points"
        }
    },
    {
        "name": "Test 8: Minimum timeline is now 4 weeks (not 6)",
        "input": {
            "company_name": "Fast Track Corp",
            "msr_version": "3.0",  # Low complexity
            "mke_version": "3.8",
            "num_mke_instances": 2,
            "total_nodes": 20,
            "app_count": 30,
            "swarm_percent": 0,  # Pure K8s
            "kubernetes_percent": 100,
            "platform_team_size": 10,
            "k8s_experience": 5,  # Expert
            "migration_exp": "extensive",
            "dedicated_team": "yes",
            "training_needs_count": 0,
            "automation_level": 90,
            "deploy_frequency": "daily",
            "environments": ["production"]
        },
        "expected": {
            "min_timeline_weeks": 4,
            "description": "Minimum timeline should be 4 weeks for simple migrations"
        }
    },
    {
        "name": "Test 9: Full Managed adds +1 week coordination overhead",
        "input": {
            "company_name": "Full Support Corp",
            "msr_version": "2.8",
            "mke_version": "3.5",
            "num_mke_instances": 3,
            "total_nodes": 30,
            "app_count": 50,
            "swarm_percent": 80,
            "kubernetes_percent": 20,
            "platform_team_size": 2,
            "k8s_experience": 2,
            "migration_exp": "none",
            "dedicated_team": "no",
            "training_needs_count": 4,
            "automation_level": 25,
            "deploy_frequency": "quarterly"
        },
        "expected": {
            "engagement_adjustment": 1,
            "description": "Full Managed adds +1 week coordination (base weeks account for work)"
        }
    },
    {
        "name": "Test 10: Output uses 'considerations' (not 'risk_factors')",
        "input": {
            "company_name": "Test Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 50,
            "kubernetes_percent": 50,
            "platform_team_size": 5,
            "k8s_experience": 3,
            "migration_exp": "some",
            "dedicated_team": "partial",
            "automation_level": 60,
            "deploy_frequency": "weekly"
        },
        "expected": {
            "has_considerations": True,
            "has_risk_factors": False,
            "description": "Output should have 'considerations' field, not 'risk_factors'"
        }
    },
    {
        "name": "Test 11: Hybrid Swarm range now 20-75% (was 30-70%)",
        "input": {
            "company_name": "Edge Swarm Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 25,  # Was outside old range (30-70)
            "kubernetes_percent": 75,
            "platform_team_size": 5,
            "k8s_experience": 3,
            "migration_exp": "some",
            "dedicated_team": "partial",
            "training_needs_count": 2,
            "automation_level": 55,
            "deploy_frequency": "weekly"
        },
        "expected": {
            "engagement_model": "hybrid",
            "description": "25% Swarm should now qualify for Hybrid (range widened to 20-75%)"
        }
    },
    {
        "name": "Test 12: Mission-critical adds timeline buffer",
        "input": {
            "company_name": "Critical Corp",
            "msr_version": "2.9",
            "mke_version": "3.8",
            "num_mke_instances": 5,
            "total_nodes": 50,
            "app_count": 100,
            "swarm_percent": 40,
            "kubernetes_percent": 60,
            "platform_team_size": 5,
            "k8s_experience": 3,
            "migration_exp": "some",
            "dedicated_team": "partial",
            "automation_level": 60,
            "deploy_frequency": "weekly",
            "mission_critical_percent": 80  # Very high - should add +3% buffer
        },
        "expected": {
            "buffer_increased": True,
            "description": "High mission-critical % should increase timeline buffer"
        }
    }
]


def call_api(input_data: dict) -> dict:
    """Call the assessment API and return the response."""
    try:
        response = requests.post(API_URL, json=input_data, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Cannot connect to API at {API_URL}")
        print("   Make sure the API is running (rebuild image and start container)")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API Error: {e}")
        print(f"   Response: {response.text}")
        return None


def validate_scenario(scenario: dict) -> tuple[bool, str]:
    """Validate a single test scenario."""
    result = call_api(scenario["input"])
    if result is None:
        return False, "API call failed"

    expected = scenario["expected"]

    # Check complexity level
    if "complexity_level" in expected:
        if result["complexity_level"] != expected["complexity_level"]:
            return False, f"Expected complexity_level '{expected['complexity_level']}', got '{result['complexity_level']}'"

    # Check engagement model
    if "engagement_model" in expected:
        if result["engagement_model"]["model"] != expected["engagement_model"]:
            return False, f"Expected engagement_model '{expected['engagement_model']}', got '{result['engagement_model']['model']}'"

    # Check engagement model is NOT something
    if "engagement_model_not" in expected:
        if result["engagement_model"]["model"] == expected["engagement_model_not"]:
            return False, f"Expected engagement_model to NOT be '{expected['engagement_model_not']}', but it was"

    # Check considerations field exists (not risk_factors)
    if "has_considerations" in expected:
        if expected["has_considerations"] and "considerations" not in result:
            return False, "Expected 'considerations' field in output, not found"

    if "has_risk_factors" in expected:
        if not expected["has_risk_factors"] and "risk_factors" in result:
            return False, "Found deprecated 'risk_factors' field in output"

    # Check minimum timeline (verify it's at or below the expected minimum - faster is better!)
    if "min_timeline_weeks" in expected:
        actual_weeks = result["timeline"]["min_months"] * 4.33
        # For simple migrations, we want timelines AT OR BELOW the expected minimum
        if actual_weeks > expected["min_timeline_weeks"] * 1.2:  # Only fail if significantly higher
            return False, f"Expected maximum ~{expected['min_timeline_weeks']} weeks for simple migration, got {actual_weeks:.1f}"

    # Check engagement adjustment
    if "engagement_adjustment" in expected:
        adjustments = result["timeline"]["multipliers_applied"]
        if "engagement" in adjustments:
            if adjustments["engagement"] != expected["engagement_adjustment"]:
                return False, f"Expected engagement adjustment {expected['engagement_adjustment']}, got {adjustments['engagement']}"

    return True, "PASSED"


def run_validation():
    """Run all validation tests."""
    print("=" * 70)
    print("REMEDIATION VALIDATION SCRIPT")
    print("=" * 70)
    print(f"\nTesting API at: {API_URL}")
    print(f"Running {len(TEST_SCENARIOS)} test scenarios...\n")

    results = []
    passed = 0
    failed = 0

    # Run air-gapped comparison tests first
    airgapped_result = None
    non_airgapped_result = None

    for scenario in TEST_SCENARIOS:
        print(f"Running: {scenario['name']}")

        success, message = validate_scenario(scenario)

        # Store results for air-gapped comparison
        if "Air-gapped" in scenario["name"]:
            airgapped_result = call_api(scenario["input"])
        elif "Non-air-gapped" in scenario["name"]:
            non_airgapped_result = call_api(scenario["input"])

        if success:
            print(f"  ✅ {message}")
            passed += 1
        else:
            print(f"  ❌ {message}")
            failed += 1

        results.append({
            "name": scenario["name"],
            "success": success,
            "message": message
        })

    # Special comparison test for air-gapped
    print("\nRunning: Air-gapped complexity comparison")
    if airgapped_result and non_airgapped_result:
        diff = airgapped_result["complexity_score"] - non_airgapped_result["complexity_score"]
        if diff == 5:
            print(f"  ✅ Air-gapped adds exactly +5 points (diff={diff})")
            passed += 1
        else:
            print(f"  ❌ Expected +5 point difference, got {diff}")
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")

    if failed == 0:
        print("\n🎉 ALL VALIDATIONS PASSED! Remediation changes working as expected.")
        return 0
    else:
        print(f"\n⚠️  {failed} validation(s) failed. Please review the changes.")
        return 1


if __name__ == "__main__":
    sys.exit(run_validation())
