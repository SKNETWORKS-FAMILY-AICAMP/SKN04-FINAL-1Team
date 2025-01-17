CREATE TABLE IF NOT EXISTS log (
    id SERIAL PRIMARY KEY,
    dttm TIMESTAMP WITH TIME ZONE,
    dag_id VARCHAR(250),
    task_id VARCHAR(250),
    map_index INTEGER,
    event VARCHAR(255),
    execution_date TIMESTAMP WITH TIME ZONE,
    owner VARCHAR(255),
    extra TEXT
);

CREATE TABLE IF NOT EXISTS connection (
    id SERIAL PRIMARY KEY,
    conn_id VARCHAR(255) UNIQUE,
    conn_type VARCHAR(255),
    description TEXT,
    host VARCHAR(255),
    schema VARCHAR(255),
    login VARCHAR(255),
    password VARCHAR(255),
    port INTEGER,
    is_encrypted BOOLEAN DEFAULT false,
    is_extra_encrypted BOOLEAN DEFAULT false,
    extra JSONB
);

CREATE TABLE IF NOT EXISTS ab_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    password VARCHAR(255),
    active BOOLEAN,
    email VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    fail_login_count INTEGER DEFAULT 0,
    created_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_on TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by_fk INTEGER,
    changed_by_fk INTEGER
);

CREATE TABLE IF NOT EXISTS ab_register_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    email VARCHAR(255),
    registration_date TIMESTAMP WITH TIME ZONE
); 