--
-- PostgreSQL database dump
--

\restrict a6MICHVm7UZR3AWCNVtklyuVmFSqmkn96QEyQFuHxorhVadnQ1ZY49OTRiLNv6d

-- Dumped from database version 16.10
-- Dumped by pg_dump version 16.10

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.vehicle_events DROP CONSTRAINT IF EXISTS vehicle_events_vehicle_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_recorded_by_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_driver_id_fkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_contract_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_vehicle_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_recorded_by_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_driver_id_fkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_contract_id_fkey;
ALTER TABLE IF EXISTS ONLY public.contracts DROP CONSTRAINT IF EXISTS contracts_vehicle_id_fkey;
ALTER TABLE IF EXISTS ONLY public.contracts DROP CONSTRAINT IF EXISTS contracts_driver_id_fkey;
ALTER TABLE IF EXISTS ONLY public.capital_adjustments DROP CONSTRAINT IF EXISTS capital_adjustments_recorded_by_fkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey;
DROP INDEX IF EXISTS public.ix_users_username;
ALTER TABLE IF EXISTS ONLY public.vehicles DROP CONSTRAINT IF EXISTS vehicles_vehicle_number_key;
ALTER TABLE IF EXISTS ONLY public.vehicles DROP CONSTRAINT IF EXISTS vehicles_reg_number_key;
ALTER TABLE IF EXISTS ONLY public.vehicles DROP CONSTRAINT IF EXISTS vehicles_pkey;
ALTER TABLE IF EXISTS ONLY public.vehicle_events DROP CONSTRAINT IF EXISTS vehicle_events_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS ONLY public.receipt_sequence DROP CONSTRAINT IF EXISTS receipt_sequence_pkey;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_receipt_number_key;
ALTER TABLE IF EXISTS ONLY public.payments DROP CONSTRAINT IF EXISTS payments_pkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_pkey;
ALTER TABLE IF EXISTS ONLY public.expenses DROP CONSTRAINT IF EXISTS expenses_expense_number_key;
ALTER TABLE IF EXISTS ONLY public.drivers DROP CONSTRAINT IF EXISTS drivers_pkey;
ALTER TABLE IF EXISTS ONLY public.contracts DROP CONSTRAINT IF EXISTS contracts_pkey;
ALTER TABLE IF EXISTS ONLY public.capital_adjustments DROP CONSTRAINT IF EXISTS capital_adjustments_pkey;
ALTER TABLE IF EXISTS ONLY public.business_settings DROP CONSTRAINT IF EXISTS business_settings_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.app_preferences DROP CONSTRAINT IF EXISTS app_preferences_pkey;
ALTER TABLE IF EXISTS public.vehicles ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.vehicle_events ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.receipt_sequence ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.payments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.expenses ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.drivers ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.contracts ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.capital_adjustments ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.business_settings ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.audit_logs ALTER COLUMN id DROP DEFAULT;
ALTER TABLE IF EXISTS public.app_preferences ALTER COLUMN id DROP DEFAULT;
DROP SEQUENCE IF EXISTS public.vehicles_id_seq;
DROP TABLE IF EXISTS public.vehicles;
DROP SEQUENCE IF EXISTS public.vehicle_events_id_seq;
DROP TABLE IF EXISTS public.vehicle_events;
DROP SEQUENCE IF EXISTS public.users_id_seq;
DROP TABLE IF EXISTS public.users;
DROP SEQUENCE IF EXISTS public.receipt_sequence_id_seq;
DROP TABLE IF EXISTS public.receipt_sequence;
DROP SEQUENCE IF EXISTS public.payments_id_seq;
DROP TABLE IF EXISTS public.payments;
DROP SEQUENCE IF EXISTS public.expenses_id_seq;
DROP TABLE IF EXISTS public.expenses;
DROP SEQUENCE IF EXISTS public.drivers_id_seq;
DROP TABLE IF EXISTS public.drivers;
DROP SEQUENCE IF EXISTS public.contracts_id_seq;
DROP TABLE IF EXISTS public.contracts;
DROP SEQUENCE IF EXISTS public.capital_adjustments_id_seq;
DROP TABLE IF EXISTS public.capital_adjustments;
DROP SEQUENCE IF EXISTS public.business_settings_id_seq;
DROP TABLE IF EXISTS public.business_settings;
DROP SEQUENCE IF EXISTS public.audit_logs_id_seq;
DROP TABLE IF EXISTS public.audit_logs;
DROP SEQUENCE IF EXISTS public.app_preferences_id_seq;
DROP TABLE IF EXISTS public.app_preferences;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_preferences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_preferences (
    id integer NOT NULL,
    pagination_size integer,
    default_report_format character varying(10),
    theme character varying(10),
    session_timeout integer,
    updated_at timestamp without time zone
);


