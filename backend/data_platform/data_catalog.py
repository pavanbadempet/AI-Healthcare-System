"""
Unity-Style Data Catalog & Governance — Clinical Data Discovery & Access Control.

Provides:
- Hierarchical namespace: Catalog → Schema → Table/Model/Function
- Column-level metadata, tags, and descriptions
- Row-level & column-level access policies
- Data classification (PII, PHI, public)
- Search and discovery across all registered assets
"""

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    PHI = "PHI"
    PII = "PII"


class AssetType(str, Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    MODEL = "MODEL"
    FUNCTION = "FUNCTION"
    NOTEBOOK = "NOTEBOOK"
    PIPELINE = "PIPELINE"
    FEATURE = "FEATURE"


class ColumnMetadata(BaseModel):
    """Metadata for a single column."""
    name: str
    data_type: str
    description: str = ""
    classification: DataClassification = DataClassification.INTERNAL
    tags: List[str] = Field(default_factory=list)
    is_nullable: bool = True


class CatalogAsset(BaseModel):
    """A registered data asset in the catalog."""
    asset_id: str = Field(default_factory=lambda: f"ASSET-{uuid.uuid4().hex[:8]}")
    catalog: str
    schema_name: str
    name: str
    asset_type: AssetType
    description: str = ""
    owner: str = ""
    classification: DataClassification = DataClassification.INTERNAL
    columns: List[ColumnMetadata] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    @property
    def fully_qualified_name(self) -> str:
        """Return three-level namespace: catalog.schema.name."""
        return f"{self.catalog}.{self.schema_name}.{self.name}"


class AccessPolicy(BaseModel):
    """Row/column-level access policy."""
    policy_id: str = Field(default_factory=lambda: f"POL-{uuid.uuid4().hex[:6]}")
    asset_fqn: str
    principal: str  # user or role
    allowed_columns: Optional[List[str]] = None  # None = all columns
    row_filter: Optional[str] = None  # SQL predicate
    grant_type: str = "SELECT"


class UnityDataCatalog:
    """
    Databricks Unity Catalog-style metadata store.

    Three-level namespace (catalog.schema.table) with column-level
    governance, data classification, and search.
    """

    def __init__(self) -> None:
        self._assets: Dict[str, CatalogAsset] = {}
        self._policies: List[AccessPolicy] = []

    def register_asset(self, asset: CatalogAsset) -> CatalogAsset:
        """Register a data asset."""
        fqn = asset.fully_qualified_name
        self._assets[fqn] = asset
        return asset

    def get_asset(self, catalog: str, schema: str, name: str) -> Optional[CatalogAsset]:
        """Look up an asset by three-level name."""
        fqn = f"{catalog}.{schema}.{name}"
        return self._assets.get(fqn)

    def search(self, query: str, asset_type: Optional[AssetType] = None) -> List[CatalogAsset]:
        """Search assets by name, description, or tags."""
        q = query.lower()
        results: List[CatalogAsset] = []
        for asset in self._assets.values():
            if asset_type and asset.asset_type != asset_type:
                continue
            searchable = f"{asset.name} {asset.description} {' '.join(asset.tags)}".lower()
            if q in searchable:
                results.append(asset)
        return results

    def add_policy(self, policy: AccessPolicy) -> AccessPolicy:
        """Add an access control policy."""
        self._policies.append(policy)
        return policy

    def check_access(self, asset_fqn: str, principal: str, column: Optional[str] = None) -> bool:
        """Check whether a principal can access an asset (and optionally a column)."""
        matching = [p for p in self._policies if p.asset_fqn == asset_fqn and p.principal == principal]
        if not matching:
            return False
        if column is None:
            return True
        for policy in matching:
            if policy.allowed_columns is None or column in policy.allowed_columns:
                return True
        return False

    def list_catalogs(self) -> List[str]:
        """List distinct catalog names."""
        return list({a.catalog for a in self._assets.values()})

    def list_schemas(self, catalog: str) -> List[str]:
        """List schemas within a catalog."""
        return list({a.schema_name for a in self._assets.values() if a.catalog == catalog})

    def list_assets(self, catalog: str, schema: str) -> List[CatalogAsset]:
        """List all assets within a catalog.schema."""
        return [a for a in self._assets.values() if a.catalog == catalog and a.schema_name == schema]

    @property
    def total_assets(self) -> int:
        """Return total registered assets."""
        return len(self._assets)


unity_data_catalog = UnityDataCatalog()
