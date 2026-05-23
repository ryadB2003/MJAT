#!/usr/bin/env python3
import requests
import json

# Test data that should trigger all warnings
data = {
    "company_name": "Test Corp",
    "industry": "Technology",
    "company_size": "100-1000",
    "msr_version": "2.9",
    "mke_version": "3.7",
    "num_clusters": 8,
    "num_msr_instances": 2,
    "total_nodes": 50,
    "app_count": 150,
    "swarm_percent": 80,
    "kubernetes_percent": 20,
    "mission_critical_percent": 40,
    "business_critical_percent": 60,
    "platform_team_size": 2,
    "application_teams": 15,
    "k8s_experience": 2,
    "dedicated_team": "partial",
    "migration_exp": "some",
    "automation_level": 50,
    "deploy_frequency": "multiple-daily"
}

response = requests.post("http://localhost:8000/api/assess", json=data)
result = response.json()

print("=" * 60)
print("VALIDATION WARNINGS (should have NO ⚠️ emoji):")
print("=" * 60)
for warning in result.get("validation_warnings", []):
    print(f"  • {warning}")

print("\n" + "=" * 60)
print("RISK FACTORS (should NOT duplicate K8s experience warning):")
print("=" * 60)
for risk in result.get("risk_factors", []):
    print(f"  • {risk}")

print("\n" + "=" * 60)
print("SUMMARY:")
print("=" * 60)
print(f"Total warnings: {len(result.get('validation_warnings', []))}")
print(f"Total risks: {len(result.get('risk_factors', []))}")
print(f"\nMSR warning text check:")
msr_warning = [w for w in result.get('validation_warnings', []) if 'MSR instances' in w]
if msr_warning:
    print(f"  Found: {msr_warning[0]}")
    if 'impacts workload distribution' in msr_warning[0]:
        print("  ✓ Correct: Uses 'impacts workload distribution'")
    else:
        print("  ✗ Wrong: Should say 'impacts workload distribution'")
