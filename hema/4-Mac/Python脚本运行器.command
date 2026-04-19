#!/bin/bash

# 获取当前脚本所在目录
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
cd "${SCRIPT_DIR}"

# 检查 python3
if ! command -v python3 &> /dev/null; then
    osascript -e 'display dialog "错误：未找到 python3\n请先安装 Python3" buttons {"确定"} default button 1 with icon stop'
    exit 1
fi

# 创建临时 Python 脚本
TEMP_PYTHON_SCRIPT="/tmp/python_runner_$$.py"

# 生成 Python 脚本
cat > "$TEMP_PYTHON_SCRIPT" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class PythonScriptRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Python脚本运行器")
        self.root.geometry("800x700")
        
        # 设置全局字体大小
        self.default_font = ("Arial", 20)
        
        # 设置窗口居中
        self.root.update_idletasks()
        width = 800
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.current_process = None
        self.create_widgets()
        
        # 绑定拖拽事件（使用 bind 方法）
        self.setup_drag_drop()
        
    def setup_drag_drop(self):
        """设置拖拽功能 - 使用 bind 方法"""
        # 为输入框绑定鼠标事件来实现拖拽
        self.entry.bind('<Button-1>', self.on_click)
        self.entry.bind('<B1-Motion>', self.on_drag)
        
        # 使用 tkinterdnd2 不可用时的替代方案：监听粘贴
        self.entry.bind('<Control-v>', self.on_paste)
        self.entry.bind('<Command-v>', self.on_paste)
        
        # 提示用户可以使用粘贴或浏览按钮
        self.status.config(text="✅ 就绪 - 可以使用浏览按钮或 Ctrl+V 粘贴文件路径")
        
    def on_click(self, event):
        """鼠标点击事件"""
        self.entry.focus_set()
        
    def on_drag(self, event):
        """拖拽事件 - 实际上在 tkinter 中需要通过其他方式实现"""
        pass
        
    def on_paste(self, event):
        """处理粘贴事件"""
        try:
            # 获取剪贴板内容
            clipboard_text = self.root.clipboard_get()
            if clipboard_text and clipboard_text.strip().endswith('.py'):
                file_path = clipboard_text.strip()
                # 处理可能的路径格式
                if file_path.startswith('file://'):
                    file_path = file_path[7:]
                if os.path.exists(file_path):
                    self.file_path.set(file_path)
                    self.status.config(text=f"📄 已粘贴: {os.path.basename(file_path)}")
                else:
                    self.status.config(text="❌ 无效的文件路径")
        except:
            pass
        return "break"
        
    def create_widgets(self):
        # 标题
        title = tk.Label(self.root, text="🐍 Python脚本运行器", 
                        font=("Arial", 24, "bold"))
        title.pack(pady=20)
        
        # 文件选择框架
        file_frame = tk.Frame(self.root)
        file_frame.pack(pady=20, padx=20, fill=tk.X)
        
        self.file_path = tk.StringVar()
        self.entry = tk.Entry(file_frame, textvariable=self.file_path, 
                             font=self.default_font)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), pady=5)
        
        browse_btn = tk.Button(file_frame, text="📁 浏览", command=self.browse_file,
                              bg="white", fg="black", font=self.default_font,
                              padx=20, pady=5)
        browse_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # 拖拽提示标签
        drag_label = tk.Label(self.root, 
                             text="💡 提示：\n1. 点击「浏览」按钮选择文件\n2. 或直接复制文件路径后 Ctrl+V 粘贴\n3. 或将文件拖拽到终端窗口获取路径后粘贴",
                             font=("Arial", 14), fg="blue", bg="#ffffcc",
                             justify=tk.LEFT)
        drag_label.pack(pady=10, padx=20, fill=tk.X)
        
        # 按钮框架
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        self.run_btn = tk.Button(btn_frame, text="▶ 运行脚本", command=self.run_script,
                                bg="white", fg="black", font=self.default_font,
                                padx=40, pady=10, width=10)
        self.run_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ 停止运行", command=self.stop_script,
                                 bg="white", fg="black", font=self.default_font,
                                 padx=40, pady=10, width=10, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        clear_btn = tk.Button(btn_frame, text="🗑 清空输出", command=self.clear_output,
                             bg="white", fg="black", font=self.default_font,
                             padx=40, pady=10, width=10)
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # 快捷路径按钮框架
        quick_frame = tk.Frame(self.root)
        quick_frame.pack(pady=10)
        
        desktop_btn = tk.Button(quick_frame, text="📂 桌面", command=lambda: self.set_quick_path("~/Desktop"),
                               bg="white", fg="black", font=("Arial", 16),
                               padx=20, pady=5)
        desktop_btn.pack(side=tk.LEFT, padx=5)
        
        downloads_btn = tk.Button(quick_frame, text="📂 下载", command=lambda: self.set_quick_path("~/Downloads"),
                                 bg="white", fg="black", font=("Arial", 16),
                                 padx=20, pady=5)
        downloads_btn.pack(side=tk.LEFT, padx=5)
        
        documents_btn = tk.Button(quick_frame, text="📂 文稿", command=lambda: self.set_quick_path("~/Documents"),
                                 bg="white", fg="black", font=("Arial", 16),
                                 padx=20, pady=5)
        documents_btn.pack(side=tk.LEFT, padx=5)
        
        # 输出区域
        output_frame = tk.LabelFrame(self.root, text="运行输出", font=self.default_font)
        output_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        self.output = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD,
                                                font=("Courier New", 18),
                                                height=12,
                                                bg="white",
                                                fg="black")
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 状态栏
        self.status = tk.Label(self.root, text="✅ 就绪 - 请选择要运行的Python文件", 
                              relief=tk.SUNKEN, anchor=tk.W, font=self.default_font,
                              bg="#f0f0f0", fg="black")
        self.status.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
    def set_quick_path(self, path):
        """快速设置路径到常用文件夹"""
        expanded_path = os.path.expanduser(path)
        self.status.config(text=f"📂 已切换到: {expanded_path}")
        # 可选：打开文件选择对话框在该目录
        filename = filedialog.askopenfilename(
            title=f"从 {expanded_path} 选择Python文件",
            initialdir=expanded_path,
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.status.config(text=f"📄 已选择: {os.path.basename(filename)}")
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="选择Python文件",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        if filename:
            self.file_path.set(filename)
            self.status.config(text=f"📄 已选择: {os.path.basename(filename)}")
            
    def run_script(self):
        file_path = self.file_path.get().strip()
        
        if not file_path:
            messagebox.showerror("错误", "请选择或粘贴一个Python文件路径")
            return
            
        if not os.path.exists(file_path):
            messagebox.showerror("错误", f"文件不存在:\n{file_path}")
            return
            
        if not file_path.endswith('.py'):
            messagebox.showerror("错误", "只能运行.py文件")
            return
            
        # 清空输出
        self.output.delete(1.0, tk.END)
        
        # 禁用运行按钮，启用停止按钮
        self.run_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status.config(text=f"⚙️ 正在运行: {os.path.basename(file_path)}")
        
        # 在新线程中运行
        thread = threading.Thread(target=self.run_thread, args=(file_path,))
        thread.daemon = True
        thread.start()
        
    def run_thread(self, file_path):
        try:
            script_dir = os.path.dirname(os.path.abspath(file_path))
            
            self.current_process = subprocess.Popen(
                [sys.executable, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=script_dir
            )
            
            for line in iter(self.current_process.stdout.readline, ''):
                if line:
                    self.root.after(0, self.append_output, line)
                    
            return_code = self.current_process.wait()
            
            if return_code == 0:
                self.root.after(0, self.run_success)
            else:
                self.root.after(0, self.run_error, return_code)
                
        except Exception as e:
            self.root.after(0, self.run_exception, str(e))
        finally:
            self.root.after(0, self.enable_buttons)
            
    def append_output(self, text):
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.root.update_idletasks()
        
    def run_success(self):
        self.status.config(text="✅ 运行完成")
        messagebox.showinfo("完成", "✅ 脚本运行完成！")
        
    def run_error(self, code):
        self.status.config(text=f"❌ 运行失败 (退出码: {code})")
        messagebox.showerror("错误", f"脚本运行失败\n退出码: {code}")
        
    def run_exception(self, error):
        self.status.config(text=f"⚠️ 错误: {error}")
        self.append_output(f"\n错误: {error}\n")
        messagebox.showerror("错误", f"运行出错:\n{error}")
        
    def stop_script(self):
        if self.current_process and self.current_process.poll() is None:
            self.append_output("\n⚠️ 正在停止脚本...\n")
            self.current_process.terminate()
            self.status.config(text="🛑 正在停止...")
            
    def enable_buttons(self):
        self.run_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.current_process = None
        
    def clear_output(self):
        self.output.delete(1.0, tk.END)
        
    def on_closing(self):
        if self.current_process and self.current_process.poll() is None:
            if messagebox.askokcancel("确认退出", "脚本正在运行中，确定要退出吗？"):
                self.current_process.terminate()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonScriptRunner(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
PYTHON_SCRIPT

# 运行 Python 脚本
python3 "$TEMP_PYTHON_SCRIPT"

# 保存退出码
EXIT_CODE=$?

# 删除临时文件
rm -f "$TEMP_PYTHON_SCRIPT"

# 如果出错，显示错误信息
if [ $EXIT_CODE -ne 0 ]; then
    echo "启动失败，退出码: $EXIT_CODE"
    read -p "按回车键退出..."
fi

exit $EXIT_CODE