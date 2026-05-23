#!/usr/bin/env python3
"""
Comprehensive API Test Runner for Migration Assessment Tool.

This script executes ALL test scenarios and stores detailed results in JSON format.
Coordinates with the hive mind testing collective through memory storage.
"""
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path
import requests

API_URL = "http://localhost:8000/api/assess"
RESULTS_FILE = Path(__file__).parent / "test_results_comprehensive.json"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def base_input(**overrides) -> Dict[str, Any]:
    """Create a base input with sensible defaults."""
    defaults = {
        "company_name": "Test Corp",
        "msr_version": "2.9",
        "mke_version": "3.8",
        "infra_location": "onprem",
        "environments": ["production"],
        "num_mke_instances": 5,
        "num_msr_instances": 1,
        "total_nodes": 50,
        "app_count": 100,
        "air_gapped": False,
        "swarm_percent": 30,
        "kubernetes_percent": 70,
        "mission_critical_percent": 30,
        "business_critical_percent": 30,
        "platform_team_size": 5,
        "k8s_experience": 3,
        "migration_exp": "some",
        "dedicated_team": "partial",
        "training_needs_count": 2,
        "automation_level": 50,
        "deploy_frequency": "weekly"
    }
    defaults.update(overrides)
    return defaults


def test_api_connectivity() -> bool:
    """Test if API is reachable."""
    try:
        response = requests.get(API_URL.replace("/assess", ""), timeout=5)
        return True
    except Exception as e:
        print(f"{RED}❌ API not reachable: {e}{RESET}")
        return False