ALTER TABLE public.app_preferences OWNER TO postgres;

--
-- Name: app_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.app_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.app_preferences_id_seq OWNER TO postgres;

--
-- Name: app_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.app_preferences_id_seq OWNED BY public.app_preferences.id;


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.audit_logs (
    id integer NOT NULL,
    user_id integer,
    action character varying(100) NOT NULL,
    entity_type character varying(50),
    entity_id integer,
    old_value text,
    new_value text,
    description text,
    ip_address character varying(45),
    user_agent character varying(255),
    created_at timestamp without time zone
);


ALTER TABLE public.audit_logs OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.audit_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.audit_logs_id_seq OWNER TO postgres;

--
-- Name: audit_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.audit_logs_id_seq OWNED BY public.audit_logs.id;


--
-- Name: business_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.business_settings (
    id integer NOT NULL,
    business_name character varying(200),
    business_logo character varying(255),
    address text,
    phone character varying(200),
    email character varying(120),
    website character varying(200),
    currency character varying(10),
    timezone character varying(50),
    date_format character varying(30),
    updated_at timestamp without time zone
);


ALTER TABLE public.business_settings OWNER TO postgres;

--
-- Name: business_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.business_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.business_settings_id_seq OWNER TO postgres;

--
-- Name: business_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.business_settings_id_seq OWNED BY public.business_settings.id;


--
-- Name: capital_adjustments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.capital_adjustments (
    id integer NOT NULL,
    type character varying(20) NOT NULL,
    amount numeric(15,2) NOT NULL,
    reason text NOT NULL,
    adjustment_date date,
    recorded_by integer,
    created_at timestamp without time zone
);


ALTER TABLE public.capital_adjustments OWNER TO postgres;

--
-- Name: capital_adjustments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.capital_adjustments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.capital_adjustments_id_seq OWNER TO postgres;

--
-- Name: capital_adjustments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.capital_adjustments_id_seq OWNED BY public.capital_adjustments.id;


--
-- Name: contracts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contracts (
    id integer NOT NULL,
    driver_id integer NOT NULL,
    vehicle_id integer NOT NULL,
    purchase_date date,
    delivery_date date,
    start_date date,
    expected_end_date date,
    vehicle_cost numeric(15,2),
    service_costs numeric(15,2),
    extra_expenses numeric(15,2),
    capital numeric(15,2),
    total_payable numeric(15,2),
    years_agreed integer,
    total_weeks integer,
    weekly_amount numeric(15,2),
    weeks_completed integer,
    status character varying(20) NOT NULL,
    notes text,
    created_at timestamp without time zone,
    date_completed timestamp without time zone,
    date_archived timestamp without time zone
);


ALTER TABLE public.contracts OWNER TO postgres;

--
-- Name: contracts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contracts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.contracts_id_seq OWNER TO postgres;

--
-- Name: contracts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contracts_id_seq OWNED BY public.contracts.id;


--
-- Name: drivers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.drivers (
    id integer NOT NULL,
    full_name character varying(120) NOT NULL,
    phone character varying(20) NOT NULL,
    address text,
    photo_path character varying(255),
    national_id character varying(50),
    license_number character varying(50),
    nok_name character varying(120),
    nok_phone character varying(20),
    nok_relationship character varying(50),
    nok_address text,
    guarantor1_name character varying(120),
    guarantor1_phone character varying(20),
    guarantor1_address text,
    guarantor2_name character varying(120),
    guarantor2_phone character varying(20),
    guarantor2_address text,
    witness1_name character varying(120),
    witness1_phone character varying(20),
    witness1_address text,
    witness2_name character varying(120),
    witness2_phone character varying(20),
    witness2_address text,
    status character varying(20) NOT NULL,
    date_registered timestamp without time zone,
    date_archived timestamp without time zone,
    notes text
);


ALTER TABLE public.drivers OWNER TO postgres;

--
-- Name: drivers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.drivers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.drivers_id_seq OWNER TO postgres;

