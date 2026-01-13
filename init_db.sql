-- Valenbisi Database Initialization Script
-- Creates the main table and indexes for optimal performance

-- Create the main table for raw Valenbisi data
CREATE TABLE IF NOT EXISTS valenbisi_raw (
    id SERIAL PRIMARY KEY,
    station_id INTEGER NOT NULL,
    station_name VARCHAR(255),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    available_bikes INTEGER,
    available_slots INTEGER,
    station_status VARCHAR(50),
    total_capacity INTEGER,
    timestamp TIMESTAMP NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_valenbisi_station_id ON valenbisi_raw(station_id);
CREATE INDEX IF NOT EXISTS idx_valenbisi_timestamp ON valenbisi_raw(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_valenbisi_station_timestamp ON valenbisi_raw(station_id, timestamp DESC);

-- Create a view for the latest status of each station
CREATE OR REPLACE VIEW valenbisi_latest AS
SELECT DISTINCT ON (station_id)
    station_id,
    station_name,
    latitude,
    longitude,
    available_bikes,
    available_slots,
    station_status,
    total_capacity,
    timestamp
FROM valenbisi_raw
ORDER BY station_id, timestamp DESC;

COMMENT ON TABLE valenbisi_raw IS 'Raw data from Valenbisi API collected every 5 minutes';
COMMENT ON VIEW valenbisi_latest IS 'Latest status for each Valenbisi station';
