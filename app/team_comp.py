    def create_test_data_tab(self):
        """创建测试即时数据页面"""
        # 创建主框架
        main_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 获取测试数据
        game_data = None
        if self.fetcher:
            game_data = self.fetcher.fetch_test_data()

        if not game_data or 'players' not in game_data:
            status_label = tk.Label(
                main_frame.interior,
                text="无法获取测试数据",
                bg="#0f3460",
                fg="#e94560",
                font=(self.font_family, 16)
            )
            status_label.pack(expand=True)
            return

        # 分离双方阵容
        blue_team = []
        red_team = []
        for player in game_data['players']:
            if player['team'] == 'ORDER':
                blue_team.append(player['championName'])
            else:
                red_team.append(player['championName'])

        # 创建双方阵容显示区域
        teams_frame = tk.Frame(main_frame.interior, bg="#0f3460")
        teams_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建左右两个面板的容器
        panels_frame = tk.Frame(teams_frame, bg="#0f3460")
        panels_frame.pack(fill="both", expand=True)

        # 蓝方阵容
        blue_frame = RoundedFrame(
            panels_frame,
            bg_color="#16213e",
            corner_radius=self.corner_radius
        )
        blue_frame.pack(side="left", fill="both", expand=True, padx=5)

        # 蓝方标题
        blue_title = tk.Label(
            blue_frame.interior,
            text="蓝方阵容",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 14)
        )
        blue_title.pack(pady=(10, 5))

        # 蓝方英雄网格
        blue_grid = tk.Frame(blue_frame.interior, bg="#16213e")
        blue_grid.pack(fill="both", expand=True, padx=10, pady=5)

        # 配置网格列权重
        for i in range(3):
            blue_grid.grid_columnconfigure(i, weight=1)

        # 显示蓝方英雄
        for i, champ in enumerate(blue_team):
            row = i // 3
            col = i % 3
            self._create_test_champion_card(blue_grid, champ, "blue", i)

        # 红方阵容
        red_frame = RoundedFrame(
            panels_frame,
            bg_color="#16213e",
            corner_radius=self.corner_radius
        )
        red_frame.pack(side="right", fill="both", expand=True, padx=5)

        # 红方标题
        red_title = tk.Label(
            red_frame.interior,
            text="红方阵容",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 14)
        )
        red_title.pack(pady=(10, 5))

        # 红方英雄网格
        red_grid = tk.Frame(red_frame.interior, bg="#16213e")
        red_grid.pack(fill="both", expand=True, padx=10, pady=5)

        # 配置网格列权重
        for i in range(3):
            red_grid.grid_columnconfigure(i, weight=1)

        # 显示红方英雄
        for i, champ in enumerate(red_team):
            row = i // 3
            col = i % 3
            self._create_test_champion_card(red_grid, champ, "red", i)

        # 创建胜率显示区域
        winrate_frame = RoundedFrame(
            teams_frame,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            height=80
        )
        winrate_frame.pack(fill="x", pady=(20, 0))
        winrate_frame.pack_propagate(False)

        # 计算并显示胜率预测
        self._calculate_team_winrates(blue_team, red_team)

    def _calculate_team_winrates(self, blue_team, red_team):
        """计算胜率"""
        self._calculate_team_winrates_thread(blue_team, red_team)

    def _calculate_team_winrates_thread(self, blue_team, red_team):
        """在背景线程中计算胜率"""
        try:
            # 转换英雄名称为英文
            blue_team_en = []
            red_team_en = []
            
            # 转换蓝队英雄名称
            for champ in blue_team:
                if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                    reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                    if champ in reverse_mapping:
                        blue_team_en.append(reverse_mapping[champ])
                        continue
                blue_team_en.append(champ)

            # 转换红队英雄名称
            for champ in red_team:
                if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                    reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                    if champ in reverse_mapping:
                        red_team_en.append(reverse_mapping[champ])
                        continue
                red_team_en.append(champ)

            # 计算蓝方胜率
            blue_winrate = 0.5  # 默认值
            if blue_team_en:
                try:
                    blue_result = recommend_compositions_api(blue_team_en)
                    if blue_result:
                        blue_winrate = blue_result[0][1]
                except Exception as e:
                    print(f"计算蓝方胜率时出错: {e}")

            # 计算红方胜率
            red_winrate = 0.5  # 默认值
            if red_team_en:
                try:
                    red_result = recommend_compositions_api(red_team_en)
                    if red_result:
                        red_winrate = red_result[0][1]
                except Exception as e:
                    print(f"计算红方胜率时出错: {e}")

            # 归一化胜率
            total = blue_winrate + red_winrate
            if total > 0:
                blue_winrate = blue_winrate / total
                red_winrate = red_winrate / total

            # 更新 UI
            self.root.after(0, lambda: self._update_winrate_display(blue_winrate, red_winrate))

        except Exception as e:
            print(f"计算胜率时出错: {e}")
            self.root.after(0, lambda: self._update_winrate_display(0.5, 0.5, error=True))

    def _update_winrate_display(self, blue_winrate, red_winrate, error=False):
        """更新胜率显示"""
        # 创建胜率显示框架
        winrate_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            height=80
        )
        winrate_frame.pack(fill="x", padx=20, pady=10)
        winrate_frame.pack_propagate(False)

        if error:
            error_label = tk.Label(
                winrate_frame.interior,
                text="胜率计算失败",
                bg="#16213e",
                fg="#e94560",
                font=(self.font_family, 14)
            )
            error_label.pack(expand=True)
            return

        # 创建胜率显示容器
        display_frame = tk.Frame(winrate_frame.interior, bg="#16213e")
        display_frame.pack(expand=True)

        # 蓝方胜率
        blue_frame = tk.Frame(display_frame, bg="#16213e")
        blue_frame.pack(side="left", padx=20)
        
        blue_label = tk.Label(
            blue_frame,
            text="蓝方胜率",
            bg="#16213e",
            fg="white",
            font=(self.font_family, 12)
        )
        blue_label.pack()
        
        blue_value = tk.Label(
            blue_frame,
            text=f"{blue_winrate:.1%}",
            bg="#16213e",
            fg="#4ecca3",
            font=(self.font_family_bold, 24)
        )
        blue_value.pack()

        # VS 标签
        vs_label = tk.Label(
            display_frame,
            text="VS",
            bg="#16213e",
            fg="#e94560",
            font=(self.font_family_bold, 16)
        )
        vs_label.pack(side="left", padx=40)

        # 红方胜率
        red_frame = tk.Frame(display_frame, bg="#16213e")
        red_frame.pack(side="left", padx=20)
        
        red_label = tk.Label(
            red_frame,
            text="红方胜率",
            bg="#16213e",
            fg="white",
            font=(self.font_family, 12)
        )
        red_label.pack()
        
        red_value = tk.Label(
            red_frame,
            text=f"{red_winrate:.1%}",
            bg="#16213e",
            fg="#e94560",
            font=(self.font_family_bold, 24)
        )
        red_value.pack()

    def _create_test_champion_card(self, parent, champion_name, team_color, index):
        """創建英雄卡片"""
        print(f"\n=== 創建英雄卡片 ===")
        print(f"英雄名稱: {champion_name}")
        print(f"隊伍顏色: {team_color}")
        print(f"索引: {index}")

        # 設置顏色
        if team_color == "blue":
            bg_color = "#1E293B"
            icon_bg = "#3B5998"
            icon_stroke = "#5F9DF7"
        else:
            bg_color = "#2D1E1E"
            icon_bg = "#983B3B"
            icon_stroke = "#F75F5F"

        # 創建卡片框架
        card_frame = RoundedFrame(
            parent,
            bg_color=bg_color,
            corner_radius=10,
            height=50
        )
        card_frame.grid(row=index // 3, column=index % 3, padx=5, pady=5, sticky="nsew")
        card_frame.pack_propagate(False)

        # 英雄圖標框架
        icon_frame = RoundedFrame(
            card_frame.interior,
            bg_color=icon_bg,
            corner_radius=20,
            width=40,
            height=40
        )
        icon_frame.pack(side="left", padx=(10, 0), pady=5)
        icon_frame.pack_propagate(False)

        # 獲取英雄圖像
        print("\n開始獲取英雄圖像:")
        image = None
        
        print(f"檢查 controller.champ_images 是否存在: {hasattr(self.controller, 'champ_images')}")
        if hasattr(self.controller, 'champ_images'):
            print(f"champ_images 中的鍵: {list(self.controller.champ_images.keys())}")
            print(f"當前英雄名稱是否在 champ_images 中: {champion_name in self.controller.champ_images}")
            
            if champion_name in self.controller.champ_images:
                image = self.controller.champ_images[champion_name]
                print(f"直接從 champ_images 找到圖像: {image is not None}")
            elif hasattr(self.fetcher, 'get_champ_key'):
                print("\n嘗試使用 fetcher.get_champ_key:")
                key = self.fetcher.get_champ_key(champion_name)
                print(f"獲取到的 champion key: {key}")
                print(f"key 是否在 champ_images 中: {key in self.controller.champ_images}")
                
                if key in self.controller.champ_images:
                    image = self.controller.champ_images[key]
                    print(f"通過 key 找到圖像: {image is not None}")

        print(f"\n最終圖像獲取結果: {image is not None}")

        # 創建圖像標籤
        if image:
            print("\n創建圖像標籤")
            icon_label = tk.Label(
                icon_frame.interior,
                image=image,
                bg=icon_bg,
                borderwidth=0
            )
            icon_label.image = image  # 保持圖像引用
            icon_label.pack(fill="both", expand=True)
            print("圖像標籤創建完成")
        else:
            print("\n創建替代圓形")
            # 如果沒有圖像，創建一個空的圓形
            icon_canvas = tk.Canvas(
                icon_frame.interior,
                width=40,
                height=40,
                bg=icon_bg,
                highlightthickness=0
            )
            icon_canvas.create_oval(5, 5, 35, 35, fill=icon_bg, outline=icon_stroke)
            icon_canvas.pack(fill="both", expand=True)
            print("替代圓形創建完成")

        # 英雄名稱
        name_label = tk.Label(
            card_frame.interior,
            text=self._get_display_name(champion_name),
            bg=bg_color,
            fg="white",
            font=(self.font_family, 16),
            anchor="center"
        )
        name_label.pack(fill="both", expand=True, padx=(20, 10))
        print("=== 英雄卡片創建完成 ===\n")

    def create_recommendation_tab(self):
        """創建推薦陣容選項卡"""
        # 創建表格
        table_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 表頭
        header_frame = RoundedFrame(
            table_frame.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            height=40
        )
        header_frame.interior.config(height=40)
        header_frame.pack(fill="x")

        # 勝率列
        win_rate_header = tk.Label(
            header_frame.interior,
            text="勝率",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=10,
            height=2
        )
        win_rate_header.pack(side="left", padx=(20, 0))

        # 陣容組合列
        comp_header = tk.Label(
            header_frame.interior,
            text="陣容組合",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=50,
            height=2
        )
        comp_header.pack(side="left", fill="x", expand=True)

        # 創建捲動容器
        scroll_container = RoundedFrame(
            table_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        scroll_container.pack(fill="both", expand=True)

        # 創建 Canvas 和捲動條
        canvas = tk.Canvas(
            scroll_container.interior,
            bg="#0f3460",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            scroll_container.interior,
            orient="vertical",
            command=canvas.yview
        )

        # 配置佈局
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 將 canvas 連接到捲動條
        canvas.configure(yscrollcommand=scrollbar.set)

        # 創建內部框架來放置表格內容
        self.table_content_frame = tk.Frame(canvas, bg="#0f3460")
        canvas_frame = canvas.create_window((0, 0), window=self.table_content_frame, anchor="nw")

        # 更新捲動區域
        self.table_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        # 添加表格行
        self.update_recommendation_table()

    def create_worst_recommendation_tab(self):
        """創建最不推薦陣容選項卡"""
        # 創建表格
        table_frame = RoundedFrame(
            self.content_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 表頭
        header_frame = RoundedFrame(
            table_frame.interior,
            bg_color="#16213e",
            corner_radius=self.corner_radius,
            height=40
        )
        header_frame.interior.config(height=40)
        header_frame.pack(fill="x")

        # 勝率列
        win_rate_header = tk.Label(
            header_frame.interior,
            text="勝率",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=10,
            height=2
        )
        win_rate_header.pack(side="left", padx=(20, 0))

        # 陣容組合列
        comp_header = tk.Label(
            header_frame.interior,
            text="陣容組合",
            bg="#16213e",
            fg="white",
            font=(self.font_family_bold, 10),
            width=50,
            height=2
        )
        comp_header.pack(side="left", fill="x", expand=True)

        # 創建捲動容器
        scroll_container = RoundedFrame(
            table_frame.interior,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        scroll_container.pack(fill="both", expand=True)

        # 創建 Canvas 和捲動條
        canvas = tk.Canvas(
            scroll_container.interior,
            bg="#0f3460",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            scroll_container.interior,
            orient="vertical",
            command=canvas.yview
        )

        # 配置佈局
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 將 canvas 連接到捲動條
        canvas.configure(yscrollcommand=scrollbar.set)

        # 創建內部框架來放置表格內容
        self.worst_table_content_frame = tk.Frame(canvas, bg="#0f3460")
        canvas_frame = canvas.create_window((0, 0), window=self.worst_table_content_frame, anchor="nw")

        # 更新捲動區域
        self.worst_table_content_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_frame, width=e.width))

        # 添加表格行
        self.update_worst_recommendation_table()

    def update_worst_recommendation_table(self):
        """更新最不推薦陣容表格"""
        # 清除現有內容
        for widget in self.worst_table_content_frame.winfo_children():
            widget.destroy()

        # 如果沒有推薦數據，顯示提示信息
        if not self.worst_recommendation_data:
            empty_label = tk.Label(
                self.worst_table_content_frame,
                text="請選擇英雄或刷新數據以獲取最不推薦陣容",
                bg="#0f3460",
                fg="white",
                font=(self.font_family, 12),
                height=4
            )
            empty_label.pack(fill="x", pady=20)
            return

        # 添加表格行
        for i, (comp, win_rate) in enumerate(self.worst_recommendation_data):
            # 創建圓角行框架
            row_frame = RoundedFrame(
                self.worst_table_content_frame,
                bg_color="#0c2b52" if i % 2 == 0 else "#0f3460",
                corner_radius=self.corner_radius,
                height=60
            )
            row_frame.interior.config(height=60)
            row_frame.pack(fill="x", pady=2)  # 增加間距使圓角明顯
            row_frame.pack_propagate(False)

            # 勝率
            win_rate_label = tk.Label(
                row_frame.interior,
                text=f"{win_rate:.2%}",
                bg=row_frame.interior["bg"],
                fg="#e94560",  # 使用紅色來表示低勝率
                font=(self.font_family_bold, 12),
                width=10,
                height=2
            )
            win_rate_label.pack(side="left", padx=(20, 0))

            # 陣容組合 - 使用更大的區域
            comp_frame = tk.Frame(row_frame.interior, bg=row_frame.interior["bg"])
            comp_frame.pack(side="left", fill="both", expand=True, padx=(10, 10))

            # 英雄圖標和名稱 - 使用固定尺寸的框架
            icons_container = tk.Frame(comp_frame, bg=row_frame.interior["bg"])
            icons_container.pack(side="left", fill="y")

            # 顯示英雄圖標和名稱
            for champ in comp:
                # 創建英雄圖標框架
                icon_frame = RoundedFrame(
                    icons_container,
                    bg_color="#16213e",
                    corner_radius=15,
                    width=40,
                    height=40
                )
                icon_frame.pack(side="left", padx=2)
                icon_frame.pack_propagate(False)

                # 獲取英雄圖像
                image = None
                if hasattr(self.controller, 'champ_images'):
                    if champ in self.controller.champ_images:
                        image = self.controller.champ_images[champ]
                    elif hasattr(self.fetcher, 'get_champ_key'):
                        key = self.fetcher.get_champ_key(champ)
                        if key in self.controller.champ_images:
                            image = self.controller.champ_images[key]

                # 創建圖像標籤
                if image:
                    icon_label = tk.Label(
                        icon_frame.interior,
                        image=image,
                        bg="#16213e",
                        borderwidth=0
                    )
                    icon_label.image = image  # 保持圖像引用
                    icon_label.pack(fill="both", expand=True)
                else:
                    # 如果沒有圖像，創建一個空的圓形
                    icon_canvas = tk.Canvas(
                        icon_frame.interior,
                        width=40,
                        height=40,
                        bg="#16213e",
                        highlightthickness=0
                    )
                    icon_canvas.create_oval(5, 5, 35, 35, fill="#16213e", outline="#e94560")
                    icon_canvas.pack(fill="both", expand=True)

                # 英雄名稱
                name_label = tk.Label(
                    icons_container,
                    text=self._get_display_name(champ),
                    bg=row_frame.interior["bg"],
                    fg="white",
                    font=(self.font_family, 10)
                )
                name_label.pack(side="left", padx=2)

    def refresh_recommendations(self):
        """刷新推薦陣容"""
        # 獲取已選英雄名稱列表
        selected_names = []

        for slot in self.selected_champion_slots:
            if slot["selected"] and slot["champion_name"] is not None:
                selected_names.append(slot["champion_name"])

        # 如果選擇的英雄不足，顯示提示信息
        if len(selected_names) < 1:
            self.recommendation_data = []
            self.worst_recommendation_data = []
            self.update_recommendation_table()
            self.update_worst_recommendation_table()
            return

        # 獲取所有可用英雄名稱
        all_champion_names = []

        # 如果有 fetcher，嘗試獲取完整的可用英雄池
        if self.fetcher:
            try:
                data = self.fetcher.fetch_live_data() or self.fetcher.load_local_data()
                if data and 'all_pool' in data:
                    all_champion_names = data['all_pool']
            except Exception as e:
                print(f"獲取英雄池時出錯: {e}")

        # 如果沒有獲取到數據，使用可用英雄槽中的數據
        if not all_champion_names:
            all_champion_names = [slot["champion_name"] for slot in self.available_champion_slots]
            # 添加已選英雄
            for name in selected_names:
                if name not in all_champion_names:
                    all_champion_names.append(name)

        # 開始計算推薦陣容和最不推薦陣容 (使用 API)
        threading.Thread(target=self._calculate_recommendations_api, args=(all_champion_names,), daemon=True).start()
        threading.Thread(target=self._calculate_worst_recommendations_api, args=(all_champion_names,), daemon=True).start()

    def _calculate_worst_recommendations_api(self, champion_pool):
        """使用 API 在後台執行最不推薦陣容計算"""
        try:
            print(f"開始API調用，英雄池大小: {len(champion_pool)}")
            start_time = time.time()

            # 轉換為英文名稱
            english_champions = []
            for champion in champion_pool:
                if self.fetcher and hasattr(self.fetcher, 'tw_mapping'):
                    reverse_mapping = {v: k for k, v in self.fetcher.tw_mapping.items()}
                    if champion in reverse_mapping:
                        english_champions.append(reverse_mapping[champion])
                        continue
                english_champions.append(champion)

            print(f"準備調用API，轉換後的英雄名稱: {english_champions}")
            
            # 使用英文名稱調用 API
            sorted_compositions = recommend_worst_compositions_api(english_champions)
            print(f"API返回結果數量: {len(sorted_compositions) if sorted_compositions else 0}")

            elapsed = time.time() - start_time
            print(f"API 計算完成，耗時: {elapsed:.2f}秒")

            # 處理 API 返回的結果
            if not sorted_compositions:
                print("API 返回空結果")
                self.root.after(0, lambda: self._update_worst_recommendations([]))
                return

            # 轉換 API 結果格式為我們需要的格式
            recommendations = []

            # 顯示最不推薦的前10個陣容（勝率最低）
            for comp, prob in sorted_compositions[:10]:
                recommendations.append((list(comp), prob))

            # 更新 UI (在主線程中)
            self.root.after(0, lambda: self._update_worst_recommendations(recommendations))

        except Exception as e:
            print(f"計算最不推薦陣容時出錯: {e}")
            self.root.after(0, lambda: self._update_worst_recommendations([]))
            messagebox.showerror("錯誤", f"最不推薦陣容計算失敗: {str(e)}")

    def _update_worst_recommendations(self, recommendations):
        """更新最不推薦陣容數據"""
        self.worst_recommendation_data = recommendations
        self.update_worst_recommendation_table()

    def create_two_column_layout(self):
        """創建兩欄佈局"""
        # 左側面板 - 英雄選擇
        left_panel = RoundedFrame(
            self,
            bg_color="#16213e",
            corner_radius=self.corner_radius
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # 右側面板 - 推薦陣容
        right_panel = RoundedFrame(
            self,
            bg_color="#16213e",
            corner_radius=self.corner_radius
        )
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # 創建標籤頁
        self.notebook = ttk.Notebook(right_panel.interior)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # 創建內容框架
        self.content_frame = RoundedFrame(
            self.notebook,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        self.notebook.add(self.content_frame, text="推薦陣容")

        # 創建最不推薦陣容內容框架
        self.worst_content_frame = RoundedFrame(
            self.notebook,
            bg_color="#0f3460",
            corner_radius=self.corner_radius
        )
        self.notebook.add(self.worst_content_frame, text="最不推薦陣容")

        # 創建推薦陣容標籤頁
        self.create_recommendation_tab()

        # 創建最不推薦陣容標籤頁
        self.create_worst_recommendation_tab()

        # 左側面板內容
        self.create_left_panel_content(left_panel)

        # 綁定標籤頁切換事件
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

    def _on_tab_changed(self, event):
        """處理標籤頁切換事件"""
        try:
            current_tab = self.notebook.select()
            tab_text = self.notebook.tab(current_tab, "text")
            
            if tab_text == "推薦陣容":
                self.create_recommendation_tab()
            elif tab_text == "最不推薦陣容":
                self.create_worst_recommendation_tab()
            elif tab_text == "測試即時數據":
                self.create_test_data_tab()
        except Exception as e:
            print(f"切換標籤頁時出錯: {e}") 