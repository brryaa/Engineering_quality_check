# Work Package 5: Database Architecture Upgrade & Concurrency Control

## 1. Overview
The database layer of the Engineering Quality Lab (EQL) platform was upgraded to support dual SQLite & PostgreSQL operation with robust transaction semantics, automated schema migrations, and optimistic locking concurrency control.

## 2. Key Architecture Upgrades

### 2.1 Dual-Engine Dialect Adapter (`backend/app/core/database.py`)
- **PostgreSQL**: Implemented connection pool (`pool_size=20`, `max_overflow=10`, `pool_recycle=1800`), automatic dead-connection pinging (`pool_pre_ping=True`), and standard `READ COMMITTED` isolation level.
- **SQLite**: Enforced WAL mode (`PRAGMA journal_mode=WAL`), normalized synchronous writes (`PRAGMA synchronous=NORMAL`), and mandatory foreign key checks (`PRAGMA foreign_keys=ON`) via connection hooks.

### 2.2 Alembic Migration System (`backend/alembic/`)
- Initialized Alembic migration environment with automatic model detection (`Base.metadata`).
- Enabled SQLite `render_as_batch=True` to support table alteration and constraint modifications in SQLite.
- Created and executed migration `18c0559dd831_initial_schema_with_optimistic_locking.py` adding `version_id` column to `issues` and `changes` tables with server default `1`.
- Verified round-trip migration (`alembic downgrade base` -> `alembic upgrade head`).

### 2.3 Optimistic Concurrency Control (OCC)
- Added `version_id = Column(Integer, default=1, nullable=False)` to `EngineeringIssue` and `EngineeringChange`.
- Configured SQLAlchemy `__mapper_args__ = {"version_id_col": version_id}`.
- Concurrency conflicts automatically trigger `sqlalchemy.orm.exc.StaleDataError`, preventing lost updates when multiple quality managers or engineers edit the same defect or ECR concurrently.

### 2.4 Data Migration CLI Tool (`backend/scripts/migrate_database.py`)
- Supports streaming batch migration between SQLite and PostgreSQL instances.
- Respects topological foreign key dependencies:
  `Program` -> `Part` -> `DFMEA` -> `DVPR` -> `TestRun` -> `EngineeringIssue` -> `RootCauseAnalysis` -> `EngineeringChange` -> `KnowledgeItem`.
- Empirically verified: Successfully migrated 3,471 records across all 9 tables with zero data loss.

### 2.5 Automated Verification
- `test_sqlite_foreign_key_integrity`: Verified that invalid foreign keys are rejected with `IntegrityError`.
- `test_optimistic_locking_issue_conflict`: Verified that stale updates to issues trigger `StaleDataError`.
- `test_optimistic_locking_change_conflict`: Verified that stale updates to engineering changes trigger `StaleDataError`.
- `test_transaction_rollback_atomic_guarantee`: Verified that partial multi-entity insert failures roll back atomically.
