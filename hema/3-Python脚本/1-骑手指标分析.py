import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
from datetime import datetime
import os

class RiderDataAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("骑手签收时间分析工具")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        
        # 数据存储
        self.data = None
        self.analysis_result = None
        self.current_sort_column = None
        self.current_sort_reverse = False
        self.all_riders = []
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 设置全局字体样式
        style.configure("TButton", font=("TkDefaultFont", 15))
        style.configure("TLabel", font=("TkDefaultFont", 15))
        style.configure("TLabelframe.Label", font=("TkDefaultFont", 15, "bold"))
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 顶部控制栏
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(control_frame, text="打开Excel文件", command=self.load_excel, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="导出结果", command=self.export_results, width=15).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="请打开Excel文件", foreground="gray", font=("TkDefaultFont", 14))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 骑手选择区域（左右分栏）
        rider_main_frame = ttk.LabelFrame(self.root, text="骑手数据分析", padding="10")
        rider_main_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        # 创建左右分栏
        paned = ttk.PanedWindow(rider_main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧：骑手选择区域
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # 右侧：关键指标显示区域
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        # ========== 左侧：骑手选择 ==========
        rider_select_frame = ttk.LabelFrame(left_frame, text="骑手选择", padding="10")
        rider_select_frame.pack(fill=tk.BOTH, expand=True)
        
        # 搜索输入和下拉选择
        select_frame = ttk.Frame(rider_select_frame)
        select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(select_frame, text="骑手名称:", font=("TkDefaultFont", 15)).pack(side=tk.LEFT, padx=5)
        
        self.rider_var = tk.StringVar()
        self.rider_combo = ttk.Combobox(select_frame, textvariable=self.rider_var, width=12, 
                                        font=("TkDefaultFont", 15))
        self.rider_combo.pack(side=tk.LEFT, padx=5)
        
        # 绑定事件
        self.rider_combo.bind('<<ComboboxSelected>>', self.on_rider_selected)
        self.rider_combo.bind('<KeyRelease>', self.on_rider_search)
        self.rider_combo.bind('<Return>', self.on_rider_enter)
        
        # 按钮框架
        button_frame = ttk.Frame(rider_select_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="查询", command=self.query_selected_rider, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重置", command=self.reset_search, width=10).pack(side=tk.LEFT, padx=5)
        
        # 提示标签
        hint_text = "提示：\n• 可直接输入骑手名称模糊搜索\n• 或从下拉列表中选择\n• 支持回车键快速查询"
        self.hint_label = ttk.Label(rider_select_frame, text=hint_text, foreground="gray", justify=tk.LEFT, font=("TkDefaultFont", 13))
        self.hint_label.pack(anchor=tk.W, padx=10, pady=10)
        
        # ========== 右侧：关键指标（网格布局） ==========
        self.create_key_metrics_grid(right_frame)
        
        # 创建主内容区域（表格显示）
        paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 上方表格框架
        top_frame = ttk.Frame(paned_window)
        paned_window.add(top_frame, weight=4)
        
        # 创建表格容器框架
        tree_container = ttk.Frame(top_frame)
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview和滚动条
        self.create_treeview(tree_container)
        
        # 下方详细统计信息框架
        bottom_frame = ttk.Frame(paned_window)
        paned_window.add(bottom_frame, weight=1)
        
        # 详细统计信息显示
        stats_frame = ttk.LabelFrame(bottom_frame, text="详细统计信息", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建带滚动条的文本框
        text_frame = ttk.Frame(stats_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.stats_text = tk.Text(text_frame, height=8, wrap=tk.WORD, font=("Consolas", 14))
        stats_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定窗口大小改变事件
        self.root.bind('<Configure>', self.on_window_resize)
        
    def create_key_metrics_grid(self, parent):
        """创建关键指标网格布局"""
        metrics_frame = ttk.LabelFrame(parent, text="关键指标", padding="8")
        metrics_frame.pack(fill=tk.BOTH, expand=True)
        
        # 使用Grid布局，创建2列6行的网格
        metrics_data = [
            ("骑手姓名", "—"),
            ("总签收次数", "—"),
            ("开始时间", "—"),
            ("结束时间", "—"),
            ("总工作时长", "—"),
            ("平均间隔", "—"),
            ("中位数间隔", "—"),
            ("最短间隔", "—"),
            ("最长间隔", "—"),
            ("签收频率", "—"),
            ("数据状态", "未查询")
        ]
        
        self.metrics_labels = {}
        self.metrics_values = {}
        
        # 创建网格布局
        for i, (label, default) in enumerate(metrics_data):
            row = i // 2
            col = i % 2
            
            # 标签框架
            frame = ttk.Frame(metrics_frame)
            frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=3)
            
            # 标签
            label_widget = ttk.Label(frame, text=f"{label}:", font=("TkDefaultFont", 15, "bold"), width=10, anchor=tk.W)
            label_widget.pack(side=tk.LEFT)
            
            # 值
            value_var = tk.StringVar(value=default)
            self.metrics_values[label] = value_var
            
            value_widget = ttk.Label(frame, textvariable=value_var, font=("TkDefaultFont", 15), 
                                     foreground="blue", anchor=tk.W, wraplength=200)
            value_widget.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)
        
        # 配置网格权重
        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        
        # 设置所有行权重
        for i in range(6):
            metrics_frame.grid_rowconfigure(i, weight=0)
    
    def update_key_metrics(self, data):
        """更新关键指标显示"""
        if data is None or len(data) == 0:
            default_values = {
                "骑手姓名": "—",
                "总签收次数": "—",
                "开始时间": "—",
                "结束时间": "—",
                "总工作时长": "—",
                "平均间隔": "—",
                "中位数间隔": "—",
                "最短间隔": "—",
                "最长间隔": "—",
                "签收频率": "—",
                "数据状态": "未查询"
            }
            for key, value in default_values.items():
                if key in self.metrics_values:
                    self.metrics_values[key].set(value)
            return
        
        total_records = len(data)
        valid_intervals = data['签收间隔(分钟)'][1:].dropna()
        total_duration_minutes = (data.iloc[-1]['签收时间'] - data.iloc[0]['签收时间']).total_seconds() / 60
        
        total_hours = int(total_duration_minutes // 60)
        total_minutes = int(total_duration_minutes % 60)
        duration_str = f"{total_hours}小时{total_minutes}分钟"
        
        # 更新指标
        self.metrics_values["骑手姓名"].set(data.iloc[0]['骑手'])
        self.metrics_values["总签收次数"].set(f"{total_records} 次")
        self.metrics_values["开始时间"].set(data.iloc[0]['签收时间(格式化)'])
        self.metrics_values["结束时间"].set(data.iloc[-1]['签收时间(格式化)'])
        self.metrics_values["总工作时长"].set(duration_str)
        
        if len(valid_intervals) > 0:
            avg_interval = valid_intervals.mean()
            median_interval = valid_intervals.median()
            min_interval = valid_intervals.min()
            max_interval = valid_intervals.max()
            frequency_per_hour = total_records / (total_duration_minutes / 60) if total_duration_minutes > 0 else 0
            
            self.metrics_values["平均间隔"].set(f"{avg_interval:.1f} 分钟")
            self.metrics_values["中位数间隔"].set(f"{median_interval:.1f} 分钟")
            self.metrics_values["最短间隔"].set(f"{min_interval:.1f} 分钟")
            self.metrics_values["最长间隔"].set(f"{max_interval:.1f} 分钟")
            self.metrics_values["签收频率"].set(f"{frequency_per_hour:.2f} 次/小时")
            self.metrics_values["数据状态"].set("已查询")
        else:
            self.metrics_values["平均间隔"].set("—")
            self.metrics_values["中位数间隔"].set("—")
            self.metrics_values["最短间隔"].set("—")
            self.metrics_values["最长间隔"].set("—")
            self.metrics_values["签收频率"].set("—")
            self.metrics_values["数据状态"].set("仅一条记录")
        
    def create_treeview(self, parent):
        """创建表格视图"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 设置表格样式
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("TkDefaultFont", 15, "bold"))
        style.configure("Treeview", font=("TkDefaultFont", 15), rowheight=35)
        
        # 创建Treeview控件
        self.tree = ttk.Treeview(tree_frame, 
                                 yscrollcommand=v_scrollbar.set,
                                 xscrollcommand=h_scrollbar.set,
                                 selectmode='extended',
                                 show='headings')
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # 设置列（添加地址列）
        self.columns = ['序号', '骑手', '签收时间', '地址', '签收间隔(分钟)']
        self.tree['columns'] = self.columns
        
        # 设置列标题和初始宽度
        for col in self.columns:
            self.tree.heading(col, text=col, anchor='center',
                            command=lambda c=col: self.sort_by_column(c))
        
        # 设置列宽
        self.column_widths = {
            '序号': 80,
            '骑手': 150,
            '签收时间': 180,
            '地址': 250,
            '签收间隔(分钟)': 150
        }
        
        for col in self.columns:
            self.tree.column(col, width=self.column_widths[col], minwidth=60, anchor='center')
        
        # 添加双击复制功能
        self.tree.bind('<Double-Button-1>', self.copy_cell_value)
        
    def sort_by_column(self, col):
        """排序表格列"""
        if self.analysis_result is None:
            return
        
        if self.current_sort_column == col:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = col
            self.current_sort_reverse = False
        
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            data.append(values)
        
        if col == '序号':
            data.sort(key=lambda x: int(x[0]), reverse=self.current_sort_reverse)
        elif col == '骑手':
            data.sort(key=lambda x: x[1], reverse=self.current_sort_reverse)
        elif col == '签收时间':
            data.sort(key=lambda x: x[2], reverse=self.current_sort_reverse)
        elif col == '地址':
            data.sort(key=lambda x: x[3], reverse=self.current_sort_reverse)
        elif col == '签收间隔(分钟)':
            data.sort(key=lambda x: float(x[4]) if x[4] != '-' else -1, reverse=self.current_sort_reverse)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for row in data:
            self.tree.insert('', tk.END, values=row)
        
        for col_name in self.columns:
            if col_name == self.current_sort_column:
                arrow = ' ↓' if self.current_sort_reverse else ' ↑'
                self.tree.heading(col_name, text=col_name + arrow)
            else:
                self.tree.heading(col_name, text=col_name)
        
        self.status_label.config(text=f"已按'{col}'列排序{'（降序）' if self.current_sort_reverse else '（升序）'}", 
                                foreground="green")
        self.root.after(2000, lambda: self.status_label.config(
            text=f"当前骑手: {self.rider_var.get() if self.rider_var.get() else '未选择'}", 
            foreground="blue" if self.analysis_result is not None else "gray"))
    
    def copy_cell_value(self, event):
        """双击复制单元格内容"""
        try:
            item = self.tree.selection()[0]
            column = self.tree.identify_column(event.x)
            if column:
                col_index = int(column.replace('#', '')) - 1
                if 0 <= col_index < len(self.columns):
                    value = self.tree.item(item, 'values')[col_index]
                    self.root.clipboard_clear()
                    self.root.clipboard_append(str(value))
                    self.status_label.config(text=f"已复制: {value}", foreground="green")
                    self.root.after(2000, lambda: self.status_label.config(
                        text=f"当前骑手: {self.rider_var.get() if self.rider_var.get() else '未选择'}", 
                        foreground="blue" if self.analysis_result is not None else "gray"))
        except:
            pass
        
    def on_window_resize(self, event):
        """窗口大小改变时调整列宽"""
        if event.widget == self.root:
            width = self.root.winfo_width()
            if width > 800:
                total_width = width - 100
                col_count = len(self.columns)
                base_width = total_width // col_count
                
                self.tree.column('序号', width=max(80, base_width // 4))
                self.tree.column('骑手', width=max(120, base_width))
                self.tree.column('签收时间', width=max(180, base_width + 20))
                self.tree.column('地址', width=max(200, base_width + 50))
                self.tree.column('签收间隔(分钟)', width=max(150, base_width))
        
    def load_excel(self):
        """加载Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            self.data = pd.read_excel(file_path)
            
            # 检查必要的列是否存在
            if 'AD' not in self.data.columns and 'AD列' not in self.data.columns:
                if len(self.data.columns) >= 30:
                    original_columns = self.data.columns.tolist()
                    rider_col = original_columns[29]  # AD列索引
                    time_col = original_columns[23]   # X列索引
                    addr_col = original_columns[8]    # I列索引
                    self.data.rename(columns={rider_col: '骑手', time_col: '签收时间', addr_col: '地址'}, inplace=True)
                else:
                    messagebox.showerror("错误", "Excel文件中没有足够的列（需要AD列、X列和I列）")
                    return
            else:
                if 'AD' in self.data.columns:
                    self.data.rename(columns={'AD': '骑手'}, inplace=True)
                if 'AD列' in self.data.columns:
                    self.data.rename(columns={'AD列': '骑手'}, inplace=True)
                if 'X' in self.data.columns:
                    self.data.rename(columns={'X': '签收时间'}, inplace=True)
                if 'X列' in self.data.columns:
                    self.data.rename(columns={'X列': '签收时间'}, inplace=True)
                if 'I' in self.data.columns:
                    self.data.rename(columns={'I': '地址'}, inplace=True)
                if 'I列' in self.data.columns:
                    self.data.rename(columns={'I列': '地址'}, inplace=True)
            
            # 确保签收时间是datetime类型
            self.data['签收时间'] = pd.to_datetime(self.data['签收时间'], errors='coerce')
            
            # 确保地址列存在，如果不存在则创建空列
            if '地址' not in self.data.columns:
                self.data['地址'] = ""
            
            # 删除无效数据
            self.data = self.data.dropna(subset=['骑手', '签收时间'])
            
            self.all_riders = sorted(self.data['骑手'].astype(str).unique())
            self.rider_combo['values'] = self.all_riders
            self.rider_var.set("")
            
            self.status_label.config(text=f"已加载文件: {os.path.basename(file_path)}，共{len(self.data)}条记录", 
                                    foreground="green")
            messagebox.showinfo("成功", f"成功加载文件！\n共找到{len(self.all_riders)}名骑手，{len(self.data)}条签收记录")
            
            self.clear_table()
            self.update_key_metrics(None)
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件时出错：\n{str(e)}")
            self.status_label.config(text="加载失败", foreground="red")
    
    def on_rider_search(self, event):
        """实时搜索骑手"""
        search_text = self.rider_var.get().strip()
        
        if not search_text:
            self.rider_combo['values'] = self.all_riders
        else:
            matched_riders = [rider for rider in self.all_riders if search_text.lower() in rider.lower()]
            self.rider_combo['values'] = matched_riders
            
            if len(matched_riders) == 1:
                self.rider_var.set(matched_riders[0])
        
        if self.rider_combo['values']:
            self.rider_combo.event_generate('<Down>')
    
    def on_rider_selected(self, event):
        """从下拉列表选择骑手"""
        selected_rider = self.rider_var.get()
        if selected_rider and selected_rider in self.all_riders:
            self.query_rider_data(selected_rider)
    
    def on_rider_enter(self, event):
        """回车确认查询"""
        self.query_selected_rider()
    
    def query_selected_rider(self):
        """查询选中的骑手"""
        rider = self.rider_var.get().strip()
        if not rider:
            messagebox.showwarning("警告", "请选择或输入骑手名称")
            return
        
        if rider not in self.all_riders:
            matched_riders = [r for r in self.all_riders if rider.lower() in r.lower()]
            if len(matched_riders) == 1:
                rider = matched_riders[0]
                self.rider_var.set(rider)
            elif len(matched_riders) > 1:
                self.rider_combo['values'] = matched_riders
                messagebox.showinfo("提示", f"找到多个匹配的骑手，请从下拉列表中选择")
                self.rider_combo.event_generate('<Down>')
                return
            else:
                messagebox.showwarning("警告", f"未找到骑手：{rider}")
                return
        
        self.query_rider_data(rider)
    
    def query_rider_data(self, rider):
        """查询骑手数据"""
        try:
            rider_data = self.data[self.data['骑手'].astype(str) == rider].copy()
            
            if len(rider_data) == 0:
                messagebox.showinfo("提示", f"骑手'{rider}'没有签收记录")
                return
            
            # 按签收时间排序
            rider_data = rider_data.sort_values('签收时间').reset_index(drop=True)
            
            # 计算时间间隔（分钟）
            time_diffs_minutes = []
            for i in range(len(rider_data)):
                if i == 0:
                    time_diffs_minutes.append(None)
                else:
                    diff = rider_data.loc[i, '签收时间'] - rider_data.loc[i-1, '签收时间']
                    time_diffs_minutes.append(round(diff.total_seconds() / 60, 1))
            
            rider_data['签收间隔(分钟)'] = time_diffs_minutes
            rider_data['签收时间(格式化)'] = rider_data['签收时间'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 处理地址列，确保是字符串类型
            rider_data['地址'] = rider_data['地址'].fillna('').astype(str)
            
            self.analysis_result = rider_data
            
            # 显示在表格中
            self.display_results(rider_data)
            
            # 显示统计信息
            self.display_statistics(rider_data)
            
            # 更新关键指标
            self.update_key_metrics(rider_data)
            
            self.status_label.config(text=f"当前骑手: {rider} (共{len(rider_data)}条记录)", 
                                    foreground="blue")
            
            # 重置排序状态
            self.current_sort_column = None
            self.current_sort_reverse = False
            
            # 更新列标题
            for col_name in self.columns:
                self.tree.heading(col_name, text=col_name)
            
            self.rider_combo['values'] = self.all_riders
            
        except Exception as e:
            messagebox.showerror("错误", f"查询数据时出错：\n{str(e)}")
            self.status_label.config(text="查询失败", foreground="red")
    
    def reset_search(self):
        """重置搜索"""
        self.rider_var.set("")
        self.rider_combo['values'] = self.all_riders
        self.clear_table()
        self.update_key_metrics(None)
        self.status_label.config(text="已重置搜索", foreground="gray")
    
    def clear_table(self):
        """清空表格和统计信息"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.stats_text.delete(1.0, tk.END)
        self.analysis_result = None
    
    def display_results(self, data):
        """在Treeview中显示结果"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for idx, row in data.iterrows():
            interval_min = f"{row['签收间隔(分钟)']:.1f}" if pd.notna(row['签收间隔(分钟)']) else "-"
            address = row['地址'] if row['地址'] != 'nan' else ""
            
            values = [
                idx + 1,
                row['骑手'],
                row['签收时间(格式化)'],
                address,
                interval_min
            ]
            
            tag = 'first_row' if idx == 0 else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
        
        self.tree.tag_configure('first_row', background='#f0f0f0')
        self.auto_fit_columns()
    
    def auto_fit_columns(self):
        """自动调整列宽以适应内容"""
        for col in self.columns:
            max_width = len(col) * 15
            for item in self.tree.get_children():
                value = self.tree.item(item, 'values')[self.columns.index(col)]
                if value:
                    width = len(str(value)) * 12
                    if width > max_width:
                        max_width = min(width, 350)
            self.tree.column(col, width=max(max_width, self.column_widths.get(col, 80)))
    
    def display_statistics(self, data):
        """显示详细统计信息"""
        self.stats_text.delete(1.0, tk.END)
        
        total_records = len(data)
        valid_intervals = data['签收间隔(分钟)'][1:].dropna()
        total_duration_minutes = (data.iloc[-1]['签收时间'] - data.iloc[0]['签收时间']).total_seconds() / 60
        
        stats_text = "=" * 70 + "\n"
        stats_text += " " * 20 + "骑手签收时间详细统计报告\n"
        stats_text += "=" * 70 + "\n\n"
        
        stats_text += f"骑手姓名：{data.iloc[0]['骑手']}\n"
        stats_text += f"总签收次数：{total_records} 次\n"
        stats_text += f"开始时间：{data.iloc[0]['签收时间(格式化)']}\n"
        stats_text += f"结束时间：{data.iloc[-1]['签收时间(格式化)']}\n"
        
        total_hours = int(total_duration_minutes // 60)
        total_minutes = int(total_duration_minutes % 60)
        stats_text += f"总工作时长：{total_hours}小时{total_minutes}分钟 ({total_duration_minutes:.1f}分钟)\n\n"
        
        if len(valid_intervals) > 0:
            stats_text += "-" * 70 + "\n"
            stats_text += " " * 20 + "签收间隔统计（分钟）\n"
            stats_text += "-" * 70 + "\n\n"
            
            avg_interval = valid_intervals.mean()
            min_interval = valid_intervals.min()
            max_interval = valid_intervals.max()
            median_interval = valid_intervals.median()
            std_interval = valid_intervals.std()
            
            stats_text += f"平均间隔：{avg_interval:.1f} 分钟\n"
            stats_text += f"中位数间隔：{median_interval:.1f} 分钟\n"
            stats_text += f"最短间隔：{min_interval:.1f} 分钟\n"
            stats_text += f"最长间隔：{max_interval:.1f} 分钟\n"
            stats_text += f"标准差：{std_interval:.1f} 分钟\n\n"
            
            stats_text += "-" * 70 + "\n"
            stats_text += " " * 20 + "签收频率\n"
            stats_text += "-" * 70 + "\n\n"
            
            frequency_per_hour = total_records / (total_duration_minutes / 60) if total_duration_minutes > 0 else 0
            stats_text += f"签收频率：{frequency_per_hour:.2f} 次/小时\n"
            if total_records > 1:
                stats_text += f"平均间隔时间：{total_duration_minutes/(total_records-1):.1f} 分钟/次\n"
        else:
            stats_text += "\n注意：只有一条签收记录，无法计算时间间隔统计信息。\n"
        
        stats_text += "\n" + "=" * 70 + "\n"
        stats_text += "提示：双击表格单元格可复制内容 | 点击列标题可排序\n"
        
        self.stats_text.insert(1.0, stats_text)
    
    def export_results(self):
        """导出分析结果到Excel"""
        if self.analysis_result is None:
            messagebox.showwarning("警告", "没有分析结果可导出，请先查询骑手数据")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存分析结果",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if file_path:
                # 准备导出数据（包含地址）
                export_data = self.analysis_result[['骑手', '签收时间(格式化)', '地址', '签收间隔(分钟)']].copy()
                export_data.rename(columns={
                    '签收时间(格式化)': '签收时间',
                    '签收间隔(分钟)': '签收间隔(分钟)'
                }, inplace=True)
                
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    export_data.to_excel(writer, sheet_name='签收记录', index=False)
                    
                    valid_intervals = self.analysis_result['签收间隔(分钟)'][1:].dropna()
                    if len(valid_intervals) > 0:
                        total_duration_minutes = (self.analysis_result.iloc[-1]['签收时间'] - self.analysis_result.iloc[0]['签收时间']).total_seconds() / 60
                        
                        stats_data = {
                            '统计指标': ['骑手名称', '总签收次数', '开始时间', '结束时间', 
                                      '总工作时长(分钟)', '平均间隔(分钟)', '中位数间隔(分钟)',
                                      '最短间隔(分钟)', '最长间隔(分钟)', '标准差(分钟)', 
                                      '签收频率(次/小时)'],
                            '数值': [
                                self.analysis_result.iloc[0]['骑手'],
                                len(self.analysis_result),
                                self.analysis_result.iloc[0]['签收时间(格式化)'],
                                self.analysis_result.iloc[-1]['签收时间(格式化)'],
                                f"{total_duration_minutes:.1f}",
                                f"{valid_intervals.mean():.1f}",
                                f"{valid_intervals.median():.1f}",
                                f"{valid_intervals.min():.1f}",
                                f"{valid_intervals.max():.1f}",
                                f"{valid_intervals.std():.1f}",
                                f"{len(self.analysis_result) / (total_duration_minutes / 60):.2f}"
                            ]
                        }
                        stats_df = pd.DataFrame(stats_data)
                        stats_df.to_excel(writer, sheet_name='统计信息', index=False)
                    else:
                        stats_data = {
                            '统计指标': ['骑手名称', '总签收次数', '开始时间', '结束时间', '总工作时长(分钟)', '说明'],
                            '数值': [
                                self.analysis_result.iloc[0]['骑手'],
                                len(self.analysis_result),
                                self.analysis_result.iloc[0]['签收时间(格式化)'],
                                self.analysis_result.iloc[-1]['签收时间(格式化)'],
                                f"{(self.analysis_result.iloc[-1]['签收时间'] - self.analysis_result.iloc[0]['签收时间']).total_seconds() / 60:.1f}",
                                '只有一条记录，无法计算时间间隔'
                            ]
                        }
                        stats_df = pd.DataFrame(stats_data)
                        stats_df.to_excel(writer, sheet_name='统计信息', index=False)
                
                messagebox.showinfo("成功", f"分析结果已导出到：\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出文件时出错：\n{str(e)}")

def main():
    root = tk.Tk()
    app = RiderDataAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()