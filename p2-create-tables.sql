CREATE TABLE airport(
    airport_name VARCHAR(20),
    airport_city VARCHAR(20),
    PRIMARY KEY (airport_name)
);

CREATE TABLE airline(
    airline_name VARCHAR(20),
    PRIMARY KEY (airline_name)
);

CREATE TABLE airplane(
    airplane_id CHAR(5),
    airline_name VARCHAR(20),
    seats NUMERIC(3,0),
    PRIMARY KEY (airplane_id,airline_name),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name)
);

CREATE TABLE flight (
    flight_num CHAR(5),
    airline_name VARCHAR(20),
    departure_airport VARCHAR(20),
    departure_time DATETIME,
    arrival_airport VARCHAR(20),
    arrival_time DATETIME,
    price NUMERIC(10, 2),
    flight_status VARCHAR(20) CHECK (flight_status IN ('upcoming', 'in-progress', 'on-time', 'delayed', 'cancelled')),
    airplane_id CHAR(5) NOT NULL,
    PRIMARY KEY (flight_num, airline_name),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name),
    FOREIGN KEY (departure_airport) REFERENCES airport(airport_name),
    FOREIGN KEY (arrival_airport) REFERENCES airport(airport_name),
    FOREIGN KEY (airplane_id) REFERENCES airplane(airplane_id)
);

CREATE TABLE customer(
    cust_email VARCHAR(20),
    cust_name VARCHAR(20),
    cust_password VARCHAR(32),
    address_building_number NUMERIC(4,0),
    address_street VARCHAR(20),
    address_city VARCHAR(20),
    address_state VARCHAR(20),
    phone_number NUMERIC(20,0), -- to account for different country conventions
    passport_number NUMERIC(10,0),
    passport_expiration DATE,
    passport_country VARCHAR(20),
    date_of_birth DATE,
    PRIMARY KEY (cust_email)
);

CREATE TABLE booking_agent(
    booking_agent_email VARCHAR(20),
    agent_password VARCHAR(32),
    booking_agent_id CHAR(5),
    PRIMARY KEY (booking_agent_email),
    INDEX booking_agent_id_index (booking_agent_id)
);

CREATE TABLE ticket(
    ticket_id CHAR(5),
    cust_email VARCHAR(20),
    airline_name VARCHAR(20),
    flight_num CHAR(5),
    booking_agent_id CHAR(5) NULL,
    booking_date DATE,
    PRIMARY KEY (ticket_id),
    FOREIGN KEY (cust_email) REFERENCES customer(cust_email),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name),
    FOREIGN KEY (flight_num) REFERENCES flight(flight_num),
    FOREIGN KEY (booking_agent_id) REFERENCES booking_agent(booking_agent_id)
);

CREATE TABLE employee(
    airline_name VARCHAR(20),
    booking_agent_password VARCHAR(32), 
    PRIMARY KEY (airline_name, booking_agent_email),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name),
    FOREIGN KEY (booking_agent_email) REFERENCES booking_agent(booking_agent_email)
);

CREATE TABLE airline_staff(
    staff_username VARCHAR(20),
    staff_password VARCHAR(32),
    first_name VARCHAR(20),
    last_name VARCHAR(20),
    date_of_birth DATE,
    airline_name VARCHAR(20),
    PRIMARY KEY (staff_username),
    FOREIGN KEY (airline_name) REFERENCES airline(airline_name)
);

CREATE TABLE permissions(
    staff_username VARCHAR(20),
    permission VARCHAR(20) CHECK (permission in ('admin', 'operator')),
    PRIMARY KEY (staff_username, permission),
    FOREIGN KEY (staff_username) REFERENCES airline_staff(staff_username)
);
