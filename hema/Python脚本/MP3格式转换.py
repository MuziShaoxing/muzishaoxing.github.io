#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音视频文件转MP3脚本
支持常见和冷门格式，包括CAF、APE、WV、DTS、AC3、EAC3、AIFF、AU、VOC等
"""

import os
import sys
from pathlib import Path
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# 支持的媒体格式（扩展名列表）
SUPPORTED_FORMATS = {
    # 视频格式
    '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp', '.3g2',
    '.webm', '.mpg', '.mpeg', '.mpe', '.m2v', '.m2ts', '.mts', '.ts', '.vob',
    '.ogv', '.divx', '.xvid', '.asf', '.rm', '.rmvb', '.f4v', '.swf',
    
    # 常见音频格式
    '.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus', '.ape',
    '.aiff', '.aif', '.aifc', '.au', '.snd', '.voc', '.vox', '.raw', '.pcm',
    
    # 无损/高保真格式
    '.wv', '.wavpack', '.dsf', '.dff', '.sacd', '.iso', '.mlp', '.tta',
    '.tak', '.ofr', '.ofs', '.spx', '.acm',
    
    # 环绕声/多声道格式
    '.ac3', '.eac3', '.dts', '.dtshd', '.truehd', '.thd', '.mlp',
    
    # Apple/Core Audio 格式
    '.caf',   # Core Audio Format (苹果专业音频格式)
    '.mp4', '.m4a', '.m4b', '.m4p', '.m4r',  # MPEG-4 家族
    '.qcp',   # Qualcomm PureVoice
    
    # 游戏/专业音频格式
    '.adx',   # CRI ADX (游戏音频)
    '.afc',   # AFC Audio
    '.aix',   # AIX Audio
    '.brstm', # BRSTM (任天堂Wii)
    '.bwav',  # Broadcast WAV
    '.caf',   # Core Audio
    '.dsp',   # DSP (PlayStation)
    '.fsb',   # FSB (FMOD)
    '.g722',  # G.722
    '.g726',  # G.726
    '.hca',   # HCA (CRI)
    '.idsp',  # IDSP (Nintendo 3DS)
    '.it',    # Impulse Tracker
    '.mod',   # MOD Music
    '.mpc',   # Musepack
    '.msv',   # Memory Stick Voice
    '.nsp',   # NSP
    '.ogg', '.ogm', '.ogx', '.oga', '.spx', '.opus',
    '.psf',   # Portable Sound Format
    '.psf2',  # PSF2
    '.rco',   # RCO
    '.rsf',   # RSF
    '.s3m',   # ScreamTracker 3
    '.spc',   # SPC700
    '.tak',   # TAK Lossless
    '.tta',   # True Audio
    '.twowav', # TwinVQ
    '.vab',   # VAB (PlayStation)
    '.vag',   # VAG (PlayStation)
    '.vgm',   # Video Game Music
    '.vgz',   # Compressed VGM
    '.vox',   # Dialogic VOX
    '.w64',   # Wave64
    '.wav', '.wave',
    '.wma',   # Windows Media Audio
    '.wv',    # WavPack
    '.xa',    # XA (PlayStation)
    '.xm',    # Extended Module
    '.ymf',   # YMF
}

class ConverterGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("音视频转MP3工具 - 支持200+格式")
        self.root.geometry("700x600")
        
        # 检查ffmpeg
        if not self.check_ffmpeg():
            self.root.withdraw()
            messagebox.showerror("错误", "未找到ffmpeg！\n\n请先安装ffmpeg。\nmacOS: brew install ffmpeg\nWindows: 从官网下载")
            self.install_ffmpeg_guide()
            return
        
        self.setup_ui()
        
    def check_ffmpeg(self):
        """检查ffmpeg是否已安装"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            return False
    
    def install_ffmpeg_guide(self):
        """提供ffmpeg安装指南"""
        print("\n❌ 错误：未找到 ffmpeg！")
        print("\n请先安装 ffmpeg：")
        print("\n● macOS (推荐):")
        print("  1. 安装 Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("  2. 运行: brew install ffmpeg")
        print("\n● Windows:")
        print("  1. 下载 ffmpeg: https://ffmpeg.org/download.html")
        print("  2. 解压到 C:\\ffmpeg")
        print("  3. 添加 C:\\ffmpeg\\bin 到系统环境变量 Path")
        print("  4. 重启命令行")
        print("\n● Linux (Ubuntu/Debian):")
        print("  sudo apt-get install ffmpeg")
        
        input("\n按Enter键退出...")
        sys.exit(1)
        
    def setup_ui(self):
        # 文件列表框架
        frame_files = ttk.LabelFrame(self.root, text="文件列表（支持200+格式）", padding=10)
        frame_files.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 列表框和滚动条
        scrollbar_y = ttk.Scrollbar(frame_files)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x = ttk.Scrollbar(frame_files, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        
        self.file_listbox = tk.Listbox(frame_files, yscrollcommand=scrollbar_y.set,
                                       xscrollcommand=scrollbar_x.set, font=("Courier", 9))
        self.file_listbox.pack(fill="both", expand=True)
        scrollbar_y.config(command=self.file_listbox.yview)
        scrollbar_x.config(command=self.file_listbox.xview)
        
        # 按钮框架
        frame_buttons = ttk.Frame(self.root)
        frame_buttons.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(frame_buttons, text="添加文件", command=self.add_files).pack(side="left", padx=2)
        ttk.Button(frame_buttons, text="添加文件夹", command=self.add_folder).pack(side="left", padx=2)
        ttk.Button(frame_buttons, text="清空列表", command=self.clear_list).pack(side="left", padx=2)
        ttk.Button(frame_buttons, text="移除选中", command=self.remove_selected).pack(side="left", padx=2)
        
        # 显示支持的格式
        ttk.Button(frame_buttons, text="显示支持的格式", command=self.show_supported_formats).pack(side="left", padx=2)
        
        # 设置框架
        frame_settings = ttk.LabelFrame(self.root, text="转换设置", padding=10)
        frame_settings.pack(fill="x", padx=10, pady=5)
        
        # 第一行设置
        ttk.Label(frame_settings, text="比特率:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.bitrate_var = tk.StringVar(value="192k")
        bitrate_combo = ttk.Combobox(frame_settings, textvariable=self.bitrate_var, 
                                     values=["96k", "128k", "160k", "192k", "256k", "320k"], 
                                     width=10)
        bitrate_combo.grid(row=0, column=1, sticky="w", padx=5)
        
        ttk.Label(frame_settings, text="采样率:").grid(row=0, column=2, sticky="w", padx=5)
        self.samplerate_var = tk.StringVar(value="44100")
        samplerate_combo = ttk.Combobox(frame_settings, textvariable=self.samplerate_var,
                                        values=["22050", "44100", "48000", "96000"], 
                                        width=10)
        samplerate_combo.grid(row=0, column=3, sticky="w", padx=5)
        
        ttk.Label(frame_settings, text="声道:").grid(row=0, column=4, sticky="w", padx=5)
        self.channels_var = tk.StringVar(value="立体声")
        channels_combo = ttk.Combobox(frame_settings, textvariable=self.channels_var,
                                      values=["立体声", "单声道", "保持原声道"], 
                                      width=12)
        channels_combo.grid(row=0, column=5, sticky="w", padx=5)
        
        # 第二行设置
        ttk.Label(frame_settings, text="输出目录:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.output_dir_var = tk.StringVar(value="源文件目录")
        output_dir_combo = ttk.Combobox(frame_settings, textvariable=self.output_dir_var,
                                        values=["源文件目录", "自定义目录"], 
                                        width=12)
        output_dir_combo.grid(row=1, column=1, sticky="w", padx=5)
        output_dir_combo.bind('<<ComboboxSelected>>', self.on_output_dir_change)
        
        self.custom_dir_btn = ttk.Button(frame_settings, text="选择目录", 
                                         command=self.select_output_dir, state="disabled")
        self.custom_dir_btn.grid(row=1, column=2, sticky="w", padx=5)
        self.custom_dir_path = tk.StringVar()
        
        # 高级选项
        ttk.Label(frame_settings, text="音量增益:").grid(row=1, column=3, sticky="w", padx=5)
        self.volume_gain = tk.StringVar(value="0")
        gain_spinbox = ttk.Spinbox(frame_settings, from_=-30, to=30, textvariable=self.volume_gain, width=8)
        gain_spinbox.grid(row=1, column=4, sticky="w", padx=5)
        ttk.Label(frame_settings, text="dB").grid(row=1, column=5, sticky="w", padx=0)
        
        # 第三行选项
        self.normalize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_settings, text="音量归一化", variable=self.normalize_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        
        self.trim_silence_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_settings, text="自动修剪静音", variable=self.trim_silence_var).grid(row=2, column=2, columnspan=2, sticky="w", padx=5)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        # 状态标签
        self.status_label = ttk.Label(self.root, text="就绪", relief="sunken")
        self.status_label.pack(fill="x", padx=10, pady=5)
        
        # 转换按钮
        self.convert_btn = ttk.Button(self.root, text="开始转换", command=self.start_conversion)
        self.convert_btn.pack(pady=10)
        
    def show_supported_formats(self):
        """显示支持的格式列表"""
        format_window = tk.Toplevel(self.root)
        format_window.title("支持的格式列表")
        format_window.geometry("500x400")
        
        # 创建文本框和滚动条
        text_frame = ttk.Frame(format_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, wrap="word")
        text_widget.pack(fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # 分组显示格式
        formats_list = sorted(list(SUPPORTED_FORMATS))
        
        categories = {
            "视频格式": ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.3gp', '.m4v', '.mpg', '.mpeg', '.ogv'],
            "常见音频": ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.m4a', '.wma', '.opus', '.ape', '.aiff'],
            "无损格式": ['.wv', '.dsf', '.dff', '.tta', '.tak', '.wavpack'],
            "环绕声": ['.ac3', '.eac3', '.dts', '.truehd', '.mlp'],
            "Apple格式": ['.caf', '.mp4', '.m4a', '.m4b', '.m4p', '.m4r', '.aiff', '.aif', '.aifc'],
            "专业/游戏": ['.adx', '.brstm', '.fsb', '.hca', '.it', '.mod', '.mpc', '.psf', '.psf2', '.s3m', '.spc', '.vgm', '.xm'],
            "其他格式": []
        }
        
        # 分类
        for fmt in formats_list:
            categorized = False
            for cat, formats in categories.items():
                if fmt in formats:
                    categorized = True
                    break
            if not categorized:
                categories["其他格式"].append(fmt)
        
        # 显示分类
        for cat, formats in categories.items():
            if formats:
                text_widget.insert(tk.END, f"\n{cat} ({len(formats)}个):\n", "header")
                text_widget.insert(tk.END, "  " + "  ".join(formats[:10]) + "\n")
                if len(formats) > 10:
                    text_widget.insert(tk.END, f"  以及 {len(formats)-10} 个其他格式...\n")
        
        text_widget.tag_config("header", font=("Arial", 10, "bold"), foreground="blue")
        text_widget.config(state="disabled")
        
    def on_output_dir_change(self, event):
        """输出目录选择变化"""
        if self.output_dir_var.get() == "自定义目录":
            self.custom_dir_btn.config(state="normal")
        else:
            self.custom_dir_btn.config(state="disabled")
            
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.custom_dir_path.set(directory)
            self.status_label.config(text=f"输出目录: {directory}")
            
    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfilenames(
            title="选择音视频文件（支持200+格式）",
            filetypes=[
                ("所有支持的格式", "*.*"),
                ("视频文件", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.webm *.3gp"),
                ("音频文件", "*.mp3 *.wav *.flac *.ogg *.aac *.m4a *.wma *.opus *.ape *.aiff"),
                ("Apple格式", "*.caf *.m4a *.m4b *.aiff"),
                ("环绕声格式", "*.ac3 *.eac3 *.dts"),
                ("无损格式", "*.wv *.dsf *.dff *.tta *.tak"),
                ("所有文件", "*.*")
            ]
        )
        added = 0
        for file in files:
            if file not in self.file_listbox.get(0, tk.END):
                self.file_listbox.insert(tk.END, file)
                added += 1
        self.status_label.config(text=f"已添加 {added} 个文件")
        
    def add_folder(self):
        """添加文件夹中的所有媒体文件"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            folder_path = Path(folder)
            files = [str(f) for f in folder_path.rglob("*")  # 递归查找
                    if f.suffix.lower() in SUPPORTED_FORMATS and f.is_file()]
            
            added = 0
            for file in files:
                if file not in self.file_listbox.get(0, tk.END):
                    self.file_listbox.insert(tk.END, file)
                    added += 1
            self.status_label.config(text=f"从文件夹添加了 {added} 个文件（包括子文件夹）")
            
    def clear_list(self):
        """清空列表"""
        self.file_listbox.delete(0, tk.END)
        self.status_label.config(text="列表已清空")
        
    def remove_selected(self):
        """移除选中的文件"""
        selected = self.file_listbox.curselection()
        for index in reversed(selected):
            self.file_listbox.delete(index)
        self.status_label.config(text=f"已移除 {len(selected)} 个文件")
        
    def convert_file(self, input_file, output_file=None):
        """转换单个文件"""
        input_path = Path(input_file)
        
        if output_file is None:
            if self.output_dir_var.get() == "自定义目录" and self.custom_dir_path.get():
                output_path = Path(self.custom_dir_path.get()) / input_path.with_suffix('.mp3').name
            else:
                output_path = input_path.with_suffix('.mp3')
        else:
            output_path = Path(output_file)
            if output_path.suffix.lower() != '.mp3':
                output_path = output_path.with_suffix('.mp3')
        
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建ffmpeg命令
        cmd = ['ffmpeg', '-i', str(input_path)]
        
        # 音频参数
        cmd.extend(['-vn'])  # 不处理视频
        
        # 声道设置
        channels = self.channels_var.get()
        if channels == "单声道":
            cmd.extend(['-ac', '1'])
        elif channels == "立体声":
            cmd.extend(['-ac', '2'])
        # "保持原声道" 不添加参数
        
        # 比特率和采样率
        cmd.extend(['-acodec', 'libmp3lame'])
        cmd.extend(['-b:a', self.bitrate_var.get()])
        cmd.extend(['-ar', self.samplerate_var.get()])
        
        # 音量增益
        gain = float(self.volume_gain.get())
        if gain != 0:
            cmd.extend(['-af', f'volume={gain}dB'])
        
        # 音量归一化
        if self.normalize_var.get():
            cmd.extend(['-af', 'loudnorm=I=-16:LRA=11:TP=-1.5'])
        
        # 修剪静音
        if self.trim_silence_var.get():
            cmd.extend(['-af', 'silenceremove=1:0:-50dB'])
        
        # 覆盖输出文件
        cmd.extend(['-y', str(output_path)])
        
        try:
            # 执行转换
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                size_mb = output_path.stat().st_size / (1024 * 1024)
                return True, f"✅ {input_path.name} -> {size_mb:.2f} MB"
            else:
                error_msg = result.stderr[-200:] if result.stderr else "未知错误"
                return False, f"❌ {input_path.name}: {error_msg}"
                
        except Exception as e:
            return False, f"❌ {input_path.name}: {str(e)}"
            
    def update_progress(self, current, total, status_text):
        """更新进度"""
        progress = (current / total) * 100
        self.progress_var.set(progress)
        self.status_label.config(text=status_text)
        self.root.update()
        
    def start_conversion(self):
        """开始转换"""
        files = list(self.file_listbox.get(0, tk.END))
        if not files:
            messagebox.showwarning("警告", "请先添加要转换的文件！")
            return
        
        # 禁用转换按钮
        self.convert_btn.config(state="disabled")
        self.progress_var.set(0)
        
        success_count = 0
        results = []
        
        for i, file in enumerate(files, 1):
            self.update_progress(i, len(files), f"正在转换 ({i}/{len(files)}): {Path(file).name}")
            
            success, message = self.convert_file(file)
            if success:
                success_count += 1
            results.append(message)
        
        # 显示结果
        result_window = tk.Toplevel(self.root)
        result_window.title("转换结果")
        result_window.geometry("500x400")
        
        text_widget = tk.Text(result_window, wrap="word")
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        for result in results:
            text_widget.insert(tk.END, result + "\n")
        
        text_widget.config(state="disabled")
        
        # 完成
        self.progress_var.set(100)
        self.status_label.config(text=f"转换完成！成功: {success_count}/{len(files)}")
        messagebox.showinfo("完成", f"转换完成！\n成功: {success_count}/{len(files)}\n详细结果请查看弹出窗口")
        
        # 恢复转换按钮
        self.convert_btn.config(state="normal")

def main():
    # 如果有命令行参数，使用命令行模式
    if len(sys.argv) > 1 and sys.argv[1] not in ['-h', '--help']:
        import argparse
        
        parser = argparse.ArgumentParser(description='音视频文件转MP3工具')
        parser.add_argument('input', help='输入文件路径')
        parser.add_argument('-o', '--output', help='输出文件路径（可选）')
        parser.add_argument('-b', '--bitrate', default='192k', help='比特率 (默认: 192k)')
        parser.add_argument('-r', '--sample-rate', type=int, default=44100, help='采样率 (默认: 44100)')
        parser.add_argument('-c', '--channels', choices=['mono', 'stereo'], default='stereo', 
                          help='声道模式 (默认: stereo)')
        parser.add_argument('-g', '--gain', type=float, default=0, help='音量增益 dB')
        parser.add_argument('-n', '--normalize', action='store_true', help='音量归一化')
        
        args = parser.parse_args()
        
        # 检查ffmpeg
        converter = ConverterGUI()
        if not converter.check_ffmpeg():
            converter.install_ffmpeg_guide()
        
        # 设置参数
        converter.bitrate_var.set(args.bitrate)
        converter.samplerate_var.set(str(args.sample_rate))
        converter.channels_var.set("立体声" if args.channels == 'stereo' else "单声道")
        converter.volume_gain.set(str(args.gain))
        converter.normalize_var.set(args.normalize)
        
        # 转换
        success, message = converter.convert_file(args.input, args.output)
        print(message)
        sys.exit(0 if success else 1)
    else:
        # GUI模式
        try:
            app = ConverterGUI()
            app.root.mainloop()
        except Exception as e:
            print(f"启动GUI失败: {e}")
            print("尝试使用命令行模式...")
            print("使用方法: python script.py <输入文件> [选项]")
            sys.exit(1)

if __name__ == '__main__':
    main()