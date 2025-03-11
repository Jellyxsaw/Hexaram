CREATE TABLE summoners (
    id SERIAL PRIMARY KEY,
    puuid VARCHAR(100) NOT NULL UNIQUE,
    summoner_name VARCHAR(100),
    riot_id_game_name VARCHAR(100),
    riot_id_tagline VARCHAR(50),
    is_searched BOOLEAN DEFAULT FALSE,
    last_searched TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    is_searched_summoners BOOLEAN DEFAULT FALSE,
    match_id VARCHAR(50) NOT NULL UNIQUE,
    game_mode VARCHAR(50),
    game_type VARCHAR(50),
    game_version VARCHAR(50),
    map_id INT,
    queue_id INT,
    platform_id VARCHAR(20),
    tournament_code VARCHAR(50),
    game_name VARCHAR(100),
    game_creation TIMESTAMP,
    game_duration INT,
    game_start_timestamp TIMESTAMP,
    game_end_timestamp TIMESTAMP,
    match_data JSONB,   -- 儲存完整清洗後的對局 JSON 資料
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE model_data (
    match_data_id TEXT PRIMARY KEY,
    win_champions JSONB,
    lose_champions JSONB,
    gold_diff INTEGER,
    win_inhibitor INTEGER,
    lose_inhibitor INTEGER,
    lose_tower INTEGER,
    game_duration INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE champion_list (
    id SERIAL PRIMARY KEY,     -- 儲存英雄的唯一識別碼 (例如 "Aatrox")
    hero_name VARCHAR(100) NOT NULL,  -- 儲存英雄名稱
    hero_tw_name VARCHAR(100) NOT NULL,  -- 儲存英雄名稱
    key INT NOT NULL UNIQUE,       -- 儲存英雄的 key 值 (例如 "266")
    created_at TIMESTAMP DEFAULT NOW()
);


CREATE TABLE model_matches (
    id SERIAL PRIMARY KEY,
    is_searched_summoners BOOLEAN DEFAULT FALSE,
    match_id VARCHAR(50) NOT NULL UNIQUE,
    game_mode VARCHAR(50),
    game_type VARCHAR(50),
    game_version VARCHAR(50),
    map_id INT,
    queue_id INT,
    platform_id VARCHAR(20),
    tournament_code VARCHAR(50),
    game_name VARCHAR(100),
    game_creation TIMESTAMP,
    game_duration INT,
    game_start_timestamp TIMESTAMP,
    game_end_timestamp TIMESTAMP,
    match_data JSONB,   -- 原本的資料
    extract_data JSONB, -- 清洗的資料
    created_at TIMESTAMP DEFAULT NOW()
);