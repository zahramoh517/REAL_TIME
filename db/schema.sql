

CREATE TABLE shipments (
    shipment_id UUID PRIMARY KEY,
    po_number BIGINT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    container_number VARCHAR(50) NOT NULL,
    original_eta TIMESTAMP NOT NULL
);

CREATE TABLE route_reference (
    route_id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL REFERENCES shipments(shipment_id),
    hub_name TEXT NOT NULL,
    expected_arrival_start TIMESTAMP NOT NULL,
    expected_arrival_end TIMESTAMP NOT NULL,
    sequence_order INT NOT NULL
);

CREATE TABLE events (
    event_id UUID PRIMARY KEY,
    shipment_id UUID NOT NULL REFERENCES shipments(shipment_id),
    timestamp TIMESTAMP NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    hub_name TEXT
);

CREATE TABLE alerts (
    alert_id SERIAL PRIMARY KEY,
    shipment_id UUID REFERENCES shipments(shipment_id),
    alert_type TEXT,
    triggering_event_id UUID REFERENCES events(event_id),
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT now(),
    resolved_at TIMESTAMP
)
COPY shipments FROM "" DELIMITER ',' CSV HEADER;
COPY route_reference FROM "" DELIMITER ',' CSV HEADER;
