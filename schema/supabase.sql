-- Execute in your PRIVATE Supabase project. No client-facing access policies.
create table if not exists public.sog_prices (
 id bigint generated always as identity primary key,
 event_id text not null, game_start_utc timestamptz not null,
 player_name text not null, line numeric not null,
 side text not null check (side in ('Over','Under')),
 book text not null check (book in ('draftkings','fanduel')),
 american_odds integer not null, price_captured_at_utc timestamptz not null,
 book_last_update_utc timestamptz, source text not null,
 unique(event_id,player_name,line,side,book,price_captured_at_utc)
);
create table if not exists public.sog_forecasts (
 id bigint generated always as identity primary key,
 event_id text not null, game_start_utc timestamptz not null,
 player_name text not null, line numeric not null,
 projected_sog numeric, prob_over numeric not null check(prob_over between 0 and 1),
 forecast_created_utc timestamptz not null,
 model_version text not null, model_status text not null default 'research',
 data_verified boolean not null default false,
 unique(event_id,player_name,line,model_version,forecast_created_utc)
);
create table if not exists public.sog_refresh_runs (
 id bigint generated always as identity primary key,
 run_at_utc timestamptz not null default now(),
 kind text not null, success boolean not null,
 message text not null, quotes int not null default 0
);
alter table public.sog_prices enable row level security;
alter table public.sog_forecasts enable row level security;
alter table public.sog_refresh_runs enable row level security;
-- No SELECT/INSERT/UPDATE/DELETE policies for anon or authenticated clients.
-- Backend only: protected server uses service-role key. Never embed it in HTML or a mobile app.
