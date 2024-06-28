create schema if not exists stage;
create schema if not exists dds;

create table if not exists stage.croud_company (
    id integer generated always as identity not null,
    payload jsonb not null,
    created_at timestamp without time zone default now() not null

);

create table if not exists dds.borrowers (
    id uuid not null primary key,
    short_name varchar not null,
    full_name varchar not null,
    model_bucket varchar,
    total_main_debt_to_investor double precision,
    created_at timestamp without time zone default now() not null,
    updated_at timestamp without time zone default now() not null

);

create table if not exists dds.loans (
    id uuid not null primary key,
    borrower uuid not null         constraint loans_borrowers__fk references dds.borrowers,
    number integer,
    funds_started_at timestamp without time zone not null,
    status_id varchar not null,
    loan_raising_due timestamp without time zone not null,
    loan_amount double precision not null,
    loan_manual_invest_max_amount double precision not null,
    loan_term int2 not null,
    loan_rate float not null,
    loan_type varchar,
    mm_refunded_loans_count int,
    is_manual_invest boolean not null,
    is_manual_invest_explicit boolean not null,
    is_collateral_product boolean not null,
    autoinvest_start_at timestamp without time zone not null,
    schedule_type varchar not null,
    raised_amount double precision,
    promo_params jsonb,
    irr float,
    rating varchar(5),
    is_potok_finance_borrower boolean not null,
    is_potok_holding_borrower boolean not null,
    borrower_have_other_investments boolean not null,
    refunded_loans_count_now integer,
    -- my_investments
    my_investment_amount double precision not null,
    pif_reserved_amount double precision not null,
    pif_invested_amount double precision not null ,
    pif_investments boolean not null
);

create table if not exists dds.rising_progress (
    id uuid not null constraint rising_progress_loans__fk references dds.loans,
    raised_amount double precision not null,
    created_at timestamp without time zone not null default now()
)