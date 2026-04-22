-- sessions
create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  topic text not null,
  subtopic text,
  level text not null default 'basis',  -- 'basis' of 'gemiddeld'
  total_score integer default 0,
  max_score integer default 0,
  created_at timestamptz default now()
);

-- answers
create table answers (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references sessions on delete cascade not null,
  question text not null,
  question_type text not null,
  subtopic text not null,
  user_answer text not null,
  feedback text not null,
  score integer not null,
  interview_taal text default '',
  pi_commando text default '',
  grammar_score    integer,
  vocabulary_score integer,
  structure_score  integer,
  fluency_score    integer,
  english_tips     text default '',
  created_at timestamptz default now()
);

-- topic_scores: cumulatieve score per subtopic
create table topic_scores (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  subtopic text not null,
  correct_answers integer default 0,
  total_answers integer default 0,
  updated_at timestamptz default now(),
  unique(user_id, subtopic)
);

-- topic_levels: huidig niveau per topic (basis/gemiddeld)
create table topic_levels (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  topic text not null,
  level text not null default 'basis',
  updated_at timestamptz default now(),
  unique(user_id, topic)
);

-- Row Level Security
alter table sessions enable row level security;
alter table answers enable row level security;
alter table topic_scores enable row level security;
alter table topic_levels enable row level security;

create policy "own data only" on sessions for all using (auth.uid() = user_id);
create policy "own data only" on topic_scores for all using (auth.uid() = user_id);
create policy "own data only" on topic_levels for all using (auth.uid() = user_id);
create policy "own data only" on answers for all using (
  session_id in (select id from sessions where user_id = auth.uid())
);