--
-- Name: drivers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.drivers_id_seq OWNED BY public.drivers.id;


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expenses (
    id integer NOT NULL,
    driver_id integer NOT NULL,
    vehicle_id integer,
    contract_id integer,
    expense_number character varying(30),
    title character varying(160) NOT NULL,
    category character varying(40) NOT NULL,
    description text,
    reason text,
    amount numeric(15,2) NOT NULL,
    amount_repaid numeric(15,2),
    expense_date date,
    expense_time time without time zone,
    approved_by character varying(120),
    owner character varying(120),
    receipt_file character varying(255),
    status character varying(20),
    notes text,
    is_archived boolean,
    created_at timestamp without time zone,
    recorded_by integer
);


ALTER TABLE public.expenses OWNER TO postgres;

--
-- Name: expenses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expenses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expenses_id_seq OWNER TO postgres;

--
-- Name: expenses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expenses_id_seq OWNED BY public.expenses.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    contract_id integer NOT NULL,
    driver_id integer NOT NULL,
    amount numeric(15,2) NOT NULL,
    receipt_number character varying(30),
    week_from integer,
    week_to integer,
    week_number integer,
    payment_date date,
    payment_time time without time zone,
    sender character varying(120),
    receiver character varying(120),
    payment_method character varying(20),
    pos_terminal character varying(100),
    bank_name character varying(100),
    reference character varying(100),
    notes text,
    is_archived boolean,
    created_at timestamp without time zone,
    recorded_by integer
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: receipt_sequence; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.receipt_sequence (
    id integer NOT NULL,
    last_seq integer NOT NULL
);


ALTER TABLE public.receipt_sequence OWNER TO postgres;

--
-- Name: receipt_sequence_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.receipt_sequence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.receipt_sequence_id_seq OWNER TO postgres;

