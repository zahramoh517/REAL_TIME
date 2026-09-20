CREATE TABLE shipments (
    shipment_id UUID PRIMARY KEY,
    po_number BIGINT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    container_number VARCHAR(50) NOT NULL,
    original_eta TIMESTAMP NOT NULL
);

CREATE TABLE route_ (
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

COPY shipments FROM '/Users/zahra/Desktop/REAL_TIME/table1_shipments.csv' DELIMITER ',' CSV HEADER;
COPY route_ FROM '/Users/zahra/Desktop/REAL_TIME/table3_route_reference.csv' DELIMITER ',' CSV HEADER;
COPY events FROM '/Users/zahra/Desktop/REAL_TIME/table2_events.csv' DELIMITER ',' CSV HEADER;
