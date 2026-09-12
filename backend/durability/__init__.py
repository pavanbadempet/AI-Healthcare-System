"""Level 11: Autonomous Continuous Durability & Zero-Data-Loss Disaster Recovery OS.

Provides continuous streaming WAL delta journaling, microsecond Point-In-Time
Recovery (PITR), autonomous ephemeral restore verification, air-gapped ransomware-proof
WORM immutability, and multi-region quorum consensus failover.
"""

from backend.durability.continuous_wal_archiver import (
    ContinuousWalArchiver,
    WalRecord,
)
from backend.durability.multi_region_failover import (
    MultiRegionFailoverCoordinator,
    ReplicationNode,
)
from backend.durability.restore_verifier import (
    AutonomousRestoreVerifier,
    ProofOfRecoverability,
)
from backend.durability.worm_immutability_shield import (
    WormImmutabilityShield,
    WormSnapshotManifest,
)

__all__ = [
    "ContinuousWalArchiver",
    "WalRecord",
    "AutonomousRestoreVerifier",
    "ProofOfRecoverability",
    "WormImmutabilityShield",
    "WormSnapshotManifest",
    "MultiRegionFailoverCoordinator",
    "ReplicationNode",
]
