import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import binascii
import os
import struct
from file_signatures import SORTED_SIGNATURES

class SingleFilePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()



    def on_click(self, event):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_path_var.set(file_path)
            self.analyze_file(file_path)

    def create_widgets(self):
        # 创建标题
        self.header_label = ttk.Label(
            self, 
            text="单次文件处理", 
            style='Header.TLabel'
        )
        self.header_label.pack(pady=(0, 15))

        # 创建拖放区域
        self.drop_frame = ttk.Frame(
            self, 
            style='DropFrame.TFrame',
            padding=30
        )
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        self.drop_frame.bind('<Button-1>', self.on_click)

        # 文件路径显示
        self.file_path_var = tk.StringVar(value='点击选择文件进行分析')
        self.drop_label = ttk.Label(
            self.drop_frame, 
            textvariable=self.file_path_var,
            style='DropText.TLabel',
            wraplength=400
        )
        self.drop_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 创建结果区域
        self.result_frame = ttk.LabelFrame(self, text='识别结果', padding=10, style='Result.TLabelframe')
        self.result_frame.pack(fill=tk.BOTH, expand=True)

        # 添加表格框架
        self.table_frame = ttk.Frame(self.result_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 文件信息显示
        self.info_frame = ttk.Frame(self.result_frame)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.info_text = tk.Text(self.info_frame, height=3, wrap=tk.WORD, state=tk.DISABLED, font=('微软雅黑', 10), bg='white', bd=1, relief=tk.SOLID)
        self.info_text.pack(fill=tk.X)

        columns = ('name', 'description', 'extension', 'confidence')
        self.result_tree = ttk.Treeview(self.table_frame, columns=columns, show='headings')
        self.result_tree.column('name', anchor=tk.W, width=100)
        self.result_tree.column('description', anchor=tk.W, width=200)
        self.result_tree.column('extension', anchor=tk.W, width=80)
        self.result_tree.column('confidence', anchor=tk.E, width=80)

        self.result_tree.heading('name', text='格式名称')
        self.result_tree.heading('description', text='描述')
        self.result_tree.heading('extension', text='扩展名')
        self.result_tree.heading('confidence', text='匹配度')

        self.result_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # 滚动条
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient='vertical', command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def read_file_header(self, file_path, size=1024):
        try:
            with open(file_path, 'rb') as f:
                return f.read(size)
        except Exception as e:
            self.append_info(f"读取文件错误: {str(e)}")
            return None

    def check_signatures(self, header):
        from file_signatures import FILE_SIGNATURES, SORTED_SIGNATURES
        results = []
        header_hex = binascii.hexlify(header).decode('ascii').upper()
        header_str = header.decode('utf-8', errors='replace')

        for signature_info in SORTED_SIGNATURES:
            try:
                # 确保签名信息包含5个元素
                name, description, ext, signature_type, signature = signature_info
                confidence = 0

                if signature_type == 'hex':
                    signature_bytes = binascii.unhexlify(signature.replace(' ', ''))
                    sig_len = len(signature_bytes)
                    if len(header) >= sig_len and header[:sig_len] == signature_bytes:
                        confidence = 100
                elif signature_type == 'string':
                    sig_len = len(signature)
                    if len(header_str) >= sig_len and header_str[:sig_len] == signature:
                        confidence = 100

                if confidence > 0:
                    results.append((name, description, ext, confidence))
            except ValueError:
                # 跳过格式不正确的签名条目
                continue

        # 更宽松的文本文件检测：允许常见控制字符并检查大部分可打印
        header_str = header.decode('utf-8', errors='replace')
        printable_chars = sum(1 for c in header_str[:256] if c in '\t\n\r ' or c.isprintable())
        if printable_chars / 256 > 0.6:
            results.append(('文本文件', '纯文本文件', '.txt', 75))

        return sorted(results, key=lambda x: x[3], reverse=True)

    def append_info(self, text):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, text + '\n')
        self.info_text.config(state=tk.DISABLED)
        self.info_text.see(tk.END)

    def clear_results(self):
        self.file_path_var.set('点击选择文件进行分析')
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def analyze_file(self, file_path):
        self.clear_results()
        self.append_info(f"分析文件: {file_path}")
        
        try:
            file_size = os.path.getsize(file_path)
            self.append_info(f"文件大小: {self.format_size(file_size)}")
            
            header = self.read_file_header(file_path)
            if not header:
                return
                
            results = self.check_signatures(header)
            if results:
                self.append_info(f"找到 {len(results)} 种可能的文件格式:")
                for name, description, ext, confidence in results:
                    self.result_tree.insert('', tk.END, values=(name, description, ext, f"{confidence}%"))
            else:
                self.append_info("未找到匹配的文件格式")
        except Exception as e:
            self.append_info(f"分析错误: {str(e)}")




class BatchFilePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()

    def create_widgets(self):
        # 创建标题
        self.header_label = ttk.Label(
            self, 
            text="批量文件处理", 
            style='Header.TLabel'
        )
        self.header_label.pack(pady=(0, 20))

        # 文件夹选择
        self.folder_frame = ttk.Frame(self)
        self.folder_frame.pack(fill=tk.X, pady=(0, 15))

        self.folder_path = tk.StringVar()
        self.folder_entry = ttk.Entry(self.folder_frame, textvariable=self.folder_path, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 10))

        self.browse_btn = ttk.Button(
            self.folder_frame, 
            text="浏览文件夹", 
            command=self.browse_folder
        )
        self.browse_btn.pack(side=tk.LEFT)

        # 扫描按钮
        self.scan_btn = ttk.Button(
            self, 
            text="扫描文件", 
            command=self.scan_files
        )
        self.scan_btn.pack(pady=(0, 15))

        # 文件列表表格
        # 结果显示框架
        self.result_frame = ttk.LabelFrame(self, text="分析结果")
        self.result_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.table_frame = ttk.Frame(self.result_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True)

        # 添加信息显示区域
        self.info_frame = ttk.Frame(self.result_frame)
        self.info_frame.pack(fill=tk.X, padx=5, pady=5)
        self.info_text = tk.Text(self.info_frame, height=3, wrap=tk.WORD, state=tk.DISABLED, font=('微软雅黑', 10), bg='white', bd=1, relief=tk.SOLID)
        self.info_text.pack(fill=tk.X)

        columns = ("filename", "current_ext", "suggested_ext")
        self.table_frame = ttk.Frame(self.result_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = (0, 1, 2, 3)
        self.file_tree = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        self.file_tree.column(0, anchor=tk.W, width=200)
        self.file_tree.column(1, anchor=tk.W, width=100)
        self.file_tree.column(2, anchor=tk.W, width=120)
        self.file_tree.column(3, anchor=tk.CENTER, width=60)

        self.file_tree.heading(0, text="文件名")
        self.file_tree.heading(1, text="当前扩展名")
        self.file_tree.heading(2, text="建议扩展名")
        self.file_tree.heading(3, text="确认")

        # 添加滚动条
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=self.scrollbar.set)

        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定Treeview点击事件用于切换复选框状态
        self.file_tree.bind('<ButtonRelease-1>', self.toggle_checkbox)

        # 批量操作按钮
        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill=tk.X, pady=15)

        self.select_all_btn = ttk.Button(
            self.button_frame, 
            text="全选", 
            command=self.select_all
        )
        self.select_all_btn.pack(side=tk.LEFT, padx=5)

        self.deselect_all_btn = ttk.Button(
            self.button_frame, 
            text="取消全选", 
            command=self.deselect_all
        )
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)

        self.rename_btn = ttk.Button(
            self.button_frame, 
            text="批量重命名", 
            command=self.batch_rename
        )
        self.rename_btn.pack(side=tk.RIGHT, padx=5)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)

    def check_file_type(self, file_path):
        # 读取文件头
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
        except Exception:
            return None

        # 检查文件签名
        from file_signatures import SORTED_SIGNATURES
        header_hex = binascii.hexlify(header).decode('ascii').upper()
        header_str = header.decode('utf-8', errors='replace')

        for signature_info in SORTED_SIGNATURES:
            try:
                name, description, ext, signature_type, signature = signature_info
                if signature_type == 'hex':
                    signature_bytes = binascii.unhexlify(signature.replace(' ', ''))
                    sig_len = len(signature_bytes)
                    if len(header) >= sig_len and header[:sig_len] == signature_bytes:
                        # 特殊处理APNG
                        if name == 'APNG':
                            return '.png'
                        return ext
                elif signature_type == 'string':
                    sig_len = len(signature)
                    if len(header_str) >= sig_len and header_str[:sig_len] == signature:
                        return ext
            except ValueError:
                continue

        # 检查是否为文本文件
        if all(c in '\t\n\r ' or c.isprintable() for c in header_str[:256]):
            return '.txt'
        return None

    def scan_files(self):
        # 清空现有内容
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        folder_path = self.folder_path.get()
        if not folder_path or not os.path.isdir(folder_path):
            messagebox.showerror("错误", "请选择有效的文件夹")
            return

        # 扫描文件夹中的顶层文件（不包含子目录）
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                current_ext = os.path.splitext(filename)[1].lower()
                
                # 获取建议的扩展名
                suggested_ext = self.check_file_type(file_path)
                if not suggested_ext:
                    suggested_ext = current_ext
                
                # APNG特殊处理
                if suggested_ext == '.apng':
                    suggested_ext = '.png'
                
                # 添加到表格
                # 添加第四列默认值'✗'（未确认）
                self.file_tree.insert('', tk.END, values=(filename, current_ext, suggested_ext, '☐'))

    def get_suggested_extension(self, file_path):
        header = self.read_file_header(file_path)
        if not header:
            return ''

        from file_signatures import SORTED_SIGNATURES
        header_hex = binascii.hexlify(header).decode('ascii').upper()
        header_str = header.decode('utf-8', errors='replace')

        for signature_info in SORTED_SIGNATURES:
            name, description, ext, signature_type, signature = signature_info
            if signature_type == 'hex':
                signature_bytes = binascii.unhexlify(signature.replace(' ', ''))
                sig_len = len(signature_bytes)
                if len(header) >= sig_len and header[:sig_len] == signature_bytes:
                    return ext.split(',')[0] if ',' in ext else ext
            elif signature_type == 'string':
                sig_len = len(signature)
                if len(header_str) >= sig_len and header_str[:sig_len] == signature:
                    return ext.split(',')[0] if ',' in ext else ext

        return ''

    def read_file_header(self, file_path, num_bytes=32):
        try:
            with open(file_path, 'rb') as f:
                return f.read(num_bytes)
        except:
            return None

    def check_signatures(self, header):
        matches = []
        header_length = len(header)

        for name, sig_info in SORTED_SIGNATURES:
            signature = sig_info['signature']
            sig_length = len(signature)

            if sig_length == 0:
                continue
            elif header_length >= sig_length and header.startswith(signature):
                matches.append({
                    'name': name,
                    'extension': sig_info['extension'],
                    'confidence': 1.0
                })
            elif header_length >= sig_length // 2:
                half_length = sig_length // 2
                if header.startswith(signature[:half_length]):
                    matches.append({
                        'name': name,
                        'extension': sig_info['extension'],
                        'confidence': 0.5
                    })

        return sorted(matches, key=lambda x: x['confidence'], reverse=True)

    def toggle_checkbox(self, event):
        # 获取点击位置的列
        region = self.file_tree.identify_region(event.x, event.y)
        if region == 'cell':
            column = int(self.file_tree.identify_column(event.x).replace('#', '')) - 1
            # 只处理第4列(索引3)的点击
            if column == 3:
                item = self.file_tree.identify_row(event.y)
                if item:
                    values = list(self.file_tree.item(item, "values"))
                    # 切换复选框状态
                    values[3] = "☑" if values[3] == "☐" else "☐"
                    self.file_tree.item(item, values=values)

    def select_all(self):
        for item in self.file_tree.get_children():
            values = list(self.file_tree.item(item, "values"))
            values[3] = "☑"
            self.file_tree.item(item, values=values)

    def deselect_all(self):
        for item in self.file_tree.get_children():
            values = list(self.file_tree.item(item, "values"))
            values[3] = "☐"
            self.file_tree.item(item, values=values)

    def append_info(self, message):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

    def batch_rename(self):
        folder_path = self.folder_path.get()
        if not folder_path:
            messagebox.showerror("错误", "请先选择文件夹并扫描文件")
            return

        renamed_count = 0
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            # 修复批量处理时的值解包错误
            if len(values) != 4:
                self.append_info(f"文件数据格式错误: {values}")
                continue
            filename, current_ext, suggested_ext, confirm = values

            # 允许强制修改扩展名，移除对suggested_ext的限制
            if confirm == "☑": # 使用新的复选框选中状态值
                # 获取新文件名
                name_without_ext = os.path.splitext(filename)[0]
                new_filename = f"{name_without_ext}{suggested_ext}"
                old_path = os.path.join(folder_path, filename)
                new_path = os.path.join(folder_path, new_filename)

                try:
                    os.rename(old_path, new_path)
                    renamed_count += 1
                except Exception as e:
                    messagebox.showerror("错误", f"重命名 {filename} 失败: {str(e)}")

        messagebox.showinfo("完成", f"批量重命名完成，共处理 {renamed_count} 个文件")
        self.scan_files()  # 重新扫描以更新列表

    def append_info(self, message):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, message + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

