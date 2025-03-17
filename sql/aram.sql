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

-- 英雄基本資料表 (適用於 PostgreSQL)
CREATE TABLE champions (
    champion_id VARCHAR(20) PRIMARY KEY,    -- 英雄ID (例如: Ashe)
    champion_name VARCHAR(50) NOT NULL,     -- 英雄名稱 (例如: Ashe 艾希)
    champion_tw_name VARCHAR(50) NOT NULL,  -- 英雄中文名稱 (例如: 艾希)
    champion_type VARCHAR(20) NOT NULL,     -- 英雄類型 (例如: 射手)
    champion_difficulty INT NOT NULL,       -- 難度 (1-3)
    recommended_position VARCHAR(50) NOT NULL, -- 推薦位置
    key INT NOT NULL,                       -- Riot 定義的英雄 key
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 英雄統計資料表
CREATE TABLE champion_stats (
    champion_id VARCHAR(20) PRIMARY KEY REFERENCES champions(champion_id),
    win_rate FLOAT NOT NULL,               -- 勝率
    pick_rate FLOAT NOT NULL,              -- 選用率
    ban_rate FLOAT NOT NULL,               -- 禁用率
    avg_kills FLOAT NOT NULL,              -- 平均擊殺
    avg_deaths FLOAT NOT NULL,             -- 平均死亡
    avg_assists FLOAT NOT NULL,            -- 平均助攻
    kda_ratio FLOAT NOT NULL,              -- KDA比率
    avg_damage FLOAT NOT NULL,             -- 平均傷害
    avg_damage_percentage FLOAT NOT NULL,  -- 傷害佔比
    avg_healing FLOAT NOT NULL,            -- 平均治療
    avg_healing_percentage FLOAT NOT NULL, -- 治療佔比
    avg_damage_taken FLOAT NOT NULL,       -- 平均承受傷害
    avg_damage_taken_percentage FLOAT NOT NULL, -- 承受傷害佔比
    tier VARCHAR(10) NOT NULL,             -- 等級 (S, A, B, C, D)
    rank INT NOT NULL,                     -- 排名
    sample_size INT NOT NULL,              -- 樣本數
    version VARCHAR(10) NOT NULL,          -- 版本
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_champion_stats_winrate ON champion_stats(win_rate DESC);
CREATE INDEX idx_champion_stats_pickrate ON champion_stats(pick_rate DESC);
CREATE INDEX idx_champion_stats_kda ON champion_stats(kda_ratio DESC);
CREATE INDEX idx_champion_stats_tier ON champion_stats(tier);

-- 英雄版本趨勢表
CREATE TABLE champion_trends (
    id SERIAL PRIMARY KEY,
    champion_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),
    version VARCHAR(10) NOT NULL,           -- 遊戲版本
    win_rate FLOAT NOT NULL,                -- 該版本勝率
    pick_rate FLOAT NOT NULL,               -- 該版本選用率
    sample_size INT NOT NULL,               -- 該版本樣本數
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (champion_id, version)
);
CREATE INDEX idx_champion_trends_champion_version ON champion_trends(champion_id, version);

-- 英雄符文構建表
CREATE TABLE champion_runes (
    id SERIAL PRIMARY KEY,
    champion_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),
    primary_path VARCHAR(20) NOT NULL,      -- 主系
    primary_rune VARCHAR(30) NOT NULL,      -- 主系符文
    secondary_path VARCHAR(20) NOT NULL,    -- 副系
    rune_options TEXT NOT NULL,             -- 所有符文選擇 (JSON格式)
    shard_options TEXT NOT NULL,            -- 符文碎片 (JSON格式)
    win_rate FLOAT NOT NULL,                -- 此配置勝率
    pick_rate FLOAT NOT NULL,               -- 此配置選用率
    sample_size INT NOT NULL,               -- 此配置樣本數
    version VARCHAR(10) NOT NULL,           -- 版本
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_champion_runes_winrate ON champion_runes(champion_id, win_rate DESC);

-- 英雄裝備構建表
CREATE TABLE champion_builds (
    id SERIAL PRIMARY KEY,
    champion_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),
    starting_items TEXT NOT NULL,           -- 起始裝備 (JSON格式)
    core_items TEXT NOT NULL,               -- 核心裝備 (JSON格式)
    optional_items TEXT NOT NULL,           -- 可選裝備 (JSON格式)
    win_rate FLOAT NOT NULL,                -- 此配置勝率
    pick_rate FLOAT NOT NULL,               -- 此配置選用率
    sample_size INT NOT NULL,               -- 此配置樣本數
    version VARCHAR(10) NOT NULL,           -- 版本
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_champion_builds_winrate ON champion_builds(champion_id, win_rate DESC);

-- 英雄技能加點表
CREATE TABLE champion_skills (
    id SERIAL PRIMARY KEY,
    champion_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),
    skill_order VARCHAR(10) NOT NULL,       -- 技能加點順序 (例如: R>Q>W>E)
    first_skill CHAR(1) NOT NULL,           -- 首選技能
    win_rate FLOAT NOT NULL,                -- 此配置勝率
    pick_rate FLOAT NOT NULL,               -- 此配置選用率
    sample_size INT NOT NULL,               -- 此配置樣本數
    version VARCHAR(10) NOT NULL,           -- 版本
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_champion_skills_winrate ON champion_skills(champion_id, win_rate DESC);

-- 英雄對英雄的對位統計表
CREATE TABLE champion_matchups (
    id SERIAL PRIMARY KEY,
    champion_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),   -- 本場英雄
    opponent_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),   -- 對位英雄
    win_rate FLOAT NOT NULL,                -- 對位勝率
    sample_size INT NOT NULL,               -- 對位樣本數
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (champion_id, opponent_id)
);
CREATE INDEX idx_champion_matchups_opponents ON champion_matchups(champion_id, opponent_id);

