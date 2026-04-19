#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TXT通讯录转换工具 - 简约圆润灰黑版
支持格式：CSV (Excel可打开), VCF (手机通讯录)
"""

import csv
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

class ContactConverter:
    def __init__(self):
        self.contacts = []
    
    def parse_txt_file(self, file_path: str, callback=None) -> bool:
        """解析TXT文件，支持多种分隔符"""
        try:
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise Exception("无法识别文件编码")
            
            lines = content.strip().split('\n')
            self.contacts = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # 尝试多种分隔符
                parts = None
                if ',' in line:
                    parts = line.split(',')
                elif '，' in line:
                    parts = line.split('，')
                elif '\t' in line:
                    parts = line.split('\t')
                elif '|' in line:
                    parts = line.split('|')
                elif ' ' in line:
                    parts = line.split(' ')
                else:
                    if callback:
                        callback(f"⚠ 第{line_num}行格式无法识别")
                    continue
                
                parts = [p.strip() for p in parts]
                
                if len(parts) >= 3:
                    contact = {
                        'name': parts[0],
                        'phone': parts[1],
                        'company': parts[2]
                    }
                elif len(parts) == 2:
                    contact = {
                        'name': parts[0],
                        'phone': parts[1],
                        'company': ''
                    }
                else:
                    if callback:
                        callback(f"⚠ 第{line_num}行数据不完整")
                    continue
                
                if contact['phone']:
                    self.contacts.append(contact)
            
            return True
            
        except Exception as e:
            if callback:
                callback(f"✗ 读取文件失败: {e}")
            return False
    
    def save_to_csv(self, output_path: str) -> bool:
        """保存为CSV格式"""
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['姓名', '电话', '公司']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for contact in self.contacts:
                    writer.writerow({
                        '姓名': contact['name'],
                        '电话': contact['phone'],
                        '公司': contact['company']
                    })
            return True
        except Exception as e:
            print(f"保存CSV文件失败: {e}")
            return False
    
    def save_to_vcf(self, output_path: str) -> bool:
        """保存为VCF格式"""
        try:
            with open(output_path, 'w', encoding='utf-8') as vcffile:
                for contact in self.contacts:
                    vcffile.write("BEGIN:VCARD\n")
                    vcffile.write("VERSION:3.0\n")
                    vcffile.write(f"FN:{contact['name']}\n")
                    vcffile.write(f"N:{contact['name']};;;\n")
                    phone = contact['phone'].replace(' ', '').replace('-', '')
                    vcffile.write(f"TEL;TYPE=CELL:{phone}\n")
                    if contact['company']:
                        vcffile.write(f"ORG:{contact['company']}\n")
                    vcffile.write("END:VCARD\n\n")
            return True
        except Exception as e:
            print(f"保存VCF文件失败: {e}")
            return False


class RoundedWidget:
    """圆角组件辅助类"""
    
    @staticmethod
    def create_rounded_canvas(parent, width, height, radius, color, **kwargs):
        """创建圆角矩形画布"""
        canvas = tk.Canvas(parent, width=width, height=height, 
                          highlightthickness=0, bg=color, **kwargs)
        canvas.create_rounded_rect = lambda x1, y1, x2, y2, r, fill: canvas.create_polygon(
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1,
            smooth=True, fill=fill, outline='')
        return canvas


class ConverterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("通讯录转换工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 灰黑色调配色方案
        self.colors = {
            'bg_primary': '#F5F5F5',      # 主背景浅灰
            'bg_secondary': '#FFFFFF',    # 次背景纯白
            'bg_card': '#FFFFFF',         # 卡片背景白
            'bg_hover': '#F0F0F0',        # 悬停背景
            'fg_primary': '#2C2C2C',      # 主文字深灰
            'fg_secondary': '#6B6B6B',    # 次文字中灰
            'fg_light': '#9A9A9A',        # 浅文字
            'accent': '#4A4A4A',          # 强调色中灰
            'accent_light': '#6B6B6B',    # 浅强调色
            'accent_dark': '#2C2C2C',     # 深强调色
            'border': '#E0E0E0',          # 边框浅灰
            'border_focus': '#9A9A9A',    # 焦点边框
            'success': '#5A8F5A',         # 成功绿（柔和）
            'warning': '#C9A03D',         # 警告黄（柔和）
            'error': '#B55A5A',           # 错误红（柔和）
            'button': '#4A4A4A',          # 按钮深灰
            'button_hover': '#5C5C5C',    # 按钮悬停
            'button_text': '#FFFFFF',     # 按钮文字白
            'table_header': '#F8F8F8',    # 表头浅灰
            'table_alt': '#FBFBFB',       # 表格交替行
            'shadow': '#E8E8E8'           # 阴影色
        }
        
        self.converter = ContactConverter()
        self.current_file = None
        
        self.setup_ui()
        self.apply_styles()
        
    def apply_styles(self):
        """应用圆润简约样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 全局字体
        default_font = ('Microsoft YaHei', 10)
        style.configure('.', font=default_font)
        
        # 框架样式 - 圆角效果通过画布实现
        style.configure('Card.TFrame', background=self.colors['bg_card'])
        style.configure('TFrame', background=self.colors['bg_primary'])
        
        # 标签样式
        style.configure('Title.TLabel', 
                       font=('Microsoft YaHei', 22, 'bold'),
                       foreground=self.colors['fg_primary'],
                       background=self.colors['bg_primary'])
        
        style.configure('Subtitle.TLabel',
                       font=('Microsoft YaHei', 10),
                       foreground=self.colors['fg_secondary'],
                       background=self.colors['bg_primary'])
        
        style.configure('CardTitle.TLabel',
                       font=('Microsoft YaHei', 12, 'bold'),
                       foreground=self.colors['fg_primary'],
                       background=self.colors['bg_card'])
        
        # 按钮样式
        style.configure('Primary.TButton',
                       background=self.colors['button'],
                       foreground=self.colors['button_text'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=(20, 10))
        style.map('Primary.TButton',
                 background=[('active', self.colors['button_hover'])])
        
        style.configure('Secondary.TButton',
                       background=self.colors['bg_card'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=1,
                       focuscolor='none',
                       font=('Microsoft YaHei', 10),
                       padding=(15, 8))
        style.map('Secondary.TButton',
                 background=[('active', self.colors['bg_hover'])],
                 bordercolor=[('active', self.colors['border_focus'])])
        
        # 输入框样式
        style.configure('TEntry',
                       fieldbackground=self.colors['bg_card'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=1,
                       lightcolor=self.colors['border'],
                       darkcolor=self.colors['border'],
                       focuscolor=self.colors['border_focus'],
                       padding=(8, 6),
                       font=('Consolas', 10))
        
        # 文本框样式
        style.configure('TText',
                       background=self.colors['bg_card'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=1,
                       font=('Consolas', 9))
        
        # 标签框架样式
        style.configure('TLabelframe',
                       background=self.colors['bg_card'],
                       foreground=self.colors['fg_primary'],
                       borderwidth=1,
                       relief='solid')
        style.configure('TLabelframe.Label',
                       background=self.colors['bg_card'],
                       foreground=self.colors['accent'],
                       font=('Microsoft YaHei', 10, 'bold'))
        
        # 树形视图样式
        style.configure('Treeview',
                       background=self.colors['bg_card'],
                       foreground=self.colors['fg_primary'],
                       fieldbackground=self.colors['bg_card'],
                       borderwidth=0,
                       font=('Microsoft YaHei', 9),
                       rowheight=32)
        style.configure('Treeview.Heading',
                       background=self.colors['table_header'],
                       foreground=self.colors['fg_primary'],
                       font=('Microsoft YaHei', 10, 'bold'),
                       borderwidth=0)
        style.map('Treeview',
                 background=[('selected', self.colors['accent_light'])],
                 foreground=[('selected', 'white')])
        
        # 滚动条样式
        style.configure('Vertical.TScrollbar',
                       background=self.colors['border'],
                       troughcolor=self.colors['bg_primary'],
                       arrowcolor=self.colors['fg_secondary'],
                       borderwidth=0,
                       width=10)
        
        # 下拉框样式
        style.configure('TCombobox',
                       fieldbackground=self.colors['bg_card'],
                       foreground=self.colors['fg_primary'],
                       selectbackground=self.colors['accent_light'],
                       padding=(8, 6))
    
    def create_rounded_frame(self, parent, **kwargs):
        """创建圆角框架"""
        frame = tk.Frame(parent, bg=self.colors['bg_card'], **kwargs)
        return frame
    
    def setup_ui(self):
        """设置UI界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题区域
        title_frame = tk.Frame(main_container, bg=self.colors['bg_primary'])
        title_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = tk.Label(title_frame, text="通讯录转换工具",
                              font=('Microsoft YaHei', 24, 'bold'),
                              fg=self.colors['fg_primary'],
                              bg=self.colors['bg_primary'])
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="TXT文件转CSV/VCF | 智能识别多种分隔符",
                                 font=('Microsoft YaHei', 10),
                                 fg=self.colors['fg_secondary'],
                                 bg=self.colors['bg_primary'])
        subtitle_label.pack(pady=(5, 0))
        
        # 分隔线
        separator = tk.Frame(main_container, height=1, bg=self.colors['border'])
        separator.pack(fill=tk.X, pady=(0, 20))
        
        # 文件选择卡片
        file_card = self.create_rounded_frame(main_container, relief='flat', bd=0)
        file_card.pack(fill=tk.X, pady=(0, 15))
        
        # 模拟圆角效果
        file_inner = tk.Frame(file_card, bg=self.colors['bg_card'], bd=0)
        file_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # 卡片头部
        card_header = tk.Frame(file_inner, bg=self.colors['bg_card'], height=45)
        card_header.pack(fill=tk.X, padx=20, pady=(15, 0))
        
        card_title = tk.Label(card_header, text="文件选择",
                             font=('Microsoft YaHei', 12, 'bold'),
                             fg=self.colors['fg_primary'],
                             bg=self.colors['bg_card'])
        card_title.pack(side=tk.LEFT)
        
        # 文件选择内容
        file_content = tk.Frame(file_inner, bg=self.colors['bg_card'])
        file_content.pack(fill=tk.X, padx=20, pady=(10, 20))
        
        self.file_path_var = tk.StringVar()
        file_entry = tk.Entry(file_content, textvariable=self.file_path_var,
                             font=('Consolas', 10),
                             bg=self.colors['bg_card'],
                             fg=self.colors['fg_primary'],
                             relief='solid', bd=1,
                             highlightcolor=self.colors['border_focus'])
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=6)
        
        browse_btn = ttk.Button(file_content, text="浏览文件", 
                               style='Secondary.TButton', 
                               command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)
        
        # 日志卡片
        log_card = self.create_rounded_frame(main_container, relief='flat', bd=0)
        log_card.pack(fill=tk.X, pady=(0, 15))
        
        log_inner = tk.Frame(log_card, bg=self.colors['bg_card'], bd=0)
        log_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        log_header = tk.Frame(log_inner, bg=self.colors['bg_card'], height=45)
        log_header.pack(fill=tk.X, padx=20, pady=(15, 0))
        
        log_title = tk.Label(log_header, text="处理日志",
                            font=('Microsoft YaHei', 12, 'bold'),
                            fg=self.colors['fg_primary'],
                            bg=self.colors['bg_card'])
        log_title.pack(side=tk.LEFT)
        
        log_content = tk.Frame(log_inner, bg=self.colors['bg_card'])
        log_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # 文本框
        text_frame = tk.Frame(log_content, bg=self.colors['bg_card'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = tk.Text(text_frame, height=5, wrap=tk.WORD,
                                bg=self.colors['bg_card'],
                                fg=self.colors['fg_primary'],
                                insertbackground=self.colors['accent'],
                                font=('Consolas', 9),
                                relief='solid', bd=1,
                                selectbackground=self.colors['accent_light'])
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", 
                                     command=self.info_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.configure(yscrollcommand=log_scrollbar.set)
        
        # 预览卡片
        preview_card = self.create_rounded_frame(main_container, relief='flat', bd=0)
        preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        preview_inner = tk.Frame(preview_card, bg=self.colors['bg_card'], bd=0)
        preview_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        preview_header = tk.Frame(preview_inner, bg=self.colors['bg_card'], height=45)
        preview_header.pack(fill=tk.X, padx=20, pady=(15, 0))
        
        preview_title = tk.Label(preview_header, text="数据预览",
                                font=('Microsoft YaHei', 12, 'bold'),
                                fg=self.colors['fg_primary'],
                                bg=self.colors['bg_card'])
        preview_title.pack(side=tk.LEFT)
        
        self.count_label = tk.Label(preview_header, text="共 0 条记录",
                                   font=('Microsoft YaHei', 9),
                                   fg=self.colors['fg_secondary'],
                                   bg=self.colors['bg_card'])
        self.count_label.pack(side=tk.RIGHT)
        
        preview_content = tk.Frame(preview_inner, bg=self.colors['bg_card'])
        preview_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))
        
        # 树形视图
        tree_container = tk.Frame(preview_content, bg=self.colors['bg_card'])
        tree_container.pack(fill=tk.BOTH, expand=True)
        
        columns = ('姓名', '电话', '公司')
        self.tree = ttk.Treeview(tree_container, columns=columns, show='headings', height=8)
        
        self.tree.heading('姓名', text='姓名')
        self.tree.heading('电话', text='电话')
        self.tree.heading('公司', text='公司')
        
        self.tree.column('姓名', width=180, anchor=tk.W)
        self.tree.column('电话', width=200, anchor=tk.W)
        self.tree.column('公司', width=320, anchor=tk.W)
        
        tree_scroll_y = ttk.Scrollbar(tree_container, orient="vertical", 
                                     command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_container, orient="horizontal", 
                                     command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set,
                           xscrollcommand=tree_scroll_x.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        
        # 按钮区域
        button_card = self.create_rounded_frame(main_container, relief='flat', bd=0)
        button_card.pack(fill=tk.X)
        
        button_inner = tk.Frame(button_card, bg=self.colors['bg_card'], bd=0)
        button_inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        button_content = tk.Frame(button_inner, bg=self.colors['bg_card'])
        button_content.pack(fill=tk.X, padx=20, pady=15)
        
        # 左侧按钮组
        left_buttons = tk.Frame(button_content, bg=self.colors['bg_card'])
        left_buttons.pack(side=tk.LEFT)
        
        self.csv_btn = ttk.Button(left_buttons, text="转换为 CSV", 
                                 style='Primary.TButton',
                                 command=lambda: self.convert('csv'),
                                 state='disabled')
        self.csv_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.vcf_btn = ttk.Button(left_buttons, text="转换为 VCF",
                                 style='Primary.TButton',
                                 command=lambda: self.convert('vcf'),
                                 state='disabled')
        self.vcf_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.both_btn = ttk.Button(left_buttons, text="同时转换",
                                  style='Primary.TButton',
                                  command=lambda: self.convert('both'),
                                  state='disabled')
        self.both_btn.pack(side=tk.LEFT)
        
        # 右侧按钮组
        right_buttons = tk.Frame(button_content, bg=self.colors['bg_card'])
        right_buttons.pack(side=tk.RIGHT)
        
        clear_btn = ttk.Button(right_buttons, text="清空数据",
                              style='Secondary.TButton',
                              command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        exit_btn = ttk.Button(right_buttons, text="退出程序",
                             style='Secondary.TButton',
                             command=self.root.quit)
        exit_btn.pack(side=tk.LEFT)
        
        # 状态栏
        status_bar = tk.Frame(main_container, bg=self.colors['bg_primary'], height=30)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = tk.Label(status_bar, text="就绪",
                                    font=('Microsoft YaHei', 9),
                                    fg=self.colors['fg_secondary'],
                                    bg=self.colors['bg_primary'])
        self.status_label.pack(side=tk.LEFT)
        
        # 初始消息
        self.log_message("欢迎使用通讯录转换工具")
        self.log_message("支持分隔符: 英文逗号、中文逗号、空格、制表符、竖线")
        self.log_message("支持2或3个字段: 姓名 电话 [公司]")
    
    def log_message(self, msg):
        """添加日志消息"""
        self.info_text.insert(tk.END, f"{msg}\n")
        self.info_text.see(tk.END)
        self.root.update()
    
    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="选择TXT文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.load_file(filename)
    
    def load_file(self, filename):
        """加载文件"""
        self.current_file = filename
        self.log_message(f"📁 正在读取: {os.path.basename(filename)}")
        self.status_label.config(text="正在处理...")
        
        def log_callback(msg):
            self.root.after(0, lambda: self.log_message(msg))
        
        def process():
            success = self.converter.parse_txt_file(filename, log_callback)
            if success:
                count = len(self.converter.contacts)
                self.root.after(0, lambda: self.update_preview())
                self.root.after(0, lambda: self.log_message(f"✓ 成功读取 {count} 条联系人记录"))
                self.root.after(0, lambda: self.count_label.config(text=f"共 {count} 条记录"))
                self.root.after(0, lambda: self.csv_btn.config(state='normal'))
                self.root.after(0, lambda: self.vcf_btn.config(state='normal'))
                self.root.after(0, lambda: self.both_btn.config(state='normal'))
                self.root.after(0, lambda: self.status_label.config(text="就绪"))
            else:
                self.root.after(0, lambda: self.status_label.config(text="读取失败"))
        
        threading.Thread(target=process, daemon=True).start()
    
    def update_preview(self):
        """更新预览表格"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, contact in enumerate(self.converter.contacts[:50]):
            self.tree.insert('', 'end', values=(
                contact['name'],
                contact['phone'],
                contact['company'] if contact['company'] else '—'
            ))
        
        if len(self.converter.contacts) > 50:
            self.log_message(f"ℹ 预览显示前50条，共{len(self.converter.contacts)}条记录")
    
    def convert(self, format_type):
        """转换文件"""
        if not self.converter.contacts:
            messagebox.showwarning("提示", "没有数据可转换，请先加载TXT文件")
            return
        
        if format_type == 'csv':
            self.save_single('csv', 'CSV文件', '.csv', self.converter.save_to_csv)
        elif format_type == 'vcf':
            self.save_single('vcf', 'VCF文件', '.vcf', self.converter.save_to_vcf)
        else:
            self.save_both()
    
    def save_single(self, format_type, format_name, extension, save_func):
        """保存单格式"""
        default_name = f"{os.path.splitext(os.path.basename(self.current_file))[0]}_通讯录{extension}"
        output_file = filedialog.asksaveasfilename(
            title=f"保存{format_name}",
            defaultextension=extension,
            filetypes=[(format_name, f"*{extension}")],
            initialfile=default_name
        )
        
        if output_file:
            self.status_label.config(text="正在保存...")
            if save_func(output_file):
                self.log_message(f"✓ {format_name}已保存: {os.path.basename(output_file)}")
                messagebox.showinfo("成功", f"{format_name}保存成功！\n{output_file}")
            else:
                self.log_message(f"✗ {format_name}保存失败")
                messagebox.showerror("错误", f"{format_name}保存失败")
            self.status_label.config(text="就绪")
    
    def save_both(self):
        """同时保存两种格式"""
        # 保存CSV
        csv_default = f"{os.path.splitext(os.path.basename(self.current_file))[0]}_通讯录.csv"
        csv_file = filedialog.asksaveasfilename(
            title="保存CSV文件",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv")],
            initialfile=csv_default
        )
        
        if csv_file:
            self.status_label.config(text="正在保存CSV...")
            if self.converter.save_to_csv(csv_file):
                self.log_message(f"✓ CSV已保存: {os.path.basename(csv_file)}")
            else:
                self.log_message(f"✗ CSV保存失败")
                messagebox.showerror("错误", "CSV文件保存失败")
                self.status_label.config(text="就绪")
                return
        
        # 保存VCF
        vcf_default = f"{os.path.splitext(os.path.basename(self.current_file))[0]}_通讯录.vcf"
        vcf_file = filedialog.asksaveasfilename(
            title="保存VCF文件",
            defaultextension=".vcf",
            filetypes=[("VCF文件", "*.vcf")],
            initialfile=vcf_default
        )
        
        if vcf_file:
            self.status_label.config(text="正在保存VCF...")
            if self.converter.save_to_vcf(vcf_file):
                self.log_message(f"✓ VCF已保存: {os.path.basename(vcf_file)}")
                messagebox.showinfo("成功", "两种格式均已保存成功！")
            else:
                self.log_message(f"✗ VCF保存失败")
                messagebox.showerror("错误", "VCF文件保存失败")
        
        self.status_label.config(text="就绪")
    
    def clear_all(self):
        """清空所有数据"""
        self.converter.contacts = []
        self.current_file = None
        self.file_path_var.set("")
        self.info_text.delete(1.0, tk.END)
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.csv_btn.config(state='disabled')
        self.vcf_btn.config(state='disabled')
        self.both_btn.config(state='disabled')
        self.count_label.config(text="共 0 条记录")
        self.log_message("✓ 已清空所有数据")
        self.status_label.config(text="就绪")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    app = ConverterGUI()
    app.run()


if __name__ == "__main__":
    main()