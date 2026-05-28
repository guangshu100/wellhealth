"""add_extension_tables

Revision ID: 481143e533da
Revises:
Create Date: 2026-05-28 13:20:55.534477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '481143e533da'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('insurance_medicine_catalog',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('drug_code', sa.String(length=20), nullable=False),
        sa.Column('drug_name', sa.String(length=100), nullable=False),
        sa.Column('specification', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=10), nullable=False),
        sa.Column('reimbursement_rate', sa.Float(), nullable=False),
        sa.Column('restrictions', sa.Text(), nullable=True),
        sa.Column('dosage_form', sa.String(length=50), nullable=False),
        sa.Column('manufacturer', sa.String(length=100), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_to', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_insurance_medicine_catalog_drug_code'), 'insurance_medicine_catalog', ['drug_code'], unique=False)

    op.create_table('drug_interaction',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('drug_a_code', sa.String(length=20), nullable=False),
        sa.Column('drug_a_name', sa.String(length=100), nullable=False),
        sa.Column('drug_b_code', sa.String(length=20), nullable=False),
        sa.Column('drug_b_name', sa.String(length=100), nullable=False),
        sa.Column('interaction_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('mechanism', sa.Text(), nullable=True),
        sa.Column('clinical_effect', sa.Text(), nullable=True),
        sa.Column('management', sa.Text(), nullable=True),
        sa.Column('evidence_source', sa.String(length=200), nullable=True),
        sa.Column('evidence_level', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_drug_interaction_drug_a_code'), 'drug_interaction', ['drug_a_code'], unique=False)
    op.create_index(op.f('ix_drug_interaction_drug_b_code'), 'drug_interaction', ['drug_b_code'], unique=False)

    op.create_table('medicine_dosage_range',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('drug_code', sa.String(length=20), nullable=False),
        sa.Column('drug_name', sa.String(length=100), nullable=False),
        sa.Column('indication', sa.String(length=200), nullable=True),
        sa.Column('age_group', sa.String(length=50), nullable=True),
        sa.Column('renal_function', sa.String(length=50), nullable=True),
        sa.Column('min_dose', sa.Float(), nullable=True),
        sa.Column('max_dose', sa.Float(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('frequency', sa.String(length=50), nullable=True),
        sa.Column('route', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_medicine_dosage_range_drug_code'), 'medicine_dosage_range', ['drug_code'], unique=False)

    op.create_table('closed_loop_records',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('triage_id', sa.String(length=36), nullable=True),
        sa.Column('internet_hospital_session_id', sa.String(length=100), nullable=True),
        sa.Column('prescription_id', sa.String(length=36), nullable=True),
        sa.Column('follow_up_plan_id', sa.String(length=36), nullable=True),
        sa.Column('loop_status', sa.String(length=20), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=False),
        sa.Column('step_history', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_closed_loop_records_loop_status'), 'closed_loop_records', ['loop_status'], unique=False)
    op.create_index(op.f('ix_closed_loop_records_patient_id'), 'closed_loop_records', ['patient_id'], unique=False)

    op.create_table('elderly_care_record',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('fall_risk_score', sa.Float(), nullable=True),
        sa.Column('fall_risk_level', sa.String(length=10), nullable=True),
        sa.Column('cognitive_score', sa.Integer(), nullable=True),
        sa.Column('cognitive_level', sa.String(length=10), nullable=True),
        sa.Column('polypharmacy_count', sa.Integer(), nullable=True),
        sa.Column('polypharmacy_review_status', sa.String(length=20), nullable=True),
        sa.Column('living_alone', sa.Boolean(), nullable=True),
        sa.Column('assistive_devices', sa.JSON(), nullable=True),
        sa.Column('assessment_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_elderly_care_record_patient_id'), 'elderly_care_record', ['patient_id'], unique=False)

    op.create_table('child_health_record',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('height_percentile', sa.Float(), nullable=True),
        sa.Column('weight_percentile', sa.Float(), nullable=True),
        sa.Column('bmi_percentile', sa.Float(), nullable=True),
        sa.Column('vaccination_records', sa.JSON(), nullable=True),
        sa.Column('vaccination_next_due', sa.DateTime(), nullable=True),
        sa.Column('screening_results', sa.JSON(), nullable=True),
        sa.Column('growth_standard_source', sa.String(length=20), nullable=True),
        sa.Column('assessment_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_child_health_record_patient_id'), 'child_health_record', ['patient_id'], unique=False)

    op.create_table('prescription_review_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('review_id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('reviewer_type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('issues', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_prescription_review_results_patient_id'), 'prescription_review_results', ['patient_id'], unique=False)
    op.create_index(op.f('ix_prescription_review_results_review_id'), 'prescription_review_results', ['review_id'], unique=False)

    op.create_table('health_plans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('patient_id', sa.String(length=36), nullable=False),
        sa.Column('plan_type', sa.String(length=30), nullable=False),
        sa.Column('goals', sa.JSON(), nullable=True),
        sa.Column('milestones', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_charset='utf8mb4',
    )
    op.create_index(op.f('ix_health_plans_patient_id'), 'health_plans', ['patient_id'], unique=False)


def downgrade() -> None:
    op.drop_table('health_plans')
    op.drop_table('prescription_review_results')
    op.drop_table('child_health_record')
    op.drop_table('elderly_care_record')
    op.drop_table('closed_loop_records')
    op.drop_table('medicine_dosage_range')
    op.drop_table('drug_interaction')
    op.drop_table('insurance_medicine_catalog')
