#!/usr/bin/env python3
"""
Database Migration & Transfer Tool
Transfers data between SQLite and PostgreSQL, maintaining foreign key integrity,
optimistic locking version_ids, and schema mapping.
"""
import sys
import os
import argparse
from sqlalchemy import create_engine, select, text, inspect
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base
from app.models.models import (
    Program, Part, DFMEA, DVPR, TestRun,
    EngineeringIssue, RootCauseAnalysis, EngineeringChange, KnowledgeItem
)

TABLE_ORDER = [
    Program,
    Part,
    DFMEA,
    DVPR,
    TestRun,
    EngineeringIssue,
    RootCauseAnalysis,
    EngineeringChange,
    KnowledgeItem
]


def migrate_database(source_url: str, target_url: str, batch_size: int = 500):
    print(f"[*] Starting migration:")
    print(f"    Source: {source_url}")
    print(f"    Target: {target_url}")

    src_engine = create_engine(source_url, connect_args={"check_same_thread": False} if "sqlite" in source_url else {})
    tgt_engine = create_engine(target_url, connect_args={"check_same_thread": False} if "sqlite" in target_url else {})

    # Create tables in target if not exist
    print("[*] Ensuring target schema is created...")
    Base.metadata.create_all(bind=tgt_engine)

    SrcSession = sessionmaker(bind=src_engine)
    TgtSession = sessionmaker(bind=tgt_engine)

    src_db = SrcSession()
    tgt_db = TgtSession()

    try:
        total_migrated = 0
        summary = {}

        for model in TABLE_ORDER:
            table_name = model.__tablename__
            src_count = src_db.query(model).count()
            print(f"  -> Migrating {table_name} ({src_count} records)...")

            offset = 0
            model_migrated = 0
            while offset < src_count:
                records = src_db.query(model).offset(offset).limit(batch_size).all()
                if not records:
                    break

                for r in records:
                    # Extract attributes
                    attrs = {col.name: getattr(r, col.name) for col in model.__table__.columns}
                    # Merge or insert into target
                    tgt_db.merge(model(**attrs))

                tgt_db.commit()
                model_migrated += len(records)
                offset += batch_size

            tgt_count = tgt_db.query(model).count()
            summary[table_name] = {"source": src_count, "target": tgt_count}
            assert tgt_count >= src_count, f"Data count mismatch for {table_name}: src={src_count}, tgt={tgt_count}"
            total_migrated += model_migrated

        print(f"\n[+] Migration completed successfully! Total records transferred: {total_migrated}")
        print("--- Verification Matrix ---")
        for tbl, counts in summary.items():
            print(f"  {tbl:<20}: Source={counts['source']:<6} Target={counts['target']:<6} [OK]")

    except Exception as e:
        tgt_db.rollback()
        print(f"[-] Migration failed: {e}", file=sys.stderr)
        raise
    finally:
        src_db.close()
        tgt_db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EQL Data Migration Tool")
    parser.add_argument("--source", default="sqlite:///./backend/eql_platform.db", help="Source DB URL")
    parser.add_argument("--target", required=True, help="Target DB URL (PostgreSQL or SQLite)")
    parser.add_argument("--batch-size", type=int, default=500, help="Batch size")
    args = parser.parse_args()

    migrate_database(args.source, args.target, args.batch_size)