--
-- Name: receipt_sequence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.receipt_sequence_id_seq OWNED BY public.receipt_sequence.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(64) NOT NULL,
    display_name character varying(120),
    email character varying(120),
    password_hash character varying(256) NOT NULL,
    role character varying(20),
    is_active boolean,
    profile_photo character varying(255),
    created_at timestamp without time zone,
    last_login timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vehicle_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vehicle_events (
    id integer NOT NULL,
    vehicle_id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    event_date timestamp without time zone NOT NULL,
    created_by character varying(80),
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.vehicle_events OWNER TO postgres;

--
-- Name: vehicle_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vehicle_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vehicle_events_id_seq OWNER TO postgres;

--
-- Name: vehicle_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vehicle_events_id_seq OWNED BY public.vehicle_events.id;


--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vehicles (
    id integer NOT NULL,
    vehicle_number character varying(50) NOT NULL,
    reg_number character varying(50),
    engine_number character varying(100),
    chassis_number character varying(100),
    manufacturer character varying(100),
    model character varying(100),
    year integer,
    color character varying(50),
    purchase_price numeric(15,2),
    purchase_date date,
    delivery_date date,
    current_mileage integer,
    insurance_expiry date,
    road_worthiness_expiry date,
    status character varying(20) NOT NULL,
    date_registered timestamp without time zone,
    date_archived timestamp without time zone,
    notes text
);


ALTER TABLE public.vehicles OWNER TO postgres;

--
-- Name: vehicles_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.vehicles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vehicles_id_seq OWNER TO postgres;

--
-- Name: vehicles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.vehicles_id_seq OWNED BY public.vehicles.id;


--
-- Name: app_preferences id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_preferences ALTER COLUMN id SET DEFAULT nextval('public.app_preferences_id_seq'::regclass);


--
-- Name: audit_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs ALTER COLUMN id SET DEFAULT nextval('public.audit_logs_id_seq'::regclass);


--
-- Name: business_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.business_settings ALTER COLUMN id SET DEFAULT nextval('public.business_settings_id_seq'::regclass);


--
-- Name: capital_adjustments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capital_adjustments ALTER COLUMN id SET DEFAULT nextval('public.capital_adjustments_id_seq'::regclass);


--
-- Name: contracts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contracts ALTER COLUMN id SET DEFAULT nextval('public.contracts_id_seq'::regclass);


--
-- Name: drivers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drivers ALTER COLUMN id SET DEFAULT nextval('public.drivers_id_seq'::regclass);


--
-- Name: expenses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses ALTER COLUMN id SET DEFAULT nextval('public.expenses_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: receipt_sequence id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.receipt_sequence ALTER COLUMN id SET DEFAULT nextval('public.receipt_sequence_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vehicle_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicle_events ALTER COLUMN id SET DEFAULT nextval('public.vehicle_events_id_seq'::regclass);


--
-- Name: vehicles id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles ALTER COLUMN id SET DEFAULT nextval('public.vehicles_id_seq'::regclass);


--
-- Data for Name: app_preferences; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.app_preferences (id, pagination_size, default_report_format, theme, session_timeout, updated_at) FROM stdin;
1	20	pdf	light	480	2026-07-14 14:56:38.526818
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.audit_logs (id, user_id, action, entity_type, entity_id, old_value, new_value, description, ip_address, user_agent, created_at) FROM stdin;
1	1	LOGIN	User	1	\N	\N	LOGIN: owner	127.0.0.1	Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 OPR/133.0.0.0	2026-07-14 14:57:45.006988
2	1	LOGIN	User	1	\N	\N	LOGIN: owner	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:10.504007
3	1	LOGIN	User	1	\N	\N	LOGIN: owner	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:26.952532
4	1	ADD_VEHICLE	Vehicle	1	\N	\N	ADD_VEHICLE: LGA-001-AA	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:26.993622
5	1	CREATE_DRIVER	Driver	1	\N	\N	CREATE_DRIVER driver: Emeka Okonkwo	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:27.048169
6	1	LOGIN	User	1	\N	\N	LOGIN: owner	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.063294
7	1	CREATE_CONTRACT	Contract	1	\N	\N	Contract for Emeka Okonkwo on LGA-001-AA. Total payable: ₦12,000,000	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.198079
8	1	RECORD_PAYMENT	Payment	1	\N	\N	RECORD_PAYMENT: receipt THMS-20260714-000001 ₦76,923 for Emeka Okonkwo — contract #1. Weeks: Part of Week 1	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.284254
9	1	RECORD_PAYMENT	Payment	2	\N	\N	RECORD_PAYMENT: receipt THMS-20260714-000002 ₦76,923 for Emeka Okonkwo — contract #1. Weeks: Week 1	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.333747
10	1	RECORD_PAYMENT	Payment	3	\N	\N	RECORD_PAYMENT: receipt THMS-20260714-000003 ₦76,923 for Emeka Okonkwo — contract #1. Weeks: Week 2	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.366735
11	1	ADD_EXPENSE	Expense	1	\N	\N	ADD_EXPENSE: EXP-202607-00001 — Engine oil change and filter replacement ₦45,000 driver=Emeka Okonkwo contract=#1. Category: Servicing. Contract #1 outstanding balance updated.	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.395096
12	1	VIEW_RECEIPT	Payment	1	\N	\N	VIEW_RECEIPT: receipt THMS-20260714-000001 ₦76,923 for Emeka Okonkwo — contract #1. Receipt viewed in browser.	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.441637
13	1	PRINT_RECEIPT	Payment	1	\N	\N	PRINT_RECEIPT: receipt THMS-20260714-000001 ₦76,923 for Emeka Okonkwo — contract #1. PDF receipt downloaded.	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:57.587606
14	1	COMPLETE_CONTRACT	Contract	1	\N	\N	Marked complete by owner. Total paid: ₦230,769	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:58.118189
15	1	ARCHIVE_CONTRACT	Contract	1	\N	\N	ARCHIVE_CONTRACT: contract #1	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:58.147332
16	1	CREATE_DRIVER	Driver	2	\N	\N	CREATE_DRIVER driver: Restore Test Driver	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:58.185913
17	1	ARCHIVE_DRIVER	Driver	2	\N	\N	ARCHIVE_DRIVER driver: Restore Test Driver	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:58.213059
18	1	RESTORE_DRIVER	Driver	2	\N	\N	RESTORE_DRIVER driver: Restore Test Driver	127.0.0.1	python-requests/2.34.2	2026-07-14 15:03:58.243841
\.


--
-- Data for Name: business_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.business_settings (id, business_name, business_logo, address, phone, email, website, currency, timezone, date_format, updated_at) FROM stdin;
1	Transport Hire Management System	\N	\N	\N	\N	\N	₦	Africa/Lagos	%d %b %Y	2026-07-14 14:56:38.520458
\.


--
-- Data for Name: capital_adjustments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.capital_adjustments (id, type, amount, reason, adjustment_date, recorded_by, created_at) FROM stdin;
\.


--
-- Data for Name: contracts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contracts (id, driver_id, vehicle_id, purchase_date, delivery_date, start_date, expected_end_date, vehicle_cost, service_costs, extra_expenses, capital, total_payable, years_agreed, total_weeks, weekly_amount, weeks_completed, status, notes, created_at, date_completed, date_archived) FROM stdin;
1	1	1	2022-01-15	2024-01-02	2024-01-01	2026-12-28	8500000.00	150000.00	50000.00	8700000.00	12000000.00	3	156	76923.08	156	archived	Standard 3-year hire-purchase agreement	2026-07-14 15:03:57.196147	2026-07-14 15:03:58.111803	2026-07-14 15:03:58.147047
\.


--
-- Data for Name: drivers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.drivers (id, full_name, phone, address, photo_path, national_id, license_number, nok_name, nok_phone, nok_relationship, nok_address, guarantor1_name, guarantor1_phone, guarantor1_address, guarantor2_name, guarantor2_phone, guarantor2_address, witness1_name, witness1_phone, witness1_address, witness2_name, witness2_phone, witness2_address, status, date_registered, date_archived, notes) FROM stdin;
1	Emeka Okonkwo	08012345678	14 Adeola Street, Lagos	\N	NIN-123456789	LSC-2022-007	Mrs. Grace Okonkwo	08098765432	Wife	\N	Mr. Chukwuemeka Eze	07011223344	22 Broad Street, Lagos	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2026-07-14 15:03:27.047098	\N	\N
2	Restore Test Driver	07099887766	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	active	2026-07-14 15:03:58.184951	\N	\N
\.


--
-- Data for Name: expenses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.expenses (id, driver_id, vehicle_id, contract_id, expense_number, title, category, description, reason, amount, amount_repaid, expense_date, expense_time, approved_by, owner, receipt_file, status, notes, is_archived, created_at, recorded_by) FROM stdin;
1	1	1	1	EXP-202607-00001	Engine oil change and filter replacement	servicing	Routine maintenance at 50,000km	Routine maintenance at 50,000km	45000.00	0.00	2024-02-10	\N	Owner	\N	\N	outstanding	\N	f	2026-07-14 15:03:57.391488	1
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, contract_id, driver_id, amount, receipt_number, week_from, week_to, week_number, payment_date, payment_time, sender, receiver, payment_method, pos_terminal, bank_name, reference, notes, is_archived, created_at, recorded_by) FROM stdin;
1	1	1	76923.00	THMS-20260714-000001	1	0	1	2024-01-07	\N	\N	\N	cash	\N	\N	REF-2024-001	Week 1 payment	f	2026-07-14 15:03:57.277455	1
2	1	1	76923.00	THMS-20260714-000002	1	1	1	2024-02-07	\N	\N	\N	transfer	\N	\N	REF-2024-002	Week 2 payment	f	2026-07-14 15:03:57.330202	1
3	1	1	76923.00	THMS-20260714-000003	2	2	2	2024-03-07	\N	\N	\N	cash	\N	\N	REF-2024-003	Week 3 payment	f	2026-07-14 15:03:57.363367	1
\.


--
-- Data for Name: receipt_sequence; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.receipt_sequence (id, last_seq) FROM stdin;
1	3
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, display_name, email, password_hash, role, is_active, profile_photo, created_at, last_login) FROM stdin;
2	developer	\N	dev@thms.local	scrypt:32768:8:1$coNSVhe2D5smgU0b$69450e69aefbb0dbbcf23c8e89625f606c08a2970bb7f90d95b23166aa30eeed3a99df30a3641359e6fc3a7fd16ffc2525400c43be72746aa5ed90dfda8f61f3	developer	t	\N	2026-07-14 14:56:38.448678	\N
1	owner	\N	owner@thms.local	scrypt:32768:8:1$R7K23EuwYq6G6dfR$e012d3f435d89b8923fe227b99a66637a5bc0b9dd3bcab3c892f23630a2263bdcfdc2dc67b100f4f5ec85a636151cfaeaea1fd0875a4cc2778a5c59364c42b4a	owner	t	\N	2026-07-14 14:56:38.448672	2026-07-14 15:03:57.059264
\.


