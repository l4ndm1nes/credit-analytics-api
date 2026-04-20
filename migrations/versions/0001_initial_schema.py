from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("login", sa.String(length=128), nullable=False),
        sa.Column("registration_date", sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("login", name="uq_users_login"),
    )

    op.create_table(
        "dictionary",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_dictionary"),
        sa.UniqueConstraint("name", name="uq_dictionary_name"),
    )

    op.create_table(
        "auth_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("login", sa.String(length=128), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_auth_users"),
        sa.UniqueConstraint("login", name="uq_auth_users_login"),
    )

    op.create_table(
        "credits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("issuance_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=False),
        sa.Column("actual_return_date", sa.Date(), nullable=True),
        sa.Column("body", sa.Numeric(18, 2), nullable=False),
        sa.Column("percent", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_credits_user_id_users",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_credits"),
    )
    op.create_index("ix_credits_user_id", "credits", ["user_id"])
    op.create_index("ix_credits_issuance_date", "credits", ["issuance_date"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("credit_id", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("sum", sa.Numeric(18, 2), nullable=False),
        sa.ForeignKeyConstraint(
            ["credit_id"],
            ["credits.id"],
            name="fk_payments_credit_id_credits",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["type_id"],
            ["dictionary.id"],
            name="fk_payments_type_id_dictionary",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
    )
    op.create_index("ix_payments_credit_id", "payments", ["credit_id"])
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"])

    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("sum", sa.Numeric(18, 2), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["dictionary.id"],
            name="fk_plans_category_id_dictionary",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_plans"),
        sa.UniqueConstraint("period", "category_id", name="uq_plans_period_category"),
    )
    op.create_index("ix_plans_period", "plans", ["period"])


def downgrade() -> None:
    op.drop_index("ix_plans_period", table_name="plans")
    op.drop_table("plans")

    op.drop_index("ix_payments_payment_date", table_name="payments")
    op.drop_index("ix_payments_credit_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_credits_issuance_date", table_name="credits")
    op.drop_index("ix_credits_user_id", table_name="credits")
    op.drop_table("credits")

    op.drop_table("auth_users")
    op.drop_table("dictionary")
    op.drop_table("users")
