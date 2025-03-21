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