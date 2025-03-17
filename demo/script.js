// API 基礎 URL
const API_BASE_URL = 'http://localhost:5000/api';

// 全域變數
let currentPage = 'champions';
let currentChampionsPage = 1;
let totalChampionsPages = 1;
let currentType = '全部';
let currentSort = '勝率';

// 工具函數
// ====================

// 顯示/隱藏載入指示器
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

// 顯示/隱藏模態框
function showModal() {
    document.getElementById('champion-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function hideModal() {
    document.getElementById('champion-modal').classList.add('hidden');
    document.body.style.overflow = '';
}

// 數據轉換工具函數
function getChampionDifficulty(difficulty) {
    switch (difficulty) {
        case 1: return '簡單';
        case 2: return '中等';
        case 3: return '困難';
        default: return '中等';
    }
}

function getRunePath(pathId) {
    const paths = {
        '8000': '精密',
        '8100': '主宰',
        '8200': '巫術',
        '8300': '靈感',
        '8400': '堅決'
    };
    return paths[pathId] || pathId;
}

function getRuneName(runeId) {
    // 理想情況下，這裡應該有一個完整的符文映射表
    return runeId;
}

function getShardName(shardId) {
    const shards = {
        '5001': '生命值',
        '5002': '護甲',
        '5003': '魔法抗性',
        '5005': '攻擊速度',
        '5007': '技能急速',
        '5008': '適應性能力'
    };
    return shards[shardId] || shardId;
}

function getItemName(itemId) {
    // 理想情況下，這裡應該有一個完整的物品映射表
    return `物品 ${itemId}`;
}

function getChampionKey(championId) {
    // 理想情況下，這裡應該有一個完整的英雄ID到Key的映射表
    const commonChampions = {
        'Aatrox': '266',
        'Ahri': '103',
        'Akali': '84',
        'Amumu': '32',
        'Annie': '1',
        'Ashe': '22',
        'Blitzcrank': '53',
        'Brand': '63',
        'Caitlyn': '51',
        'Darius': '122',
        'Ezreal': '81',
        'Jinx': '222',
        'Kaisa': '145',
        'Katarina': '55',
        'LeeSin': '64',
        'Lux': '99',
        'MasterYi': '11',
        'MissFortune': '21',
        'Pyke': '555',
        'Sona': '37',
        'Soraka': '16',
        'Teemo': '17',
        'Thresh': '412',
        'Vayne': '67',
        'Yasuo': '157',
        'Yuumi': '350',
        'Zed': '238',
        'Ziggs': '115'
    };

    return commonChampions[championId] || '1'; // 預設值改為 Annie
}

// 數據載入函數
// ====================

// 載入版本信息
function loadVersionInfo() {
    fetch(`${API_BASE_URL}/version`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('api-version').textContent = data.api_version;
            document.getElementById('last-updated').textContent = data.last_updated;
            document.getElementById('total-samples').textContent = data.total_samples.toLocaleString();
        })
        .catch(error => console.error('載入版本信息錯誤:', error));
}

// 載入英雄列表
function loadChampions(page = 1, type = '全部', sort = '勝率') {
    showLoading();

    // 使用模擬資料，將在實際環境中替換為真正的API請求
    // 實際環境解除這段註解
    fetch(`${API_BASE_URL}/champions?page=${page}&limit=12&type=${type}&sort=${sort}`)
        .then(response => response.json())
        .then(data => {
            renderChampionsList(data.champions);
            renderPagination(data.pagination);
            currentChampionsPage = data.pagination.current_page;
            totalChampionsPages = data.pagination.total_pages;
            hideLoading();
        })
        .catch(error => {
            console.error('載入英雄列表錯誤:', error);
            hideLoading();
        });
}

// 載入英雄詳情
function loadChampionDetail(championId) {
    showLoading();

    fetch(`${API_BASE_URL}/champions/${championId}`)
        .then(response => response.json())
        .then(data => {
            renderChampionDetail(data);
            showModal();
            hideLoading();
        })
        .catch(error => {
            console.error('載入英雄詳情錯誤:', error);
            hideLoading();
        });
}

