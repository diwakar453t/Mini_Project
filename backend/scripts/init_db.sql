-- Initialize database with PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create indexes for better performance
-- Note: These will be created by Alembic migrations, but included here for reference

-- Spatial index on charger locations (created by Alembic)
-- CREATE INDEX IF NOT EXISTS idx_chargers_location ON chargers USING GIST (location);

-- Common search indexes
-- CREATE INDEX IF NOT EXISTS idx_chargers_city_active ON chargers (city, is_active);
-- CREATE INDEX IF NOT EXISTS idx_chargers_connector_type ON chargers (connector_type);
-- CREATE INDEX IF NOT EXISTS idx_chargers_charger_type ON chargers (charger_type);

-- Booking indexes
-- CREATE INDEX IF NOT EXISTS idx_bookings_start_time ON bookings (start_time);
-- CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings (status);
-- CREATE INDEX IF NOT EXISTS idx_bookings_renter_status ON bookings (renter_id, status);

-- User indexes  
-- CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
-- CREATE INDEX IF NOT EXISTS idx_users_phone ON users (phone);
-- CREATE INDEX IF NOT EXISTS idx_users_role_active ON users (role, is_active);

-- Review indexes
-- CREATE INDEX IF NOT EXISTS idx_reviews_charger_public ON reviews (charger_id, is_public);

-- Telemetry indexes
-- CREATE INDEX IF NOT EXISTS idx_charger_telemetry_timestamp ON charger_telemetry (charger_id, timestamp);

-- Functions for common operations
CREATE OR REPLACE FUNCTION calculate_distance(lat1 float, lon1 float, lat2 float, lon2 float)
RETURNS float AS $$
BEGIN
    -- Calculate distance in kilometers using Haversine formula
    RETURN (
        6371 * acos(
            cos(radians(lat1)) * cos(radians(lat2)) * 
            cos(radians(lon2) - radians(lon1)) + 
            sin(radians(lat1)) * sin(radians(lat2))
        )
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to generate booking codes
CREATE OR REPLACE FUNCTION generate_booking_code()
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..8 LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::INTEGER, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to update charger rating
CREATE OR REPLACE FUNCTION update_charger_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE chargers SET
        average_rating = (
            SELECT COALESCE(AVG(rating::float), 0.0)
            FROM reviews 
            WHERE charger_id = NEW.charger_id AND is_public = true
        ),
        rating_count = (
            SELECT COUNT(*)
            FROM reviews 
            WHERE charger_id = NEW.charger_id AND is_public = true
        )
    WHERE id = NEW.charger_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update host rating
CREATE OR REPLACE FUNCTION update_host_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE profiles SET
        host_rating = (
            SELECT COALESCE(AVG(r.host_communication_rating::float), 0.0)::TEXT
            FROM reviews r
            JOIN chargers c ON r.charger_id = c.id
            WHERE c.host_id = (SELECT host_id FROM chargers WHERE id = NEW.charger_id)
            AND r.is_public = true
            AND r.host_communication_rating IS NOT NULL
        ),
        host_rating_count = (
            SELECT COUNT(*)
            FROM reviews r
            JOIN chargers c ON r.charger_id = c.id
            WHERE c.host_id = (SELECT host_id FROM chargers WHERE id = NEW.charger_id)
            AND r.is_public = true
            AND r.host_communication_rating IS NOT NULL
        )
    WHERE user_id = (SELECT host_id FROM chargers WHERE id = NEW.charger_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;