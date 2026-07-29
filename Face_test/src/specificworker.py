#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2026 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QGroupBox, QSlider, QLabel, QCheckBox, QLineEdit, QGridLayout, 
    QFrame
)
from PySide6.QtGui import QFont
from genericworker import *
from rich.console import Console
import os

console = Console(highlight=False)

try:
    import setproctitle
    setproctitle.setproctitle(os.path.basename(os.getcwd()))
except:
    pass


class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]
        
        if startup_check:
            self.startup_check()
        else:
            QTimer.singleShot(150, self.create_test_ui)
            
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def create_test_ui(self):
        """A dashboard to thoroughly test all of the EBO robot's capabilities."""
        self.window = QWidget()
        self.window.setWindowTitle("EBO Robot - Face Control Dashboard ")
        self.window.resize(500, 750)
        
        # === STYLE DEFINITIONS ===
        self.window.setStyleSheet("""
            QWidget {
                background-color: #1e1e24;
                color: #e0e0e6;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox {
                border: 2px solid #3a3a45;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                font-size: 13px;
                color: #00d2ff;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #2e2e3a;
                border: 1px solid #4a4a5a;
                border-radius: 5px;
                padding: 8px;
                min-height: 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3e3e50;
                border-color: #00d2ff;
            }
            QPushButton:pressed {
                background-color: #00d2ff;
                color: #1e1e24;
            }
            QLineEdit {
                background-color: #121216;
                border: 1px solid #4a4a5a;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #4a4a5a;
                height: 8px;
                background: #121216;
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00d2ff;
                border: 1px solid #00d2ff;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)

        main_layout = QVBoxLayout()
        
        # --- TOP INFORMATION PANEL ---
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.StyledPanel)
        header_frame.setStyleSheet("background-color: #2a2a35; border-radius: 6px; padding: 10px;")
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("EBO EMOTIONAL MOTOR SYSTEM")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #00d2ff; letter-spacing: 1px;")
        
        self.status_bar = QLabel("System is ready, waiting for connection...")
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setStyleSheet("color: #a0a0b0; font-size: 11px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(self.status_bar)
        main_layout.addWidget(header_frame)
        
        # --- 1. EMOTION EXPRESSIONS  ---
        emotions_group = QGroupBox("Emotion expressions")
        emotions_layout = QGridLayout()
        
        emotions = [
            ("😊 Joy ", self.emotionalmotor_proxy.expressJoy, "#2ecc71"),
            ("😡 Anger ", self.emotionalmotor_proxy.expressAnger, "#e74c3c"),
            ("😢 Sadness ", self.emotionalmotor_proxy.expressSadness, "#3498db"),
            ("😲 Surprise ", self.emotionalmotor_proxy.expressSurprise, "#f1c40f"),
            ("🤢 Disgust ", self.emotionalmotor_proxy.expressDisgust, "#9b59b6"),
            ("😨 Fear ", self.emotionalmotor_proxy.expressFear, "#e67e22")
        ]
        
        for index, (name, func, color) in enumerate(emotions):
            btn = QPushButton(name)
            btn.setStyleSheet(f"QPushButton:hover {{ border-color: {color}; color: {color}; }}")
            btn.clicked.connect(lambda checked=False, f=func: self.safe_proxy_call(f))
            row = index // 2
            col = index % 2
            emotions_layout.addWidget(btn, row, col)
            
        emotions_group.setLayout(emotions_layout)
        main_layout.addWidget(emotions_group)
        
        # --- 2. SPANISH SPEAKING PANEL ---
        talk_group = QGroupBox("Talking Spanish")
        talk_layout = QVBoxLayout()
        
        talk_layout.addWidget(QLabel("Text to send:"))
        self.txt_speech = QLineEdit()
        self.txt_speech.setPlaceholderText("Example: ¡Hola amigo! ¿Cómo estás?")
        self.txt_speech.setText("¿Hola amigo, como ests?")
        talk_layout.addWidget(self.txt_speech)
        
        btn_talk_row = QHBoxLayout()
        btn_send_talk = QPushButton("🗣 Send text and talk")
        btn_send_talk.setStyleSheet("background-color: #0f3d3d; border-color: #00d2ff;")
        btn_send_talk.clicked.connect(self.send_speech_command)
        
        btn_stop_talk = QPushButton("🤫 Close mouth (Rest)")
        btn_stop_talk.setStyleSheet("background-color: #4a2323; border-color: #ff4a4a;")
        btn_stop_talk.clicked.connect(lambda: self.safe_proxy_call(self.emotionalmotor_proxy.talking, False, ""))
        
        btn_talk_row.addWidget(btn_send_talk)
        btn_talk_row.addWidget(btn_stop_talk)
        talk_layout.addLayout(btn_talk_row)
        
        talk_group.setLayout(talk_layout)
        main_layout.addWidget(talk_group)
        
        # --- 3. STATES AND MODES ---
        states_group = QGroupBox("Concurrent States")
        states_layout = QHBoxLayout()
        
        # Listening mode
        self.chk_listening = QCheckBox("🎧 Listening")
        self.chk_listening.stateChanged.connect(
            lambda state: self.safe_proxy_call(self.emotionalmotor_proxy.listening, state == 2)
        )
        
        # Sensing somebody / Sleeping mode
        self.chk_anybody = QCheckBox("👤 There is somebody (awake)")
        self.chk_anybody.setChecked(True) # EBO is awake as default
        self.chk_anybody.stateChanged.connect(
            lambda state: self.safe_proxy_call(self.emotionalmotor_proxy.isanybodythere, state == 2)
        )
        
        states_layout.addWidget(self.chk_listening)
        states_layout.addWidget(self.chk_anybody)
        states_group.setLayout(states_layout)
        main_layout.addWidget(states_group)
        
        # --- 4. PUPIL CONTROLLER ---
        pupil_group = QGroupBox("Pupil Position Control Panel")
        pupil_main_layout = QHBoxLayout()
        
        # Sol Taraf: Kaydırıcılar (Slider'lar)
        sliders_layout = QVBoxLayout()
        
        self.lbl_x = QLabel("X Axes (Left/Right): 0.00")
        sliders_layout.addWidget(self.lbl_x)
        self.slider_x = QSlider(Qt.Horizontal)
        self.slider_x.setMinimum(-100)
        self.slider_x.setMaximum(100)
        self.slider_x.setValue(0)
        self.slider_x.valueChanged.connect(self.on_pupil_changed)
        sliders_layout.addWidget(self.slider_x)
        
        self.lbl_y = QLabel("Y Axes (Up/Down): 0.00")
        sliders_layout.addWidget(self.lbl_y)
        self.slider_y = QSlider(Qt.Horizontal)
        self.slider_y.setMinimum(-100)
        self.slider_y.setMaximum(100)
        self.slider_y.setValue(0)
        self.slider_y.valueChanged.connect(self.on_pupil_changed)
        sliders_layout.addWidget(self.slider_y)
        
        btn_center = QPushButton("🎯 Center the eyes")
        btn_center.clicked.connect(self.center_pupils)
        sliders_layout.addWidget(btn_center)
        
        pupil_main_layout.addLayout(sliders_layout, stretch=3)
        
        # Right Side: Fast Look-up Grid (8 Directions Joystick Mechanism)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(4)
        
        directions = [
            ("↖", -0.8, 0.8, 0, 0),   ("⬆", 0.0, 0.8, 0, 1),   ("↗", 0.8, 0.8, 0, 2),
            ("⬅", -0.8, 0.0, 1, 0),   ("🎯", 0.0, 0.0, 1, 1),  ("➡", 0.8, 0.0, 1, 2),
            ("↙", -0.8, -0.8, 2, 0),  ("⬇", 0.0, -0.8, 2, 1),  ("↘", 0.8, -0.8, 2, 2)
        ]
        
        for icon, px, py, row, col in directions:
            btn_dir = QPushButton(icon)
            btn_dir.setFixedSize(35, 35)
            btn_dir.setStyleSheet("font-size: 14px; font-weight: bold; background-color: #252530;")
            btn_dir.clicked.connect(lambda checked=False, x=px, y=py: self.send_pupil_coordinates(x, y))
            grid_layout.addWidget(btn_dir, row, col)
            
        pupil_main_layout.addLayout(grid_layout, stretch=2)
        
        pupil_group.setLayout(pupil_main_layout)
        main_layout.addWidget(pupil_group)
        
        self.window.setLayout(main_layout)
        self.window.show()

    def send_speech_command(self):
        text = self.txt_speech.text()
        self.safe_proxy_call(self.emotionalmotor_proxy.talking, True, text)

    def on_pupil_changed(self):
        """It sends normalized float values ​​as the slider values ​​change."""
        x_val = self.slider_x.value() / 100.0
        y_val = self.slider_y.value() / 100.0
        self.lbl_x.setText(f"X Axes (Right/Left): {x_val:.2f}")
        self.lbl_y.setText(f"Y Axes (Up/Down): {y_val:.2f}")
        self.safe_proxy_call(self.emotionalmotor_proxy.pupposition, x_val, y_val)

    def send_pupil_coordinates(self, x, y):
        """When the quick direction buttons are pressed, it sends the slider values ​​in a synchronized manner."""
        self.slider_x.blockSignals(True)
        self.slider_y.blockSignals(True)
        self.slider_x.setValue(int(x * 100))
        self.slider_y.setValue(int(y * 100))
        self.slider_x.blockSignals(False)
        self.slider_y.blockSignals(False)
        
        self.lbl_x.setText(f"X Ekseni (Right/Left): {x:.2f}")
        self.lbl_y.setText(f"Y Ekseni (Up/Down): {y:.2f}")
        
        self.safe_proxy_call(self.emotionalmotor_proxy.pupposition, x, y)

    def center_pupils(self):
        """Resets the sliders and centers the eyes."""
        self.slider_x.setValue(0)
        self.slider_y.setValue(0)

    def safe_proxy_call(self, func, *args):
        """It prevents the application from freezing during connection errors and displays the status on the screen."""
        try:
            func(*args)
            msg = f"[SUCCESS] {func.__name__} called ({args})"
            console.print(f"[green]{msg}[/green]")
            self.status_bar.setText(f"Successful: {func.__name__}")
            self.status_bar.setStyleSheet("color: #2ecc71; font-size: 11px;")
        except Exception as e:
            msg = f"[ERROR] {func.__name__} could not called: {e}"
            console.print(f"[red]{msg}[/red]")
            self.status_bar.setText(f"Error: Is emotional motor component working?")
            self.status_bar.setStyleSheet("color: #e74c3c; font-size: 11px;")

    @Slot()
    def compute(self):
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    def __del__(self):
        """Destructor"""




    ######################
    # From the RoboCompEmotionalMotor you can call this methods:
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressAnger()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressDisgust()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressFear()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressJoy()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressSadness()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressSurprise()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.isanybodythere(bool isAny)
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.listening(bool setListening)
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.pupposition(float x, float y)
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.talking(bool setTalk, str texto)


