-- sessions: één rij per leersessie
create table sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users not null,
  topic text not null,           -- 'linux' of 'netwerk'
  subtopic text,                 -- bijv. 'processen_performance', 'tcp_fundamenten'
  total_score integer default 0,
  max_score integer default 0,
  created_at timestamptz default now()
);

-- answers: één rij per vraag binnen een sessie
create table answers (
  id uuid primary key default gen_random_uuid(),
  session_id uuid references sessions on delete cascade not null,
  question text not null,
  question_type text not null,   -- 'scenario' of 'command'
  subtopic text not null,
  user_answer text not null,
  feedback text not null,
  score integer not null,        -- 0-10
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

-- Row Level Security: alleen de eigenaar ziet zijn eigen data
alter table sessions enable row level security;
alter table answers enable row level security;
alter table topic_scores enable row level security;

create policy "own data only" on sessions
  for all using (auth.uid() = user_id);

create policy "own data only" on topic_scores
  for all using (auth.uid() = user_id);

create policy "own data only" on answers
  for all using (
    session_id in (select id from sessions where user_id = auth.uid())
  );
