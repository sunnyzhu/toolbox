import sys
import vlc
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                            QSlider, QTextEdit)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class VideoPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频分割工具")
        self.setGeometry(100, 100, 800, 600)

        # 创建VLC实例和播放器
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 创建视频显示区域
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(360)
        self.layout.addWidget(self.video_frame)

        # 创建控制区域
        self.create_controls()
        
        # 创建时间显示
        self.time_label = QLabel("00:00:00 / 00:00:00")
        self.time_label.setFont(QFont("Arial", 10))
        self.layout.addWidget(self.time_label)

        # 创建进度条
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.setRange(0, 1000)  # 初始范围设置为0-1000
        self.layout.addWidget(self.progress_slider)

        # 创建时间点选择按钮
        self.create_time_selection()

        # 创建文本输入框
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(100)
        self.layout.addWidget(self.text_edit)

        # 更新定时器
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_ui)
        
        self.media = None
        self.is_playing = False

        # 添加一个标志来跟踪视频是否已加载
        self.video_loaded = False

        # 初始化音量状态
        self.is_muted = False
        self.player.audio_set_volume(100)  # 设置初始音量为100%

        # 启用拖放
        self.setAcceptDrops(True)
        self.video_frame.setAcceptDrops(True)

        # 设置进度条可以接收焦点
        self.progress_slider.setFocusPolicy(Qt.StrongFocus)
        # 连接键盘事件
        self.progress_slider.keyPressEvent = self.on_slider_key_press

    def create_controls(self):
        control_layout = QHBoxLayout()
        
        # 打开文件按钮
        self.open_button = QPushButton("打开文件")
        self.open_button.clicked.connect(self.open_file)
        
        # 播放/暂停按钮
        self.play_button = QPushButton("播放")
        self.play_button.clicked.connect(self.play_pause)
        
        # 静音按钮
        self.mute_button = QPushButton("有声")
        self.mute_button.setFixedWidth(40)
        self.mute_button.clicked.connect(self.toggle_mute)
        
        control_layout.addWidget(self.open_button)
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.mute_button)
        control_layout.addStretch()  # 添加弹性空间
        
        self.layout.addLayout(control_layout)

    def create_time_selection(self):
        time_layout = QHBoxLayout()
        
        self.start_button = QPushButton("选择开始时间")
        self.end_button = QPushButton("选择结束时间")
        
        self.start_button.clicked.connect(lambda: self.add_time_to_text("开始"))
        self.end_button.clicked.connect(lambda: self.add_time_to_text("结束"))
        
        time_layout.addWidget(self.start_button)
        time_layout.addWidget(self.end_button)
        self.layout.addLayout(time_layout)

    def dragEnterEvent(self, event):
        """处理拖入事件"""
        if event.mimeData().hasUrls():
            # 检查是否是视频文件
            file_path = event.mimeData().urls()[0].toLocalFile()
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv']
            if any(file_path.lower().endswith(ext) for ext in video_extensions):
                event.acceptProposedAction()

    def dropEvent(self, event):
        """处理放下事件"""
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.load_media(file_path)

    def load_media(self, file_path):
        """加载媒体文件"""
        self.media = self.instance.media_new(file_path)
        self.player.set_media(self.media)
        
        # 将视频输出设置到视频框架
        if sys.platform.startswith('linux'): # Linux
            self.player.set_xwindow(self.video_frame.winId())
        elif sys.platform == "win32": # Windows
            self.player.set_hwnd(self.video_frame.winId())
        elif sys.platform == "darwin": # Mac
            self.player.set_nsobject(int(self.video_frame.winId()))

        # 设置音量状态
        if self.is_muted:
            self.player.audio_set_volume(0)
        else:
            self.player.audio_set_volume(100)
        
        # 获取文件名并添加到文本框顶部
        file_name = os.path.basename(file_path)  # 从路径中提取文件名
        current_text = self.text_edit.toPlainText()
        
        # 如果文本框不为空，添加换行
        if current_text:
            new_text = f"{current_text}\n{file_name}"
        else:
            new_text = f"{file_name}"
        
        self.text_edit.setText(new_text)
        
        self.play_pause()
        self.timer.start()
        # 等待媒体加载完成
        self.media.parse()
        self.video_loaded = True
        
        # 获取视频总时长（毫秒）
        duration = self.player.get_length()
        if duration > 0:
            self.progress_slider.setRange(0, duration)        

    def open_file(self):
        """打开文件按钮的处理函数"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, 
            "打开视频文件",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv)"
        )
        if file_name:
            self.load_media(file_name)

    def play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_button.setText("播放")
            self.is_playing = False
        else:
            self.player.play()
            self.play_button.setText("暂停")
            self.is_playing = True

    def update_ui(self):
        """更新UI状态"""
        if not self.video_loaded:
            return

        # 获取当前播放时间（毫秒）
        current_time = self.player.get_time()
        if current_time >= 0:
            # 更新进度条
            self.progress_slider.setValue(current_time)

        # 更新时间标签
        current_time = self.player.get_time() // 1000  # 转换为秒
        total_time = self.player.get_length() // 1000  # 转换为秒
        
        if current_time >= 0 and total_time > 0:
            current_str = f"{current_time//3600:02d}:{(current_time%3600)//60:02d}:{current_time%60:02d}"
            total_str = f"{total_time//3600:02d}:{(total_time%3600)//60:02d}:{total_time%60:02d}"
            self.time_label.setText(f"{current_str} / {total_str}")

    def set_position(self, position):
        """设置播放位置"""
        if self.video_loaded:
            self.player.set_time(position)

    def add_time_to_text(self, type_str):
        """添加时间到文本框"""
        if not self.player.is_playing() and not self.media:
            return
            
        current_time = self.player.get_time() // 1000  # 转换为秒
        time_str = f"{current_time//3600:02d}:{(current_time%3600)//60:02d}:{current_time%60:02d}"
        
        # 移动光标到文本末尾
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.End)
        self.text_edit.setTextCursor(cursor)
        
        current_text = self.text_edit.toPlainText()
        if type_str == "开始":
            if current_text and not current_text.endswith("\n"):
                self.text_edit.append("")
                # 再次移动光标到末尾
                cursor = self.text_edit.textCursor()
                cursor.movePosition(cursor.End)
                self.text_edit.setTextCursor(cursor)
            self.text_edit.insertPlainText(f"{time_str}-")
        else:  # 结束时间
            if not current_text.endswith("-"):
                return
            self.text_edit.insertPlainText(f"{time_str}")
            # 添加新行
            self.text_edit.append("")

    def toggle_mute(self):
        """切换静音状态"""
        if not self.is_muted:
            # 静音
            self.player.audio_set_volume(0)
            self.mute_button.setText("静音")
            self.is_muted = True
        else:
            # 取消静音
            self.player.audio_set_volume(100)
            self.mute_button.setText("有声")
            self.is_muted = False

    def on_slider_key_press(self, event):
        """处理进度条的键盘事件"""
        if not self.video_loaded:
            return
            
        if event.key() == Qt.Key_Space:
            # 空格键控制播放/暂停
            self.play_pause()
        elif event.key() == Qt.Key_Left:
            # 后退5秒
            current_time = self.player.get_time()
            new_time = max(0, current_time - 5000)  # 5000毫秒 = 5秒
            self.player.set_time(new_time)
        elif event.key() == Qt.Key_Right:
            # 前进5秒
            current_time = self.player.get_time()
            new_time = min(self.player.get_length(), current_time + 5000)
            self.player.set_time(new_time)
        else:
            # 对于其他按键，保持默认行为
            super(QSlider, self.progress_slider).keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_()) 