CREATE TABLE api_requests (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    request_method VARCHAR(10),
    endpoint TEXT,
    request_data TEXT,
    response_data JSONB,
    user_agent TEXT,
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);