-- 隊伍協同統計表
CREATE TABLE team_synergies (
    id SERIAL PRIMARY KEY,
    champion1_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),  -- 英雄1
    champion2_id VARCHAR(20) NOT NULL REFERENCES champions(champion_id),  -- 英雄2
    win_rate FLOAT NOT NULL,                -- 一起出場時勝率
    synergy_score FLOAT NOT NULL,           -- 協同分數
    sample_size INT NOT NULL,               -- 樣本數
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (champion1_id, champion2_id)
);
CREATE INDEX idx_team_synergies_pair ON team_synergies(champion1_id, champion2_id);

-- 為符文編號與名稱建立對應表
CREATE TABLE rune_definitions (
    rune_id INT PRIMARY KEY,
    rune_name VARCHAR(50) NOT NULL,
    rune_path VARCHAR(20) NOT NULL,
    rune_slot INT NOT NULL,
    rune_description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_rune_definitions_path_slot ON rune_definitions(rune_path, rune_slot);

-- 為物品編號與名稱建立對應表
CREATE TABLE item_definitions (
    item_id INT PRIMARY KEY,
    item_name VARCHAR(50) NOT NULL,
    item_type VARCHAR(20) NOT NULL,
    item_description TEXT,
    item_cost INT NOT NULL,
    is_mythic BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_item_definitions_type ON item_definitions(item_type);

-- 建立參考資料更新日誌表
CREATE TABLE data_update_logs (
    id SERIAL PRIMARY KEY,
    update_type VARCHAR(20) NOT NULL,        -- 更新類型
    version VARCHAR(10) NOT NULL,            -- 更新版本
    records_processed INT NOT NULL,          -- 處理記錄數
    update_status VARCHAR(20) NOT NULL,      -- 更新狀態
    start_time TIMESTAMP NOT NULL,           -- 開始時間
    end_time TIMESTAMP NOT NULL,             -- 結束時間
    error_message TEXT,                      -- 錯誤訊息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 建立API請求日誌表
CREATE TABLE api_request_logs (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(100) NOT NULL,          -- API端點
    ip_address VARCHAR(50),                  -- IP地址
    request_params TEXT,                     -- 請求參數
    response_status INT,                     -- 回應狀態碼
    execution_time FLOAT,                    -- 執行時間(秒)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_request_logs_endpoint ON api_request_logs(endpoint);
CREATE INDEX idx_api_request_logs_created_at ON api_request_logs(created_at);

-- 建立用戶授權表
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(64) NOT NULL UNIQUE,     -- API密鑰
    user_name VARCHAR(50) NOT NULL,          -- 用戶名稱
    email VARCHAR(100),                      -- 電子郵件
    rate_limit INT DEFAULT 100,              -- 每日請求限制
    is_active BOOLEAN DEFAULT TRUE,          -- 是否啟用
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_api_keys_user ON api_keys(user_name);

-- 讀取權限視圖 (方便前端查詢沒有敏感資訊)
CREATE VIEW v_champion_summary AS
SELECT
    c.champion_id,
    c.champion_name,
    c.champion_tw_name,
    c.champion_type,
    c.champion_difficulty,
    c.recommended_position,
    c.key,
    s.win_rate,
    s.pick_rate,
    s.ban_rate,
    s.avg_kills,
    s.avg_deaths,
    s.avg_assists,
    s.kda_ratio,
    s.tier,
    s.rank
FROM
    champions c
LEFT JOIN
    champion_stats s ON c.champion_id = s.champion_id;