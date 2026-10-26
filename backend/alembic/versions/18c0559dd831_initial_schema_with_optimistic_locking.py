"""Initial schema with full tables and optimistic locking

Revision ID: 18c0559dd831
Revises: 
Create Date: 2026-10-25 23:13:45.589111

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '18c0559dd831'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. Table: programs
    if "programs" not in existing_tables:
        op.create_table(
            "programs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("code", sa.String(32), nullable=False, unique=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("platform", sa.String(64), nullable=False),
            sa.Column("phase", sa.String(32), nullable=False, server_default="Proto-A"),
            sa.Column("sop_date", sa.String(10), nullable=True),
            sa.Column("lead_engineer", sa.String(64), nullable=False),
            sa.Column("quality_manager", sa.String(64), nullable=False),
            sa.Column("target_market", sa.String(64), nullable=False, server_default="Global"),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_programs_code", "programs", ["code"])

    # 2. Table: parts
    if "parts" not in existing_tables:
        op.create_table(
            "parts",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("part_number", sa.String(64), nullable=False, unique=True),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("subsystem", sa.String(64), nullable=False),
            sa.Column("category", sa.String(64), nullable=False),
            sa.Column("supplier", sa.String(128), nullable=False),
            sa.Column("material", sa.String(128), nullable=False),
            sa.Column("revision", sa.String(16), nullable=False, server_default="Rev A.0"),
            sa.Column("weight_kg", sa.Float(), nullable=False, server_default="1.0"),
            sa.Column("safety_critical", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_parts_part_number", "parts", ["part_number"])
        op.create_index("ix_parts_program_id", "parts", ["program_id"])
        op.create_index("ix_parts_subsystem", "parts", ["subsystem"])

    # 3. Table: dfmeas
    if "dfmeas" not in existing_tables:
        op.create_table(
            "dfmeas",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("part_id", sa.Integer(), sa.ForeignKey("parts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("item_function", sa.String(256), nullable=False),
            sa.Column("failure_mode", sa.String(256), nullable=False),
            sa.Column("failure_effect", sa.Text(), nullable=False),
            sa.Column("severity", sa.Integer(), nullable=False),
            sa.Column("potential_cause", sa.Text(), nullable=False),
            sa.Column("occurrence", sa.Integer(), nullable=False),
            sa.Column("prevention_control", sa.Text(), nullable=False),
            sa.Column("detection_control", sa.Text(), nullable=False),
            sa.Column("detection", sa.Integer(), nullable=False),
            sa.Column("rpn", sa.Integer(), nullable=False),
            sa.Column("action_priority", sa.String(8), nullable=False),
            sa.Column("recommended_action", sa.Text(), nullable=True),
            sa.Column("responsible", sa.String(64), nullable=True),
            sa.Column("target_date", sa.String(10), nullable=True),
            sa.Column("action_status", sa.String(32), nullable=False, server_default="Open"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_dfmeas_part_id", "dfmeas", ["part_id"])
        op.create_index("ix_dfmeas_action_priority", "dfmeas", ["action_priority"])

    # 4. Table: dvprs
    if "dvprs" not in existing_tables:
        op.create_table(
            "dvprs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("part_id", sa.Integer(), sa.ForeignKey("parts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("dfmea_id", sa.Integer(), sa.ForeignKey("dfmeas.id", ondelete="SET NULL"), nullable=True),
            sa.Column("plan_code", sa.String(64), nullable=False, unique=True),
            sa.Column("test_phase", sa.String(32), nullable=False),
            sa.Column("test_name", sa.String(256), nullable=False),
            sa.Column("standard_ref", sa.String(128), nullable=False),
            sa.Column("acceptance_criteria", sa.Text(), nullable=False),
            sa.Column("sample_size", sa.Integer(), nullable=False, server_default="3"),
            sa.Column("target_completion_date", sa.String(10), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="Planned"),
            sa.Column("responsible_engineer", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_dvprs_plan_code", "dvprs", ["plan_code"])
        op.create_index("ix_dvprs_program_id", "dvprs", ["program_id"])
        op.create_index("ix_dvprs_part_id", "dvprs", ["part_id"])

    # 5. Table: test_runs
    if "test_runs" not in existing_tables:
        op.create_table(
            "test_runs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("dvpr_id", sa.Integer(), sa.ForeignKey("dvprs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("run_number", sa.String(64), nullable=False, unique=True),
            sa.Column("sample_identifier", sa.String(64), nullable=False),
            sa.Column("test_bench", sa.String(128), nullable=False),
            sa.Column("chamber_temp_c", sa.Float(), nullable=False),
            sa.Column("chamber_humidity_rh", sa.Float(), nullable=False),
            sa.Column("cycles_completed", sa.Integer(), nullable=False),
            sa.Column("target_cycles", sa.Integer(), nullable=False),
            sa.Column("result", sa.String(16), nullable=False),
            sa.Column("failure_description", sa.Text(), nullable=True),
            sa.Column("telemetry_data", sa.Text(), nullable=True),
            sa.Column("executed_at", sa.DateTime(), nullable=True),
            sa.Column("operator", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_test_runs_run_number", "test_runs", ["run_number"])
        op.create_index("ix_test_runs_dvpr_id", "test_runs", ["dvpr_id"])

    # 6. Table: issues
    if "issues" not in existing_tables:
        op.create_table(
            "issues",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("issue_code", sa.String(64), nullable=False, unique=True),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("part_id", sa.Integer(), sa.ForeignKey("parts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("test_run_id", sa.Integer(), sa.ForeignKey("test_runs.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("severity", sa.String(16), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="New"),
            sa.Column("containment_action", sa.Text(), nullable=True),
            sa.Column("assignee", sa.String(64), nullable=False),
            sa.Column("target_close_date", sa.String(10), nullable=True),
            sa.Column("closed_at", sa.DateTime(), nullable=True),
            sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_issues_issue_code", "issues", ["issue_code"])
        op.create_index("ix_issues_program_id", "issues", ["program_id"])
        op.create_index("ix_issues_part_id", "issues", ["part_id"])
    else:
        columns = {c["name"] for c in inspector.get_columns("issues")}
        if "version_id" not in columns:
            with op.batch_alter_table("issues") as batch_op:
                batch_op.add_column(sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"))

    # 7. Table: root_causes
    if "root_causes" not in existing_tables:
        op.create_table(
            "root_causes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("methodology", sa.String(32), nullable=False, server_default="5-Why"),
            sa.Column("why_1", sa.Text(), nullable=False),
            sa.Column("why_2", sa.Text(), nullable=True),
            sa.Column("why_3", sa.Text(), nullable=True),
            sa.Column("why_4", sa.Text(), nullable=True),
            sa.Column("why_5", sa.Text(), nullable=True),
            sa.Column("ishikawa_factors", sa.Text(), nullable=True),
            sa.Column("root_cause_summary", sa.Text(), nullable=False),
            sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_root_causes_issue_id", "root_causes", ["issue_id"])

    # 8. Table: changes
    if "changes" not in existing_tables:
        op.create_table(
            "changes",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("change_code", sa.String(64), nullable=False, unique=True),
            sa.Column("program_id", sa.Integer(), sa.ForeignKey("programs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("part_id", sa.Integer(), sa.ForeignKey("parts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("issue_id", sa.Integer(), sa.ForeignKey("issues.id", ondelete="SET NULL"), nullable=True),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("change_type", sa.String(32), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("pre_change_rev", sa.String(16), nullable=False),
            sa.Column("post_change_rev", sa.String(16), nullable=False),
            sa.Column("cost_impact_rmb", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("weight_impact_kg", sa.Float(), nullable=False, server_default="0.0"),
            sa.Column("tooling_lead_weeks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("requires_homologation", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("requires_dvp_retest", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("approval_status", sa.String(32), nullable=False, server_default="Draft"),
            sa.Column("initiator", sa.String(64), nullable=False),
            sa.Column("approver", sa.String(64), nullable=True),
            sa.Column("approval_date", sa.String(10), nullable=True),
            sa.Column("implementation_date", sa.String(10), nullable=True),
            sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_changes_change_code", "changes", ["change_code"])
        op.create_index("ix_changes_program_id", "changes", ["program_id"])
        op.create_index("ix_changes_part_id", "changes", ["part_id"])
    else:
        columns = {c["name"] for c in inspector.get_columns("changes")}
        if "version_id" not in columns:
            with op.batch_alter_table("changes") as batch_op:
                batch_op.add_column(sa.Column("version_id", sa.Integer(), nullable=False, server_default="1"))

    # 9. Table: knowledge_items
    if "knowledge_items" not in existing_tables:
        op.create_table(
            "knowledge_items",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("title", sa.String(256), nullable=False),
            sa.Column("category", sa.String(64), nullable=False),
            sa.Column("subsystem", sa.String(64), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("standard_code", sa.String(64), nullable=True),
            sa.Column("tags", sa.String(256), nullable=True),
            sa.Column("author", sa.String(64), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_knowledge_items_category", "knowledge_items", ["category"])
        op.create_index("ix_knowledge_items_subsystem", "knowledge_items", ["subsystem"])

    # 10. Table: users
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("username", sa.String(64), nullable=False, unique=True),
            sa.Column("email", sa.String(128), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(256), nullable=False),
            sa.Column("full_name", sa.String(128), nullable=False),
            sa.Column("role", sa.String(32), nullable=False, server_default="design_eng"),
            sa.Column("department", sa.String(64), nullable=False, server_default="Engineering Quality"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_users_username", "users", ["username"])
        op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    tables = [
        "users", "knowledge_items", "changes", "root_causes",
        "issues", "test_runs", "dvprs", "dfmeas", "parts", "programs"
    ]
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = set(inspector.get_table_names())
    for t in tables:
        if t in existing:
            op.drop_table(t)
