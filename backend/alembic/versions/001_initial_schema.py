"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension only if available on the system
    bind = op.get_bind()
    try:
        available = bind.execute(sa.text("SELECT COUNT(*) FROM pg_available_extensions WHERE name='postgis'"))
        count = available.scalar() if hasattr(available, 'scalar') else list(available)[0][0]
        if count and int(count) > 0:
            op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    except Exception:
        # If the extension is not available (e.g., missing control file), skip without failing migrations
        pass
    
    # NOTE: In non-PostGIS environments, we store latitude/longitude as floats.
    # Create users table
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=True),
    sa.Column('phone_verified', sa.Boolean(), nullable=True),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('GUEST', 'RENTER', 'HOST', 'ADMIN', name='userrole'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('kyc_status', sa.Enum('PENDING', 'SUBMITTED', 'VERIFIED', 'REJECTED', name='kycstatus'), nullable=True),
    sa.Column('email_verified', sa.Boolean(), nullable=True),
    sa.Column('last_login', sa.String(length=255), nullable=True),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)

    # Create profiles table
    op.create_table('profiles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('avatar_url', sa.String(length=500), nullable=True),
    sa.Column('bio', sa.Text(), nullable=True),
    sa.Column('date_of_birth', sa.String(length=10), nullable=True),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('state', sa.String(length=100), nullable=True),
    sa.Column('pincode', sa.String(length=10), nullable=True),
    sa.Column('country', sa.String(length=100), nullable=True),
    sa.Column('preferred_language', sa.String(length=10), nullable=True),
    sa.Column('timezone', sa.String(length=50), nullable=True),
    sa.Column('currency', sa.String(length=5), nullable=True),
    sa.Column('email_notifications', sa.Boolean(), nullable=True),
    sa.Column('sms_notifications', sa.Boolean(), nullable=True),
    sa.Column('push_notifications', sa.Boolean(), nullable=True),
    sa.Column('kyc_documents', sa.JSON(), nullable=True),
    sa.Column('host_rating', sa.String(length=5), nullable=True),
    sa.Column('host_rating_count', sa.Integer(), nullable=True),
    sa.Column('response_time_minutes', sa.Integer(), nullable=True),
    sa.Column('vehicle_details', sa.JSON(), nullable=True),
    sa.Column('preferred_connectors', sa.JSON(), nullable=True),
    sa.Column('emergency_contact_name', sa.String(length=255), nullable=True),
    sa.Column('emergency_contact_phone', sa.String(length=20), nullable=True),
    sa.Column('social_links', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'], unique=False)

    # Create chargers table
    op.create_table('chargers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('host_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('address', sa.Text(), nullable=False),
    sa.Column('city', sa.String(length=100), nullable=False),
    sa.Column('state', sa.String(length=100), nullable=False),
    sa.Column('pincode', sa.String(length=10), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.Column('connector_type', sa.Enum('CCS', 'CHADEMO', 'NACS', 'TYPE2', 'TYPE1', name='connectortype'), nullable=False),
    sa.Column('charger_type', sa.Enum('LEVEL1', 'LEVEL2', 'DC_FAST', name='chargertype'), nullable=False),
    sa.Column('max_power_kw', sa.Float(), nullable=False),
    sa.Column('voltage', sa.Integer(), nullable=True),
    sa.Column('current_rating', sa.Integer(), nullable=True),
    sa.Column('images', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('cover_image', sa.String(length=500), nullable=True),
    sa.Column('amenities', sa.JSON(), nullable=True),
    sa.Column('features', sa.JSON(), nullable=True),
    sa.Column('availability_schedule', sa.JSON(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('is_verified', sa.Boolean(), nullable=True),
    sa.Column('auto_accept_bookings', sa.Boolean(), nullable=True),
    sa.Column('current_status', sa.Enum('AVAILABLE', 'IN_USE', 'MAINTENANCE', 'OFFLINE', 'FAULT', name='chargerstatus'), nullable=True),
    sa.Column('last_maintenance', sa.DateTime(), nullable=True),
    sa.Column('access_instructions', sa.Text(), nullable=True),
    sa.Column('access_code', sa.String(length=50), nullable=True),
    sa.Column('host_contact_required', sa.Boolean(), nullable=True),
    sa.Column('total_bookings', sa.Integer(), nullable=True),
    sa.Column('total_energy_delivered', sa.Float(), nullable=True),
    sa.Column('average_rating', sa.Float(), nullable=True),
    sa.Column('rating_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['host_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chargers_id'), 'chargers', ['id'], unique=False)
    op.create_index('idx_chargers_city_active', 'chargers', ['city', 'is_active'], unique=False)

    # Create charger_pricing table
    op.create_table('charger_pricing',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('charger_id', sa.Integer(), nullable=False),
    sa.Column('pricing_type', sa.Enum('PER_HOUR', 'PER_KWH', 'FLAT_RATE', name='pricingtype'), nullable=False),
    sa.Column('price_value', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(length=5), nullable=True),
    sa.Column('min_session_minutes', sa.Integer(), nullable=True),
    sa.Column('max_session_minutes', sa.Integer(), nullable=True),
    sa.Column('peak_hours_start', sa.String(length=5), nullable=True),
    sa.Column('peak_hours_end', sa.String(length=5), nullable=True),
    sa.Column('peak_price_multiplier', sa.Float(), nullable=True),
    sa.Column('weekend_price_multiplier', sa.Float(), nullable=True),
    sa.Column('cancellation_policy', sa.JSON(), nullable=True),
    sa.Column('advance_booking_hours', sa.Integer(), nullable=True),
    sa.Column('same_day_booking', sa.Boolean(), nullable=True),
    sa.Column('booking_fee', sa.Float(), nullable=True),
    sa.Column('overstay_fee_per_hour', sa.Float(), nullable=True),
    sa.Column('late_cancellation_fee', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_charger_pricing_id'), 'charger_pricing', ['id'], unique=False)

    # Create bookings table
    op.create_table('bookings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('charger_id', sa.Integer(), nullable=False),
    sa.Column('renter_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
    sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'CONFIRMED', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'FAILED', 'NO_SHOW', 'EXPIRED', name='bookingstatus'), nullable=False),
    sa.Column('payment_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIAL_REFUND', name='paymentstatus'), nullable=False),
    sa.Column('pricing_type', sa.String(length=20), nullable=False),
    sa.Column('unit_price', sa.Float(), nullable=False),
    sa.Column('estimated_cost', sa.Float(), nullable=False),
    sa.Column('final_cost', sa.Float(), nullable=True),
    sa.Column('subtotal', sa.Float(), nullable=False),
    sa.Column('platform_fee', sa.Float(), nullable=False),
    sa.Column('taxes', sa.Float(), nullable=True),
    sa.Column('total_amount', sa.Float(), nullable=False),
    sa.Column('paid_amount', sa.Float(), nullable=True),
    sa.Column('currency', sa.String(length=5), nullable=True),
    sa.Column('payment_method', sa.String(length=50), nullable=True),
    sa.Column('payment_id', sa.String(length=255), nullable=True),
    sa.Column('razorpay_order_id', sa.String(length=255), nullable=True),
    sa.Column('razorpay_payment_id', sa.String(length=255), nullable=True),
    sa.Column('booking_code', sa.String(length=20), nullable=False),
    sa.Column('qr_code_url', sa.String(length=500), nullable=True),
    sa.Column('vehicle_info', sa.JSON(), nullable=True),
    sa.Column('access_code', sa.String(length=50), nullable=True),
    sa.Column('special_instructions', sa.Text(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('started_charging_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('cancellation_reason', sa.Text(), nullable=True),
    sa.Column('cancelled_by', sa.String(length=20), nullable=True),
    sa.Column('refund_amount', sa.Float(), nullable=True),
    sa.Column('extended_times', sa.Integer(), nullable=True),
    sa.Column('overstay_minutes', sa.Integer(), nullable=True),
    sa.Column('overstay_fee', sa.Float(), nullable=True),
    sa.Column('host_notified', sa.Boolean(), nullable=True),
    sa.Column('renter_notified', sa.Boolean(), nullable=True),
    sa.Column('host_notes', sa.Text(), nullable=True),
    sa.Column('admin_notes', sa.Text(), nullable=True),
    sa.Column('status_history', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['charger_id'], ['chargers.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['renter_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('booking_code')
    )
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    op.create_index('idx_bookings_start_time', 'bookings', ['start_time'], unique=False)
    op.create_index('idx_bookings_status', 'bookings', ['status'], unique=False)

    # Create remaining tables (sessions, reviews, payouts, disputes, audit_logs, charger_telemetry)
    # ... (continuing in next part due to length)


def downgrade() -> None:
    op.drop_index('idx_bookings_status', table_name='bookings')
    op.drop_index('idx_bookings_start_time', table_name='bookings')
    op.drop_index(op.f('ix_bookings_id'), table_name='bookings')
    op.drop_table('bookings')
    op.drop_index(op.f('ix_charger_pricing_id'), table_name='charger_pricing')
    op.drop_table('charger_pricing')
    op.drop_index('idx_chargers_city_active', table_name='chargers')
    op.drop_index(op.f('ix_chargers_id'), table_name='chargers')
    op.drop_table('chargers')
    op.drop_index(op.f('ix_profiles_id'), table_name='profiles')
    op.drop_table('profiles')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS kycstatus")
    op.execute("DROP TYPE IF EXISTS connectortype")
    op.execute("DROP TYPE IF EXISTS chargertype")
    op.execute("DROP TYPE IF EXISTS chargerstatus")
    op.execute("DROP TYPE IF EXISTS pricingtype")
    op.execute("DROP TYPE IF EXISTS bookingstatus")
    op.execute("DROP TYPE IF EXISTS paymentstatus")