--
-- Data for Name: vehicle_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vehicle_events (id, vehicle_id, event_type, title, description, event_date, created_by, created_at) FROM stdin;
1	1	registered	Vehicle LGA-001-AA registered in the system	Added by owner.	2026-07-14 15:03:26.993188	owner	2026-07-14 15:03:26.994822
2	1	assigned	Assigned to Emeka Okonkwo — Contract #1	Weekly payment: ₦76,923.08 over 156 weeks.	2026-07-14 15:03:57.197634	owner	2026-07-14 15:03:57.200381
3	1	contract_completed	Contract #1 completed — Emeka Okonkwo	All 156 weeks paid. Vehicle returned to fleet.	2026-07-14 15:03:58.115039	owner	2026-07-14 15:03:58.116068
4	1	returned	Vehicle returned by Emeka Okonkwo	Driver completed all hire-purchase payments.	2026-07-14 15:03:58.115113	owner	2026-07-14 15:03:58.11607
\.


--
-- Data for Name: vehicles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.vehicles (id, vehicle_number, reg_number, engine_number, chassis_number, manufacturer, model, year, color, purchase_price, purchase_date, delivery_date, current_mileage, insurance_expiry, road_worthiness_expiry, status, date_registered, date_archived, notes) FROM stdin;
1	LGA-001-AA	\N	\N	\N	Toyota	Hiace Bus	2022	White	8500000.00	2022-01-15	\N	\N	\N	\N	available	2026-07-14 15:03:26.991942	\N	Test vehicle for simulation
\.