class FileIdentifierApp:

    def __init__(self, root):
        self.root = root
        self.root.title("文件格式识别工具")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        self.root.configure(bg='#e6f2ff')

        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('winnative')  # 使用Windows原生主题确保兼容性
        self.style.configure('TLabel', font=('微软雅黑', 10), background='#e6f2ff', foreground='#333333')
        self.style.configure('Header.TLabel', font=('微软雅黑', 12, 'bold'), background='#e6f2ff', foreground='#0066cc')
        self.style.configure('TFrame', background='#e6f2ff')
        self.style.configure('DropFrame.TFrame', background='#fff0f5', borderwidth=2, relief=tk.SOLID)
        self.style.configure('Result.TLabelframe', background='#cce5ff')
        self.style.configure('Result.TLabelframe.Label', foreground='#0066cc', font=('微软雅黑', 10, 'bold'))
        self.style.configure('Treeview', background='white', fieldbackground='white', foreground='#333333')
        self.style.configure('Treeview.Heading', background='#0066cc', foreground='white')
        self.style.configure('Sidebar.TButton', font=('微软雅黑', 10), width=15)

        # 复制TLabelframe的默认布局到自定义样式
        self.style.layout('Result.TLabelframe', self.style.layout('TLabelframe'))

        # 创建主容器
        self.container = ttk.Frame(root)
        self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建侧边栏和主内容区的分隔
        self.paned_window = ttk.PanedWindow(self.container, orient=tk.HORIZONTAL)
        self.style = ttk.Style()
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # 创建侧边栏
        self.sidebar_frame = ttk.Frame(self.paned_window, width=150, padding=10)
        self.paned_window.add(self.sidebar_frame, weight=0)

        # 创建侧边栏标题
        self.sidebar_label = ttk.Label(
            self.sidebar_frame, 
            text="功能菜单", 
            style='Header.TLabel'
        )
        self.sidebar_label.pack(pady=(0, 20))

        # 创建侧边栏按钮
        # 侧边栏按钮样式
        self.style.configure('Sidebar.TButton', font=('微软雅黑', 10), width=15, padding=(5, 10))
        self.style.configure('Sidebar.Hover.TButton', background='#e0e0e0')
        self.style.configure('Sidebar.Selected.TButton', background='#0078d7', foreground='white')
        self.style.map('Sidebar.TButton',
            background=[('selected', '#0078d7'), ('active', '#e0e0e0')],
            foreground=[('selected', 'white'), ('active', '#000000')],
            relief=[('selected', 'flat'), ('!selected', 'ridge')]
        )

        self.single_page_btn = ttk.Button(
            self.sidebar_frame, 
            text="单次文件处理", 
            command=lambda: self.show_page("single"),
            style='Sidebar.TButton'
        )
        self.single_page_btn.pack(fill=tk.X, pady=1, ipady=5)
        self.single_page_btn.bind('<Enter>', lambda e: self.on_hover(e, self.single_page_btn))
        self.single_page_btn.bind('<Leave>', lambda e: self.off_hover(e, self.single_page_btn))

        self.batch_page_btn = ttk.Button(
            self.sidebar_frame, 
            text="批量文件处理", 
            command=lambda: self.show_page("batch"),
            style='Sidebar.TButton'
        )
        self.batch_page_btn.pack(fill=tk.X, pady=1, ipady=5)
        self.batch_page_btn.bind('<Enter>', lambda e: self.on_hover(e, self.batch_page_btn))
        self.batch_page_btn.bind('<Leave>', lambda e: self.off_hover(e, self.batch_page_btn))

        # 创建内容区域
        self.content_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.content_frame, weight=1)

        # 创建页面实例
        self.pages = {
            "single": SingleFilePage(parent=self.content_frame, controller=self),
            "batch": BatchFilePage(parent=self.content_frame, controller=self)
        }

        # 默认显示单次处理页面
        self.show_page("single")

    def on_hover(self, event, button):
        if not button.instate(['selected']):
            button.config(style='Sidebar.Hover.TButton')

    def off_hover(self, event, button):
        if not button.instate(['selected']):
            button.config(style='Sidebar.TButton')

    def show_page(self, page_name):
        # 重置所有按钮状态
        self.single_page_btn.state(['!selected'])
        self.batch_page_btn.state(['!selected'])
        
        # 隐藏所有页面
        for frame in self.pages.values():
            frame.pack_forget()
            
        # 显示选中页面并激活对应按钮
        frame = self.pages[page_name]
        frame.pack(fill=tk.BOTH, expand=True)
        
        if page_name == "single":
            self.single_page_btn.state(['selected'])
            self.style.configure('Sidebar.TButton', padding=(10, 5))
        else:
            self.batch_page_btn.state(['selected'])
            self.style.configure('Sidebar.TButton', padding=(5, 5))
        
        # 添加页面切换动画
        pass
        # 隐藏所有页面
        for page in self.pages.values():
            page.pack_forget()
        # 显示选中的页面
        self.pages[page_name].pack(fill=tk.BOTH, expand=True)

        

    def on_click(self, event):
        # 处理点击选择文件
        file_path = filedialog.askopenfilename(title="选择文件")
        if file_path:
            self.analyze_file(file_path)

    def read_file_header(self, file_path, num_bytes=32):
        # 读取文件头字节
        try:
            with open(file_path, 'rb') as f:
                return f.read(num_bytes)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件: {str(e)}")
            return None

    def append_info(self, text):
        # 添加文本到信息区域
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, text + "\n")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

    def clear_results(self):
        # 清空结果区域
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

    def analyze_file(self, file_path):
        # 分析文件并显示结果
        self.clear_results()
        self.append_info(f"正在分析文件: {os.path.basename(file_path)}")
        self.append_info(f"文件路径: {file_path}")

        # 获取文件大小
        file_size = os.path.getsize(file_path)
        self.append_info(f"文件大小: {self.format_size(file_size)}")

        # 读取文件头
        header = self.read_file_header(file_path)
        if not header:
            return

        # 检查文件签名
        matches = self.check_signatures(header)

        if matches:
            # 显示最高概率的文件格式
            top_match = matches[0]
            top_confidence = top_match['confidence'] * 100
            self.append_info(f"\n最可能的文件格式: {top_match['name']} (匹配度: {top_confidence:.2f}%)")
            
            # 表格显示所有结果
            self.append_info("所有识别结果:")
            for match in matches:
                confidence = match['confidence'] * 100
                self.result_tree.insert("", tk.END, values=(
                    match['name'],
                    match['description'],
                    match['extension'],
                    f"{confidence:.2f}%"
                ))
        else:
            self.append_info("\n未识别到已知文件格式。")
            self.append_info("可能是未知格式或加密文件。")

    def check_signatures(self, header):
        # 检查文件头与签名数据库
        matches = []
        header_length = len(header)

        for name, sig_info in SORTED_SIGNATURES:
            signature = sig_info['signature']
            sig_length = len(signature)

            if sig_length == 0:
                # 处理没有签名的文件类型（如文本文件）
                # 简单检测是否为纯文本
                try:
                    header.decode('utf-8')
                    matches.append({
                        'name': name,
                        'description': sig_info['description'],
                        'extension': sig_info['extension'],
                        'confidence': 0.5  # 文本文件置信度较低
                    })
                except UnicodeDecodeError:
                    continue
            elif header_length >= sig_length and header.startswith(signature):
                # 完全匹配
                matches.append({
                    'name': name,
                    'description': sig_info['description'],
                    'extension': sig_info['extension'],
                    'confidence': 1.0
                })
            elif header_length >= sig_length // 2:
                # 部分匹配
                half_length = sig_length // 2
                if header.startswith(signature[:half_length]):
                    matches.append({
                        'name': name,
                        'description': sig_info['description'],
                        'extension': sig_info['extension'],
                        'confidence': 0.5
                    })

        # 按置信度排序
        return sorted(matches, key=lambda x: x['confidence'], reverse=True)

    def format_size(self, size_bytes):
        # 格式化文件大小
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

if __name__ == "__main__":
    root = tk.Tk()
    app = FileIdentifierApp(root)
    root.mainloop()