// 載入梯隊排名
function loadTierList(type = '全部') {
    showLoading();

    fetch(`${API_BASE_URL}/tier-list${type !== '全部' ? `?type=${type}` : ''}`)
        .then(response => response.json())
        .then(data => {
            renderTierList(data.tier_list);
            hideLoading();
        })
        .catch(error => {
            console.error('載入梯隊排名錯誤:', error);
            hideLoading();
        });
}

// 載入協同矩陣
function loadSynergyMatrix() {
    showLoading();

    fetch(`${API_BASE_URL}/synergy-matrix?limit=20`)
        .then(response => response.json())
        .then(data => {
            renderSynergyMatrix(data);
            hideLoading();
        })
        .catch(error => {
            console.error('載入協同矩陣錯誤:', error);
            hideLoading();
        });
}

// 載入對位矩陣
function loadMatchupMatrix() {
    showLoading();

    fetch(`${API_BASE_URL}/matchup-matrix?limit=20`)
        .then(response => response.json())
        .then(data => {
            renderMatchupMatrix(data);
            hideLoading();
        })
        .catch(error => {
            console.error('載入對位矩陣錯誤:', error);
            hideLoading();
        });
}

// 搜索英雄
function searchChampions(query) {
    if (!query || query.length < 1) {
        document.getElementById('search-results').classList.add('hidden');
        return;
    }

    fetch(`${API_BASE_URL}/champion-search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            renderSearchResults(data.results);
        })
        .catch(error => {
            console.error('搜索英雄錯誤:', error);
        });
}

// 頁面渲染函數
// ====================

// 渲染英雄列表
function renderChampionsList(champions) {
    const content = document.getElementById('page-content');

    if (!champions || champions.length === 0) {
        content.innerHTML = '<div class="text-center py-8 text-gray-500">沒有找到英雄數據</div>';
        return;
    }

    let html = '<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">';

    champions.forEach(champion => {
        const tierClass = `tier-${champion.tier.toLowerCase()}`;

        html += `
        <div class="champion-card bg-white rounded-lg shadow-md overflow-hidden cursor-pointer" data-id="${champion.championId}">
            <div class="h-40 bg-gray-200 relative">
                <img src="https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${champion.key}_0.jpg" alt="${champion.name}" class="w-full h-full object-cover">
                <div class="absolute top-0 right-0 ${tierClass} text-sm font-bold px-2 py-1 rounded-bl-lg">
                    ${champion.tier} 級
                </div>
            </div>
            <div class="p-4">
                <h3 class="font-bold text-lg mb-2">${champion.name}</h3>
                <div class="flex justify-between text-sm">
                    <span>勝率: <span class="font-semibold text-green-600">${champion.winRate}%</span></span>
                    <span>選用率: <span class="font-semibold text-blue-600">${champion.pickRate}%</span></span>
                </div>
                <div class="mt-2 text-sm">
                    <span>KDA: <span class="font-semibold">${champion.kda} (${champion.kdaRatio})</span></span>
                </div>
            </div>
        </div>
        `;
    });

    html += '</div>';
    content.innerHTML = html;

    // 添加點擊事件
    document.querySelectorAll('.champion-card').forEach(card => {
        card.addEventListener('click', () => {
            const championId = card.getAttribute('data-id');
            loadChampionDetail(championId);
        });
    });
}

// 渲染分頁
function renderPagination(pagination) {
    const paginationElement = document.getElementById('pagination');

    if (!pagination) {
        paginationElement.innerHTML = '';
        return;
    }

    const { current_page, total_pages } = pagination;

    if (total_pages <= 1) {
        paginationElement.innerHTML = '';
        return;
    }

    let html = '';

    // 上一頁按鈕
    html += `
    <button class="px-3 py-1 rounded-md border ${current_page === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white hover:bg-gray-100'}"
            ${current_page === 1 ? 'disabled' : ''}
            data-page="${current_page - 1}">
        <i class="fas fa-chevron-left"></i>
    </button>
    `;

    // 頁碼
    for (let i = 1; i <= total_pages; i++) {
        // 顯示當前頁和前後兩頁
        if (i === 1 || i === total_pages || (i >= current_page - 2 && i <= current_page + 2)) {
            html += `
            <button class="px-3 py-1 rounded-md border ${i === current_page ? 'bg-blue-500 text-white' : 'bg-white hover:bg-gray-100'}"
                    data-page="${i}">
                ${i}
            </button>
            `;
        } else if (i === current_page - 3 || i === current_page + 3) {
            html += `<span class="px-2">...</span>`;
        }
    }

    // 下一頁按鈕
    html += `
    <button class="px-3 py-1 rounded-md border ${current_page === total_pages ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-white hover:bg-gray-100'}"
            ${current_page === total_pages ? 'disabled' : ''}
            data-page="${current_page + 1}">
        <i class="fas fa-chevron-right"></i>
    </button>
    `;

    paginationElement.innerHTML = html;

    // 添加頁碼點擊事件
    paginationElement.querySelectorAll('button:not([disabled])').forEach(button => {
        button.addEventListener('click', () => {
            const page = parseInt(button.getAttribute('data-page'));
            loadChampions(page, currentType, currentSort);
        });
    });
}

// 渲染英雄詳情
function renderChampionDetail(champion) {
    const content = document.getElementById('champion-detail-content');
    const { basic_info, stats, runes, builds, skills, matchups, synergies, tips } = champion;

    // 確保所有需要的資料都存在
    if (!basic_info || !stats) {
        content.innerHTML = '<div class="text-center py-8 text-gray-500">載入英雄詳情時發生錯誤</div>';
        return;
    }

    let html = `
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="md:col-span-1">
            <div class="bg-gray-200 rounded-lg overflow-hidden">
                <img src="https://ddragon.leagueoflegends.com/cdn/img/champion/splash/${basic_info.key}_0.jpg" alt="${basic_info.champion_name}" class="w-full h-auto">
            </div>
            <div class="mt-4 bg-white rounded-lg shadow-md p-4">
                <h2 class="text-2xl font-bold mb-2">${basic_info.champion_name} ${basic_info.champion_tw_name ? `(${basic_info.champion_tw_name})` : ''}</h2>
                <div class="text-sm text-gray-600 mb-2">${basic_info.champion_type} | 難度: ${getChampionDifficulty(basic_info.champion_difficulty)}</div>
                <div class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full inline-block font-semibold mb-3">${basic_info.tier} 級 | ${basic_info.rank_desc}</div>

                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div class="bg-green-50 p-3 rounded-lg">
                        <div class="text-green-800 font-bold text-lg">${stats.win_rate}%</div>
                        <div class="text-sm text-gray-600">勝率</div>
                    </div>
                    <div class="bg-blue-50 p-3 rounded-lg">
                        <div class="text-blue-800 font-bold text-lg">${stats.pick_rate}%</div>
                        <div class="text-sm text-gray-600">選用率</div>
                    </div>
                </div>

                <h3 class="font-bold text-lg mb-2">數據統計</h3>
                <div class="space-y-2 mb-4">
                    <div class="flex justify-between">
                        <span>KDA:</span>
                        <span class="font-semibold">${stats.kda} (${stats.kda_ratio})</span>
                    </div>
                    <div class="flex justify-between">
                        <span>平均傷害:</span>
                        <span class="font-semibold">${stats.damage} (${stats.damage_percentage})</span>
                    </div>
                    <div class="flex justify-between">
                        <span>平均承傷:</span>
                        <span class="font-semibold">${stats.damage_taken} (${stats.damage_taken_percentage})</span>
                    </div>
                    <div class="flex justify-between">
                        <span>平均治療:</span>
                        <span class="font-semibold">${stats.healing} (${stats.healing_percentage})</span>
                    </div>
                </div>

                <h3 class="font-bold text-lg mb-2">技能順序</h3>
                <div class="mb-4">
                    <div class="text-sm">優先級: <span class="font-semibold">${skills ? skills.skill_order : 'R > Q > W > E'}</span></div>
                    <div class="text-sm">起手技能: <span class="font-semibold">${skills ? skills.first_skill : 'Q'}</span></div>
                </div>

                <h3 class="font-bold text-lg mb-2">使用小技巧</h3>
                <ul class="list-disc list-inside text-sm space-y-1 mb-4">
                    ${tips ? tips.map(tip => `<li>${tip}</li>`).join('') : '<li>沒有可用的小技巧</li>'}
                </ul>
            </div>
        </div>

        <div class="md:col-span-2">
            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h3 class="font-bold text-xl mb-4">最佳符文配置</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${runes && runes.length > 0 ? runes.map((rune, index) => `
                    <div class="border rounded-lg p-4">
                        <div class="flex justify-between items-center mb-3">
                            <span class="font-semibold text-lg">配置 ${index + 1}</span>
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm">勝率 ${rune.runes_win_rate}%</span>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <div class="text-sm font-semibold mb-1">主系: ${getRunePath(rune.primary_path)}</div>
                                <div class="text-sm mb-2">核心: ${getRuneName(rune.primary_rune)}</div>
                                <div class="text-sm">
                                    ${rune.secondary_runes.map(id => `<div>${getRuneName(id)}</div>`).join('')}
                                </div>
                            </div>
                            <div>
                                <div class="text-sm font-semibold mb-1">副系: ${getRunePath(rune.secondary_path)}</div>
                                <div class="text-sm mb-3">
                                    ${rune.secondary_choices.map(id => `<div>${getRuneName(id)}</div>`).join('')}
                                </div>
                                <div class="text-sm font-semibold mb-1">符文碎片:</div>
                                <div class="text-sm">
                                    ${rune.shards.map(id => `<div>${getShardName(id)}</div>`).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                    `).join('') : '<div class="text-center py-4 text-gray-500">沒有找到符文配置資料</div>'}
                </div>
            </div>

            <div class="bg-white rounded-lg shadow-md p-6 mb-6">
                <h3 class="font-bold text-xl mb-4">推薦出裝</h3>
                <div class="space-y-6">
                    ${builds && builds.length > 0 ? builds.map((build, index) => `
                    <div class="border rounded-lg p-4">
                        <div class="flex justify-between items-center mb-3">
                            <span class="font-semibold text-lg">出裝 ${index + 1}</span>
                            <span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-sm">勝率 ${build.build_win_rate}%</span>
                        </div>
                        <div class="space-y-3">
                            <div>
                                <div class="text-sm font-semibold mb-2">起始裝備:</div>
                                <div class="flex flex-wrap gap-2">
                                    ${build.starting_items.map(id => `
                                    <div class="bg-gray-100 rounded-lg p-1">
                                        <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/item/${id}.png" alt="Item ${id}" class="w-10 h-10 object-cover" title="${getItemName(id)}">
                                    </div>
                                    `).join('')}
                                </div>
                            </div>
                            <div>
                                <div class="text-sm font-semibold mb-2">核心裝備:</div>
                                <div class="flex flex-wrap gap-2">
                                    ${build.core_items.map(id => `
                                    <div class="bg-gray-100 rounded-lg p-1">
                                        <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/item/${id}.png" alt="Item ${id}" class="w-10 h-10 object-cover" title="${getItemName(id)}">
                                    </div>
                                    `).join('')}
                                </div>
                            </div>
                            <div>
                                <div class="text-sm font-semibold mb-2">可選裝備:</div>
                                <div class="flex flex-wrap gap-2">
                                    ${build.optional_items.map(id => `
                                    <div class="bg-gray-100 rounded-lg p-1">
                                        <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/item/${id}.png" alt="Item ${id}" class="w-10 h-10 object-cover" title="${getItemName(id)}">
                                    </div>
                                    `).join('')}
                                </div>
                            </div>
                        </div>
                    </div>
                    `).join('') : '<div class="text-center py-4 text-gray-500">沒有找到出裝資料</div>'}
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="font-bold text-xl mb-4">最佳對位</h3>
                    <div class="space-y-2">
                        ${matchups && matchups.best && matchups.best.length > 0 ? matchups.best.map(matchup => `
                        <div class="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                            <div class="flex items-center">
                                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${getChampionKey(matchup.opponent_id)}.png" alt="${matchup.opponent_id}" class="w-8 h-8 rounded-full mr-2">
                                <span>${matchup.opponent_id}</span>
                            </div>
                            <span class="text-green-600 font-semibold">${matchup.win_rate}%</span>
                        </div>
                        `).join('') : '<div class="text-center py-4 text-gray-500">沒有找到對位資料</div>'}
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="font-bold text-xl mb-4">最佳協同</h3>
                    <div class="space-y-2">
                        ${synergies && synergies.length > 0 ? synergies.map(synergy => `
                        <div class="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                            <div class="flex items-center">
                                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${getChampionKey(synergy.champion_id)}.png" alt="${synergy.champion_id}" class="w-8 h-8 rounded-full mr-2">
                                <span>${synergy.champion_id}</span>
                            </div>
                            <span class="text-blue-600 font-semibold">+${synergy.synergy_score}</span>
                        </div>
                        `).join('') : '<div class="text-center py-4 text-gray-500">沒有找到協同資料</div>'}
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;

    content.innerHTML = html;
}

// 渲染梯隊排名
function renderTierList(tierList) {
    const content = document.getElementById('page-content');

    if (!tierList || tierList.length === 0) {
        content.innerHTML = '<div class="text-center py-8 text-gray-500">沒有找到梯隊資料</div>';
        return;
    }

    let html = '<div class="space-y-8">';

    tierList.forEach(tier => {
        const tierClass = `tier-${tier.tier.toLowerCase()}`;

        html += `
        <div class="bg-white rounded-lg shadow-md overflow-hidden">
            <div class="p-4 ${tierClass}">
                <h2 class="text-2xl font-bold">${tier.tier} 級英雄</h2>
            </div>
            <div class="p-6">
                <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    ${tier.champions.map(champion => `
                    <div class="champion-card bg-white border rounded-lg overflow-hidden cursor-pointer" data-id="${champion.champion_id}">
                        <div class="h-28 bg-gray-200 relative">
                            <img src="https://ddragon.leagueoflegends.com/cdn/img/champion/loading/${champion.key}_0.jpg" alt="${champion.champion_name}" class="w-full h-full object-cover">
                            <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white text-xs px-2 py-1">
                                排名 #${champion.rank}
                            </div>
                        </div>
                        <div class="p-3">
                            <h3 class="font-bold text-sm text-center mb-1">${champion.champion_name}</h3>
                            <div class="flex justify-between text-xs">
                                <span>勝率: <span class="font-semibold text-green-600">${champion.win_rate}%</span></span>
                                <span>選用率: <span class="font-semibold text-blue-600">${champion.pick_rate}%</span></span>
                            </div>
                        </div>
                    </div>
                    `).join('')}
                </div>
            </div>
        </div>
        `;
    });

    html += '</div>';
    content.innerHTML = html;

    // 添加點擊事件
    document.querySelectorAll('.champion-card').forEach(card => {
        card.addEventListener('click', () => {
            const championId = card.getAttribute('data-id');
            loadChampionDetail(championId);
        });
    });
}

// 渲染協同矩陣
function renderSynergyMatrix(data) {
    const content = document.getElementById('page-content');

    if (!data || !data.champions || !data.matrix) {
        content.innerHTML = '<div class="text-center py-8 text-gray-500">載入協同矩陣資料時發生錯誤</div>';
        return;
    }

    const { champions, matrix } = data;

    let html = `
    <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 class="text-2xl font-bold mb-6">英雄協同矩陣</h2>
        <p class="mb-6">此矩陣顯示了熱門英雄之間的協同效應。數值越高表示這兩個英雄一起選擇時勝率提升越多。</p>

        <div class="overflow-x-auto">
            <table class="w-full border-collapse">
                <thead>
                    <tr>
                        <th class="border p-2 bg-gray-100"></th>
                        ${champions.map(champion => `
                        <th class="border p-2 bg-gray-100">
                            <div class="w-12 h-12 mx-auto">
                                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${getChampionKey(champion)}.png" alt="${champion}" class="w-full h-full object-cover rounded-full" title="${champion}">
                            </div>
                        </th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${champions.map((champion, i) => `
                    <tr>
                        <th class="border p-2 bg-gray-100">
                            <div class="w-12 h-12">
                                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${getChampionKey(champion)}.png" alt="${champion}" class="w-full h-full object-cover rounded-full" title="${champion}">
                            </div>
                        </th>${matrix[i].map((value, j) => {
                            let bgColor = 'bg-white';
                            let textColor = 'text-gray-600';

                            if (i === j) {
                                bgColor = 'bg-gray-200';
                            } else if (value > 5) {
                                bgColor = 'bg-green-100';
                                textColor = 'text-green-800';
                            } else if (value > 2) {
                                bgColor = 'bg-green-50';
                                textColor = 'text-green-700';
                            } else if (value < -2) {
                                bgColor = 'bg-red-50';
                                textColor = 'text-red-700';
                            } else if (value < -5) {
                                bgColor = 'bg-red-100';
                                textColor = 'text-red-800';
                            }

                            return `<td class="border p-2 text-center ${bgColor} ${textColor}">${i === j ? '-' : value}</td>`;
                        }).join('')}
                    </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    </div>
    `;

    content.innerHTML = html;
}

// 渲染對位矩陣
function renderMatchupMatrix(data) {
    const content = document.getElementById('page-content');

    if (!data || !data.champions || !data.matrix) {
        content.innerHTML = '<div class="text-center py-8 text-gray-500">載入對位矩陣資料時發生錯誤</div>';
        return;
    }

    const { champions, matrix } = data;

    let html = `
    <div class="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 class="text-2xl font-bold mb-6">英雄對位矩陣</h2>
        <p class="mb-6">此矩陣顯示了熱門英雄之間的對位勝率。數值表示縱軸英雄對陣橫軸英雄時的勝率。</p>

        <div class="overflow-x-auto">
            <table class="w-full border-collapse">
                <thead>
                    <tr>
                        <th class="border p-2 bg-gray-100"></th>
                        ${champions.map(champion => `
                        <th class="border p-2 bg-gray-100">
                            <div class="w-12 h-12 mx-auto">
                                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${getChampionKey(champion)}.png" alt="${champion}" class="w-full h-full object-cover rounded-full" title="${champion}">
                            </div>
                        </th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${champions.map((champion, i) => `
                    <tr>
                        <th class="border p-2 bg-gray-100">
                            <div class="w-12 h-12">
                                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${getChampionKey(champion)}.png" alt="${champion}" class="w-full h-full object-cover rounded-full" title="${champion}">
                            </div>
                        </th>
                        ${matrix[i].map((value, j) => {
                            let bgColor = 'bg-white';
                            let textColor = 'text-gray-600';

                            if (i === j) {
                                bgColor = 'bg-gray-200';
                            } else if (value > 55) {
                                bgColor = 'bg-green-100';
                                textColor = 'text-green-800';
                            } else if (value > 52) {
                                bgColor = 'bg-green-50';
                                textColor = 'text-green-700';
                            } else if (value < 48) {
                                bgColor = 'bg-red-50';
                                textColor = 'text-red-700';
                            } else if (value < 45) {
                                bgColor = 'bg-red-100';
                                textColor = 'text-red-800';
                            }

                            return `<td class="border p-2 text-center ${bgColor} ${textColor}">${i === j ? '-' : value + '%'}</td>`;
                        }).join('')}
                    </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    </div>
    `;

    content.innerHTML = html;
}

// 渲染搜索結果
function renderSearchResults(results) {
    const resultsContainer = document.getElementById('search-results');

    if (!results || results.length === 0) {
        resultsContainer.classList.add('hidden');
        return;
    }

    let html = '';

    results.forEach(champion => {
        html += `
        <div class="search-result p-2 hover:bg-gray-100 cursor-pointer" data-id="${champion.champion_id}">
            <div class="flex items-center">
                <img src="https://ddragon.leagueoflegends.com/cdn/13.11.1/img/champion/${champion.key}.png" alt="${champion.champion_name}" class="w-8 h-8 rounded-full mr-2">
                <div>
                    <div class="font-medium">${champion.champion_name}</div>
                    <div class="text-xs text-gray-500">${champion.champion_tw_name || champion.champion_type}</div>
                </div>
            </div>
        </div>
        `;
    });

    resultsContainer.innerHTML = html;
    resultsContainer.classList.remove('hidden');

    // 添加點擊事件
    document.querySelectorAll('.search-result').forEach(result => {
        result.addEventListener('click', () => {
            const championId = result.getAttribute('data-id');
            loadChampionDetail(championId);
            resultsContainer.classList.add('hidden');
            document.getElementById('search-input').value = '';
        });
    });
}

// 載入特定頁面
function loadPage(page) {
    currentPage = page;
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-page') === page) {
            link.classList.add('active');
        }
    });

    document.getElementById('pagination').innerHTML = '';

    switch (page) {
        case 'champions':
            loadChampions(1, currentType, currentSort);
            break;
        case 'tier-list':
            loadTierList(currentType);
            break;
        case 'team-builder':
            // 顯示移除後的訊息
            document.getElementById('page-content').innerHTML = `
                <div class="bg-white rounded-lg shadow-md p-6 mb-8">
                    <h2 class="text-2xl font-bold mb-4">ARAM 隊伍模擬器</h2>
                    <p class="mb-6">此功能目前正在開發中，敬請期待！</p>
                </div>
            `;
            break;
        case 'synergy':
            loadSynergyMatrix();
            break;
        case 'matchup':
            loadMatchupMatrix();
            break;
    }
}

// 初始化應用
function init() {
    // 檢查載入指示器元素是否存在並添加 hidden 類別
    const loadingElement = document.getElementById('loading');
    if (loadingElement && !loadingElement.classList.contains('hidden')) {
        loadingElement.classList.add('hidden');
    }

    // 載入版本信息
    loadVersionInfo();

    // 載入初始頁面
    loadPage('champions');

    // 添加頁面切換事件
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.getAttribute('data-page');
            loadPage(page);
        });
    });

    // 移動菜單切換
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', () => {
            document.getElementById('mobile-menu').classList.toggle('hidden');
        });
    }

    // 關閉模態框按鈕
    const closeModalButton = document.getElementById('close-modal');
    if (closeModalButton) {
        closeModalButton.addEventListener('click', hideModal);
    }

    // 類型篩選事件
    const typeFilter = document.getElementById('champion-type-filter');
    if (typeFilter) {
        typeFilter.addEventListener('change', (e) => {
            currentType = e.target.value;
            if (currentPage === 'champions') {
                loadChampions(1, currentType, currentSort);
            } else if (currentPage === 'tier-list') {
                loadTierList(currentType);
            }
        });
    }

    // 排序方式事件
    const sortSelect = document.getElementById('champion-sort');
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            if (currentPage === 'champions') {
                loadChampions(1, currentType, currentSort);
            }
        });
    }

    // 搜索輸入事件
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            searchChampions(query);
        });
    }

    // 點擊空白處隱藏搜索結果
    document.addEventListener('click', (e) => {
        const searchResults = document.getElementById('search-results');
        const searchInput = document.getElementById('search-input');
        if (searchResults && searchInput && !searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // 點擊空白處隱藏模態框
    const championModal = document.getElementById('champion-modal');
    if (championModal) {
        championModal.addEventListener('click', (e) => {
            if (e.target === championModal) {
                hideModal();
            }
        });
    }
}

// 頁面載入完成後初始化
document.addEventListener('DOMContentLoaded', init);