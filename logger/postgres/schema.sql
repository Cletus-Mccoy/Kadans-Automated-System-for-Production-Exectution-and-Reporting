CREATE TABLE plc_variables (
    id SERIAL PRIMARY KEY,
    machine_name TEXT,
    variable_name TEXT,
    data_type TEXT,
    trigger_type TEXT,     -- 'on_change', 'on_rising', 'on_cycle'
    polling_interval INT   -- in ms, nullable
);