--
-- Name: app_preferences_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.app_preferences_id_seq', 1, false);


--
-- Name: audit_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.audit_logs_id_seq', 18, true);


--
-- Name: business_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.business_settings_id_seq', 1, false);


--
-- Name: capital_adjustments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.capital_adjustments_id_seq', 1, false);


--
-- Name: contracts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contracts_id_seq', 1, true);


--
-- Name: drivers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.drivers_id_seq', 2, true);


--
-- Name: expenses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.expenses_id_seq', 1, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 3, true);


--
-- Name: receipt_sequence_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.receipt_sequence_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 2, true);


--
-- Name: vehicle_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vehicle_events_id_seq', 4, true);


--
-- Name: vehicles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.vehicles_id_seq', 1, true);


--
-- Name: app_preferences app_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_preferences
    ADD CONSTRAINT app_preferences_pkey PRIMARY KEY (id);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: business_settings business_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.business_settings
    ADD CONSTRAINT business_settings_pkey PRIMARY KEY (id);


--
-- Name: capital_adjustments capital_adjustments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capital_adjustments
    ADD CONSTRAINT capital_adjustments_pkey PRIMARY KEY (id);


--
-- Name: contracts contracts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_pkey PRIMARY KEY (id);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (id);


--
-- Name: expenses expenses_expense_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_expense_number_key UNIQUE (expense_number);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: payments payments_receipt_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_receipt_number_key UNIQUE (receipt_number);


--
-- Name: receipt_sequence receipt_sequence_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.receipt_sequence
    ADD CONSTRAINT receipt_sequence_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: vehicle_events vehicle_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicle_events
    ADD CONSTRAINT vehicle_events_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (id);


--
-- Name: vehicles vehicles_reg_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_reg_number_key UNIQUE (reg_number);


--
-- Name: vehicles vehicles_vehicle_number_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_vehicle_number_key UNIQUE (vehicle_number);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: audit_logs audit_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: capital_adjustments capital_adjustments_recorded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.capital_adjustments
    ADD CONSTRAINT capital_adjustments_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id);


--
-- Name: contracts contracts_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(id);


--
-- Name: contracts contracts_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contracts
    ADD CONSTRAINT contracts_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id);


--
-- Name: expenses expenses_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id);


--
-- Name: expenses expenses_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(id);


--
-- Name: expenses expenses_recorded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id);


--
-- Name: expenses expenses_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id);


--
-- Name: payments payments_contract_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_contract_id_fkey FOREIGN KEY (contract_id) REFERENCES public.contracts(id);


--
-- Name: payments payments_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(id);


--
-- Name: payments payments_recorded_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_recorded_by_fkey FOREIGN KEY (recorded_by) REFERENCES public.users(id);


--
-- Name: vehicle_events vehicle_events_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vehicle_events
    ADD CONSTRAINT vehicle_events_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict a6MICHVm7UZR3AWCNVtklyuVmFSqmkn96QEyQFuHxorhVadnQ1ZY49OTRiLNv6d

