create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  created_at timestamptz not null default now()
);

create table if not exists batches (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  status text not null, -- pending|running|done|failed
  field text,
  location text,
  job_type text,
  created_at timestamptz not null default now()
);

create index if not exists idx_batches_user_created on batches(user_id, created_at desc);

create table if not exists applications (
  id uuid primary key default gen_random_uuid(),
  batch_id uuid not null references batches(id) on delete cascade,
  job_url text not null,
  company text,
  title text,
  recruiter_email text,
  status text not null, -- pending|sent|failed
  error text,
  created_at timestamptz not null default now(),
  unique(batch_id, job_url)
);

 reminder: no PII in sample data; use mock jobs in n8n.