def call_api(input_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
    """
    Call the assessment API and return (success, response_data, error_message).
    """
    try:
        response = requests.post(API_URL, json=input_data, timeout=30)
        response.raise_for_status()
        return True, response.json(), ""
    except requests.exceptions.HTTPError as e:
        return False, {}, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, {}, str(e)


class TestRunner:
    """Manages test execution and result collection."""

    def __init__(self):
        self.results = {
            "metadata": {
                "test_run_timestamp": datetime.now().isoformat(),
                "api_url": API_URL,
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "duration_seconds": 0
            },
            "categories": {},
            "failed_tests": []
        }
        self.start_time = time.time()

    def add_category(self, category_name: str):
        """Initialize a new test category."""
        if category_name not in self.results["categories"]:
            self.results["categories"][category_name] = {
                "tests": [],
                "passed": 0,
                "failed": 0
            }

    def add_test_result(self, category: str, test_name: str,
                       input_data: Dict, expected: Dict,
                       passed: bool, actual_result: Dict,
                       validation_message: str):
        """Add a test result to the collection."""
        self.add_category(category)

        test_result = {
            "test_name": test_name,
            "passed": passed,
            "input_data": input_data,
            "expected": expected,
            "actual_result": actual_result,
            "validation_message": validation_message,
            "timestamp": datetime.now().isoformat()
        }

        self.results["categories"][category]["tests"].append(test_result)
        self.results["metadata"]["total_tests"] += 1

        if passed:
            self.results["categories"][category]["passed"] += 1
            self.results["metadata"]["passed"] += 1
        else:
            self.results["categories"][category]["failed"] += 1
            self.results["metadata"]["failed"] += 1
            self.results["failed_tests"].append({
                "category": category,
                "test_name": test_name,
                "reason": validation_message
            })

    def finalize(self):
        """Finalize results and calculate duration."""
        self.results["metadata"]["duration_seconds"] = round(time.time() - self.start_time, 2)

        # Calculate pass rate
        total = self.results["metadata"]["total_tests"]
        passed = self.results["metadata"]["passed"]
        self.results["metadata"]["pass_rate"] = round(100 * passed / total, 2) if total > 0 else 0

    def save_results(self):
        """Save results to JSON file."""
        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n{BLUE}📁 Results saved to: {RESULTS_FILE}{RESET}")

    def print_summary(self):
        """Print test summary to console."""
        metadata = self.results["metadata"]

        print(f"\n{'='*70}")
        print(f"{BLUE}TEST EXECUTION SUMMARY{RESET}")
        print(f"{'='*70}")
        print(f"Total Tests: {metadata['total_tests']}")
        print(f"{GREEN}✅ Passed: {metadata['passed']}{RESET}")
        print(f"{RED}❌ Failed: {metadata['failed']}{RESET}")
        print(f"Pass Rate: {metadata['pass_rate']}%")
        print(f"Duration: {metadata['duration_seconds']}s")

        print(f"\n{BLUE}Category Breakdown:{RESET}")
        for category, data in self.results["categories"].items():
            print(f"  {category}: {data['passed']}/{data['passed'] + data['failed']} passed")

        if self.results["failed_tests"]:
            print(f"\n{RED}Failed Tests:{RESET}")
            for failure in self.results["failed_tests"][:10]:  # Show first 10
                print(f"  • {failure['category']}: {failure['test_name']}")
                print(f"    Reason: {failure['reason']}")


def run_valid_scenarios(runner: TestRunner):
    """Test valid, well-formed scenarios."""
    print(f"\n{BLUE}Running Valid Scenario Tests...{RESET}")

    # ACME Scenario - Expert team
    acme_input = base_input(
        company_name="ACME Corp",
        k8s_experience=5,
        migration_exp="extensive",
        dedicated_team="yes",
        platform_team_size=10,
        training_needs_count=0,
        automation_level=80,
        swarm_percent=0,
        kubernetes_percent=100
    )
    success, result, error = call_api(acme_input)
    passed = success and result.get("engagement_model", {}).get("model") == "advisory"
    runner.add_test_result(
        "valid_scenarios",
        "ACME - Expert Advisory",
        acme_input,
        {"engagement_model": "advisory"},
        passed,
        result,
        "Advisory model expected" if not passed else "PASSED"
    )
    print(f"  {'✅' if passed else '❌'} ACME Scenario")

    # Distributed Chaos - Hybrid infrastructure
    chaos_input = base_input(
        company_name="Chaos Corp",
        infra_location="hybrid",
        k8s_experience=3,
        swarm_percent=50,
        kubernetes_percent=50
    )
    success, result, error = call_api(chaos_input)
    passed = success and result.get("engagement_model", {}).get("model") == "assessment-first"
    runner.add_test_result(
        "valid_scenarios",
        "Distributed Chaos - Hybrid",
        chaos_input,
        {"engagement_model": "assessment-first"},
        passed,
        result,
        "Assessment-first model expected" if not passed else "PASSED"
    )
    print(f"  {'✅' if passed else '❌'} Distributed Chaos")

    # Full Managed - Overwhelmed organization
    overwhelmed_input = base_input(
        company_name="Overwhelmed Corp",
        k8s_experience=1,
        migration_exp="none",
        platform_team_size=2,
        training_needs_count=5,
        automation_level=20,
        swarm_percent=85,
        kubernetes_percent=15
    )
    success, result, error = call_api(overwhelmed_input)
    passed = success and result.get("engagement_model", {}).get("model") == "full"
    runner.add_test_result(
        "valid_scenarios",
        "Full Managed - Overwhelmed",
        overwhelmed_input,
        {"engagement_model": "full"},
        passed,
        result,
        "Full managed model expected" if not passed else "PASSED"
    )
    print(f"  {'✅' if passed else '❌'} Full Managed")

    # Hybrid - Time constrained
    hybrid_input = base_input(
        company_name="Hybrid Corp",
        k8s_experience=3,
        migration_exp="some",
        dedicated_team="partial",
        platform_team_size=6,
        training_needs_count=2,
        automation_level=55,
        swarm_percent=40,
        kubernetes_percent=60
    )
    success, result, error = call_api(hybrid_input)
    passed = success and result.get("engagement_model", {}).get("model") == "hybrid"
    runner.add_test_result(
        "valid_scenarios",
        "Hybrid - Time Constrained",
        hybrid_input,
        {"engagement_model": "hybrid"},
        passed,
        result,
        "Hybrid model expected" if not passed else "PASSED"
    )
    print(f"  {'✅' if passed else '❌'} Hybrid Model")


def run_boundary_tests(runner: TestRunner):
    """Test boundary conditions and edge values."""
    print(f"\n{BLUE}Running Boundary Condition Tests...{RESET}")

    boundaries = [
        # Swarm percentage boundaries
        ("Swarm 0%", {"swarm_percent": 0, "kubernetes_percent": 100}),
        ("Swarm 1%", {"swarm_percent": 1, "kubernetes_percent": 99}),
        ("Swarm 49%", {"swarm_percent": 49, "kubernetes_percent": 51}),
        ("Swarm 50%", {"swarm_percent": 50, "kubernetes_percent": 50}),
        ("Swarm 100%", {"swarm_percent": 100, "kubernetes_percent": 0}),

        # K8s experience boundaries
        ("K8s Exp 1", {"k8s_experience": 1}),
        ("K8s Exp 3", {"k8s_experience": 3}),
        ("K8s Exp 5", {"k8s_experience": 5}),

        # Automation boundaries
        ("Automation 0%", {"automation_level": 0}),
        ("Automation 50%", {"automation_level": 50}),
        ("Automation 100%", {"automation_level": 100}),

        # Team size boundaries
        ("Team 1", {"platform_team_size": 1}),
        ("Team 2", {"platform_team_size": 2}),
        ("Team 6", {"platform_team_size": 6}),
        ("Team 20", {"platform_team_size": 20}),
    ]

    for test_name, overrides in boundaries:
        input_data = base_input(**overrides)
        success, result, error = call_api(input_data)
        passed = success and "engagement_model" in result and "complexity_score" in result

        runner.add_test_result(
            "boundary_conditions",
            test_name,
            input_data,
            {"has_valid_response": True},
            passed,
            result,
            error if not passed else "Valid response received"
        )
        print(f"  {'✅' if passed else '❌'} {test_name}")


def run_invalid_input_tests(runner: TestRunner):
    """Test invalid inputs and error handling."""
    print(f"\n{BLUE}Running Invalid Input Tests...{RESET}")

    invalid_cases = [
        # Negative values
        ("Negative Swarm%", {"swarm_percent": -10, "kubernetes_percent": 110}),
        ("Negative Team Size", {"platform_team_size": -5}),
        ("Negative Apps", {"app_count": -100}),

        # Out of range values
        ("Swarm > 100%", {"swarm_percent": 150, "kubernetes_percent": -50}),
        ("K8s Exp > 5", {"k8s_experience": 10}),
        ("Automation > 100%", {"automation_level": 150}),

        # Invalid percentages (don't sum to 100)
        ("Invalid Swarm+K8s", {"swarm_percent": 40, "kubernetes_percent": 40}),

        # Zero critical values
        ("Zero MKE", {"num_mke_instances": 0}),
        ("Zero Nodes", {"total_nodes": 0}),
    ]

    for test_name, overrides in invalid_cases:
        input_data = base_input(**overrides)
        success, result, error = call_api(input_data)

        # For invalid inputs, we expect either 422 error or validation error in response
        passed = not success or (success and "error" in result)

        runner.add_test_result(
            "invalid_inputs",
            test_name,
            input_data,
            {"should_error": True},
            passed,
            result if success else {"error": error},
            "Properly rejected invalid input" if passed else "Should have rejected invalid input"
        )
        print(f"  {'✅' if passed else '❌'} {test_name}")


def run_response_validation_tests(runner: TestRunner):
    """Validate response structure and data types."""
    print(f"\n{BLUE}Running Response Validation Tests...{RESET}")

    test_input = base_input(company_name="Validation Test Corp")
    success, result, error = call_api(test_input)

    if not success:
        print(f"  {RED}❌ Failed to get API response{RESET}")
        return

    # Check required fields
    required_fields = {
        "engagement_model": dict,
        "complexity_score": (int, float),
        "complexity_level": str,
        "readiness_score": (int, float),
        "readiness_level": str,
        "timeline": dict,
        "considerations": list
    }

    for field, expected_type in required_fields.items():
        has_field = field in result

        if has_field:
            actual_value = result[field]
            if isinstance(expected_type, tuple):
                correct_type = isinstance(actual_value, expected_type)
            else:
                correct_type = isinstance(actual_value, expected_type)
        else:
            correct_type = False

        passed = has_field and correct_type

        runner.add_test_result(
            "response_validation",
            f"Field '{field}' type check",
            test_input,
            {"field": field, "expected_type": str(expected_type)},
            passed,
            {"has_field": has_field, "value": result.get(field, "MISSING")},
            f"Field present and correct type" if passed else f"Field missing or wrong type"
        )
        print(f"  {'✅' if passed else '❌'} {field}: {expected_type}")

    # Check engagement model structure
    if "engagement_model" in result:
        em_fields = ["model", "name", "ps_effort_percent", "duration_multiplier"]
        em = result["engagement_model"]

        for field in em_fields:
            passed = field in em
            runner.add_test_result(
                "response_validation",
                f"Engagement model field '{field}'",
                test_input,
                {"field": field},
                passed,
                {"value": em.get(field, "MISSING")},
                "Field present" if passed else "Field missing"
            )
            print(f"  {'✅' if passed else '❌'} engagement_model.{field}")


def main():
    """Main test execution."""
    print(f"{BLUE}{'='*70}")
    print("COMPREHENSIVE API TEST EXECUTION")
    print(f"{'='*70}{RESET}")
    print(f"API URL: {API_URL}")
    print(f"Results File: {RESULTS_FILE}")

    # Check API connectivity
    if not test_api_connectivity():
        print(f"\n{RED}❌ Cannot connect to API. Make sure it's running:{RESET}")
        print(f"   cd /Users/moustaphagueye/Modular_assessment/python-assessment")
        print(f"   uvicorn api:app --reload")
        return 1

    print(f"{GREEN}✅ API is reachable{RESET}")

    # Initialize test runner
    runner = TestRunner()

    # Execute test suites
    run_valid_scenarios(runner)
    run_boundary_tests(runner)
    run_invalid_input_tests(runner)
    run_response_validation_tests(runner)

    # Finalize and save
    runner.finalize()
    runner.save_results()
    runner.print_summary()

    # Return exit code based on pass/fail
    return 0 if runner.results["metadata"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
