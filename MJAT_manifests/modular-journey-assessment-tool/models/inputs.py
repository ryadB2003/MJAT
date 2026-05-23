    """
Input data models with validation using Pydantic.
This ensures all inputs are validated before processing.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field, validator


class AssessmentInputs(BaseModel):
    """
    Complete input data for migration assessment.
    All fields are validated automatically by Pydantic.
    """
    # Company Info
    company_name: str = Field(..., min_length=1)
    industry: str = Field(default="")
    company_size: str = Field(default="")

    # Environment
    msr_version: str = Field(..., pattern=r"^\d+\.\d+$")
    mke_version: str = Field(..., pattern=r"^\d+\.\d+$")
    infra_location: Literal['onprem', 'aws', 'azure', 'gcp', 'hybrid', 'multi'] = Field(default='onprem')
    environments: list[Literal['production', 'staging', 'dev', 'dr']] = Field(default_factory=lambda: ['production'])
    num_mke_instances: int = Field(..., ge=1, le=100)  # MKE/cluster instances to migrate
    num_msr_instances: int = Field(default=1, ge=0, le=100)  # 0 = no MSR
    total_nodes: int = Field(..., ge=1, le=10000)
    app_count: int = Field(..., ge=1, le=10000)
    air_gapped: bool = Field(default=False, description="Environment has no internet access")

    # Workloads
    swarm_percent: int = Field(..., ge=0, le=100)
    kubernetes_percent: int = Field(..., ge=0, le=100)
    mission_critical_percent: int = Field(default=0, ge=0, le=100)
    business_critical_percent: int = Field(default=0, ge=0, le=100)

    # Team & Skills
    platform_team_size: int = Field(..., ge=0, le=1000)
    application_teams: int = Field(default=0, ge=0, le=1000)
    k8s_experience: int = Field(..., ge=1, le=5, description="1=Basic, 5=Expert")
    migration_exp: Literal['none', 'some', 'extensive'] = Field(...)
    dedicated_team: Literal['no', 'partial', 'yes'] = Field(...)
    training_needs_count: int = Field(default=0, ge=0, le=10)

    # Processes
    automation_level: int = Field(..., ge=0, le=100)
    deploy_frequency: Literal['quarterly', 'monthly', 'weekly', 'daily', 'multiple-daily'] = Field(...)

    # Integration
    auth_method: str = Field(default="")
    features_required: list[str] = Field(default_factory=list)

    # MSR Infrastructure Configuration (for MSR 4.0 migration)
    msr4_location: Literal['same-cluster', 'different-cluster', 'external'] = Field(
        default='same-cluster',
        description="Where MSR 4.0 will be deployed relative to MKE cluster"
    )
    network_performance: Literal['same-subnet', 'same-datacenter', 'cross-datacenter', 'cross-region'] = Field(
        default='same-subnet',
        description="Network proximity between MKE cluster and MSR 4.0"
    )
    postgresql_deployment: Literal['in-cluster', 'external-managed', 'external-self-managed'] = Field(
        default='in-cluster',
        description="PostgreSQL deployment method for MSR 4.0"
    )
    redis_deployment: Literal['in-cluster-zalando', 'in-cluster-bitnami', 'external-managed', 'external-self-managed'] = Field(
        default='in-cluster-zalando',
        description="Redis deployment method for MSR 4.0"
    )
    postgresql_storage: Literal['local-ssd', 'nfs', 'cloud-block', 'san'] = Field(
        default='local-ssd',
        description="Storage type for PostgreSQL"
    )
    blob_storage_type: Literal['s3', 'azure-blob', 'gcs', 'nfs', 'local'] = Field(
        default='s3',
        description="Blob storage backend for container images"
    )

    @validator('kubernetes_percent')
    def validate_workload_percentages(cls, v, values):
        """Ensure swarm + kubernetes = 100%"""
        if 'swarm_percent' in values:
            total = values['swarm_percent'] + v
            if total != 100:
                raise ValueError(f"Swarm ({values['swarm_percent']}%) + Kubernetes ({v}%) must equal 100%, got {total}%")
        return v

    @property
    def nodes_per_mke(self) -> float:
        """Calculate average nodes per MKE instance"""
        return self.total_nodes / self.num_mke_instances if self.num_mke_instances > 0 else 0

    @property
    def apps_per_team(self) -> float:
        """Calculate apps per platform team member"""
        return self.app_count / self.platform_team_size if self.platform_team_size > 0 else 999

    @property
    def mke_per_team(self) -> float:
        """Calculate MKE instances per platform team member"""
        return self.num_mke_instances / self.platform_team_size if self.platform_team_size > 0 else 999

    @property
    def msr_per_team(self) -> float:
        """Calculate MSR instances per platform team member"""
        return self.num_msr_instances / self.platform_team_size if self.platform_team_size > 0 else 999

    @property
    def num_environments(self) -> int:
        """Count of environments to migrate"""
        return len(self.environments)

    class Config:
        schema_extra = {
            "example": {
                "company_name": "ACME Corp",
                "industry": "Financial",
                "msr_version": "2.9",
                "mke_version": "3.8",
                "num_mke_instances": 5,
                "num_msr_instances": 2,
                "total_nodes": 200,
                "app_count": 300,
                "swarm_percent": 0,
                "kubernetes_percent": 100,
                "platform_team_size": 10,
                "k8s_experience": 5,
                "migration_exp": "some",
                "dedicated_team": "yes",
                "training_needs_count": 0,
                "automation_level": 80,
                "deploy_frequency": "daily"
            }
        }
