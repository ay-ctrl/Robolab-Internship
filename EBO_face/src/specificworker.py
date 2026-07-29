#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2026 by RoboComp
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

# To add more flexible movements to different components of face, you can make a different layer for each component (eyes, mouth, eyebrows etc).

import os
import sys
import threading
import time
import math
import pygame
import random
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from rich.console import Console
from genericworker import *

console = Console(highlight=False)

try:
    import setproctitle
    setproctitle.setproctitle(os.path.basename(os.getcwd()))
except ImportError:
    pass

# === SCREEN RESOLUTION & PYGAME SETUP ===
pygame.init()
screen_info = pygame.display.Info()
res_x = screen_info.current_w / 2
res_y = screen_info.current_h / 2

screen = pygame.display.set_mode((res_x, res_y))
pygame.display.set_caption("EBO Robot Display")

# Frame rate limiting via PyGame clock
clock = pygame.time.Clock()

# === ANIMATION CONFIGURATION ===
BASE_DIR = "/home/robolab/robocomp-giraff/components/EBO_face/Animations/"
EMOTION_MAP = {
    "Neutral":    {"dir": "neutralAnimeFrames", "prefix": "neutral"},
    "Joy":        {"dir": "smileAnimeFrames", "prefix": "smiling"},
    "Anger":      {"dir": "angerAnimeFrames", "prefix": "angry"},
    "Fear":       {"dir": "fearAnimeFrames",  "prefix": "scared"},
    "Sad":        {"dir": "sadAnimeFrames",   "prefix": "sad"},
    "Surprised":  {"dir": "surpriseAnimeFrames", "prefix": "surprised"},
    "Disgusted":  {"dir": "disgustAnimeFrames", "prefix": "disgusted"},
    
    "Listening":  {"dir": "listeningAnimeFrames", "prefix": "listening"},
    
    "Sleep":      {"dir": "sleepAnimeFrames", "prefix": "sleep"},
    "Sleeping":   {"dir": "sleepingAnimeFrames", "prefix": "sleeping"},
    "Awakening":  {"dir": "awakeningAnimeFrames", "prefix": "awakening"},
    
    "Talk_Rest":        {"dir": "speakingAnimeFrames", "file": "rest.png"},
    "Talk_AEO":         {"dir": "speakingAnimeFrames", "file": "aeo.png"},
    "Talk_IUY":         {"dir": "speakingAnimeFrames", "file": "iuy.png"},
    "Talk_BMP":         {"dir": "speakingAnimeFrames", "file": "bmp.png"},
    "Talk_Consonants":  {"dir": "speakingAnimeFrames", "file": "cons.png"},
}

# === VISUAL CACHING DICTIONARY ===
IMAGE_CACHE = {}

def get_cached_image(path, target_w, target_h):
    """Loads and caches images into RAM to eliminate disk I/O overhead and micro-stuttering."""
    cache_key = (path, target_w, target_h)
    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]
    
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            scaled_img = pygame.transform.scale(img, (target_w, target_h))
            IMAGE_CACHE[cache_key] = scaled_img
            return scaled_img
        except pygame.error as e:
            console.print(f"[bold red]Failed to load image: {path} - Error: {e}[/bold red]")
    else:
        console.print(f"[bold red]Error: Animation source not found -> {path}[/bold red]")
    return None

# Shared Data Structure
shared_data = {
    'image': None,            
    'face_tracking_bg': None, 
    'listening_frame': None, 
    'target_pupil_x': 0.0,
    'target_pupil_y': 0.0,
    'current_pupil_x': 0.0,
    'current_pupil_y': 0.0,
    'pupil_alpha': 255,        
    'lock': threading.Lock()
}

FACE_BG_PATH = f"{BASE_DIR}/eyeAnimeFrames/face_background.png" 
loaded_face_bg = get_cached_image(FACE_BG_PATH, res_x, res_y)
if loaded_face_bg:
    console.print("[bold green]EBO: face_background.png successfully loaded![/bold green]")

PUPIL_IMAGE_PATH = f"{BASE_DIR}/eyeAnimeFrames/pupils.png"
loaded_pupil_img = get_cached_image(PUPIL_IMAGE_PATH, res_x, res_y)
if loaded_pupil_img:
    console.print("[bold green]EBO: Dynamic pupils image successfully loaded![/bold green]")

# === HELPER FUNCTIONS ===
def update_shared_image(path, target_w, target_h):
    """Retrieves an image from cache and safely assigns it to the shared memory structure."""
    scaled_img = get_cached_image(path, target_w, target_h)
    if scaled_img is not None:
        with shared_data['lock']:
            shared_data['image'] = scaled_img
            shared_data['face_tracking_bg'] = None
        return True
    return False

def load_neutral_face():
    neutral_path = f"{BASE_DIR}/eboface.png"
    update_shared_image(neutral_path, res_x, res_y)

# === DYNAMIC RANDOM BLINKING THREAD ===
class BlinkThread(threading.Thread):
    def __init__(self, base_dir, worker_instance, total_frames=11):
        super().__init__()
        self.base_dir = base_dir
        self.worker = worker_instance
        self.total_frames = total_frames
        self.stopped = False
        self.daemon = True

    def run(self):
        cfg = EMOTION_MAP["Neutral"]
        while not self.stopped:
            sleep_duration = random.uniform(3.0, 6.5)
            
            steps = int(sleep_duration / 0.1)
            for _ in range(steps):
                if self.stopped:
                    return
                time.sleep(0.1)

            can_blink = (self.worker.current_emotion in ["Neutral", "Pupil_Movement"]) and \
                        not self.worker.is_sleeping and \
                        not self.worker.is_talking

            if can_blink and not self.stopped:
                with shared_data['lock']:
                    shared_data['pupil_alpha'] = 0

                for i in range(self.total_frames):
                    if self.stopped or self.worker.current_emotion not in ["Neutral", "Pupil_Movement"]:
                        break
                    frame_path = f"{self.base_dir}/{cfg['dir']}/{cfg['prefix']}.{i:04d}.png"
                    update_shared_image(frame_path, res_x, res_y)
                    time.sleep(0.03)

                if self.worker.current_emotion == "Pupil_Movement" and loaded_face_bg is not None:
                    with shared_data['lock']:
                        shared_data['image'] = None 
                        shared_data['face_tracking_bg'] = loaded_face_bg 
                else:
                    load_neutral_face()

                with shared_data['lock']:
                    shared_data['pupil_alpha'] = 255

# === SPEECH SYNCHRONIZATION (VISEME TIMING) ===
def get_viseme_data_for_char(char):
    """Returns the Viseme key and display duration based on character type."""
    char = char.lower()
    if char in ['a', 'e', 'o', 'á', 'é', 'ó']:
        return "Talk_AEO", 0.10   
    elif char in ['i', 'u', 'y', 'í', 'ú']:
        return "Talk_IUY", 0.08
    elif char in ['b', 'm', 'p']:
        return "Talk_BMP", 0.05   
    elif char in ['c', 'd', 'g', 'l', 'n', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z', 'ñ']:
        return "Talk_Consonants", 0.045
    return "Talk_Rest", 0.035    

# === TALKING WORKER THREAD ===
class TalkingAnimationThread(threading.Thread):
    def __init__(self, text, base_dir, worker):
        super().__init__()
        self.text = text
        self.base_dir = base_dir
        self.worker = worker
        self.stopped = False

    def run(self):
        console.print(f"[bold magenta]EBO speaks Spanish: {self.text}[/bold magenta]")
        
        for char in self.text:
            if self.stopped: 
                break
            
            viseme, hold_duration = get_viseme_data_for_char(char)
            cfg = EMOTION_MAP[viseme]
            frame_path = f"{self.base_dir}/{cfg['dir']}/{cfg['file']}"
            
            update_shared_image(frame_path, res_x, res_y)
            time.sleep(hold_duration)

        self.worker.is_talking = False
        self.worker.current_emotion = "Neutral" 
        
        load_neutral_face()
        self.worker._start_blinking_if_needed()
        
        console.print("[bold green]EBO: Talking finished, face reset to Neutral.[/bold green]")

# === EMOTION ANIMATION WORKER THREAD ===
class EmotionAnimationThread(threading.Thread):
    def __init__(self, target_emotion, current_emotion, worker_instance, max_frames=16):
        super().__init__()
        self.target_emotion = target_emotion
        self.source_emotion = current_emotion
        self.worker = worker_instance
        self.max_frames = max_frames
        self.stopped = False

    def run(self):
        active_emotions = ["Joy", "Anger", "Disgusted", "Sad", "Fear", "Surprised"]
        if self.source_emotion and self.source_emotion in active_emotions:
            console.print(f"[bold yellow]EBO: Rolling back {self.source_emotion} back to neutral position...[/bold yellow]")
            src_cfg = EMOTION_MAP.get(self.source_emotion, EMOTION_MAP["Neutral"])
            
            for i in range(self.max_frames - 2, -1, -1):
                if self.stopped: 
                    return
                frame_path = f"{BASE_DIR}/{src_cfg['dir']}/{src_cfg['prefix']}.{i:04d}.png"
                update_shared_image(frame_path, res_x, res_y)
                time.sleep(0.041)
                
            time.sleep(0.1)

        console.print(f"[bold cyan]EBO: Playing {self.target_emotion} transition forward...[/bold cyan]")
        tgt_cfg = EMOTION_MAP.get(self.target_emotion, EMOTION_MAP["Neutral"])
        
        for i in range(self.max_frames):
            if self.stopped: 
                return
            frame_path = f"{BASE_DIR}/{tgt_cfg['dir']}/{tgt_cfg['prefix']}.{i:04d}.png"
            update_shared_image(frame_path, res_x, res_y)
            time.sleep(0.041)
            
        console.print(f"[bold green]EBO: {self.target_emotion} expression successfully rendered.[/bold green]")

# === LISTENING ANIMATION WORKER THREAD ===
class ListeningAnimationThread(threading.Thread):
    def __init__(self, base_dir, max_frames=16):
        super().__init__()
        self.base_dir = base_dir
        self.max_frames = max_frames
        self.stopped = False

    def run(self):
        console.print("[bold blue]EBO: Listening animation loop started...[/bold blue]")
        cfg = EMOTION_MAP["Listening"]
        
        while not self.stopped:
            for i in range(self.max_frames):
                if self.stopped:
                    break
                frame_path = f"{self.base_dir}/{cfg['dir']}/{cfg['prefix']}.{i:04d}.png"
                scaled_img = get_cached_image(frame_path, res_x, res_y)
                
                if scaled_img is not None:
                    with shared_data['lock']:
                        shared_data['listening_frame'] = scaled_img
                
                time.sleep(0.08)
        
        # Thread durduğunda dinleme katmanını temizle
        with shared_data['lock']:
            shared_data['listening_frame'] = None

# === SLEEP AND AWAKE WORKER THREAD ===
class SleepAnimationThread(threading.Thread):
    def __init__(self, base_dir, go_to_sleep=True, max_frames=16):
        super().__init__()
        self.base_dir = base_dir
        self.go_to_sleep = go_to_sleep
        self.max_frames = max_frames
        self.stopped = False

    def run(self):
        if self.go_to_sleep:
            console.print("[bold purple]EBO: Starting transition to deep sleep...[/bold purple]")
            cfg_sleep = EMOTION_MAP["Sleep"]
            for i in range(self.max_frames):
                if self.stopped: 
                    return
                frame_path = f"{self.base_dir}/{cfg_sleep['dir']}/{cfg_sleep['prefix']}.{i:04d}.png"
                update_shared_image(frame_path, res_x, res_y)
                time.sleep(0.05) 

            console.print("[bold purple]EBO: Deep sleep mode active...[/bold purple]")
            cfg_sleeping = EMOTION_MAP["Sleeping"]
            while not self.stopped:
                for i in range(self.max_frames):
                    if self.stopped: 
                        break
                    frame_path = f"{self.base_dir}/{cfg_sleeping['dir']}/{cfg_sleeping['prefix']}.{i:04d}.png"
                    update_shared_image(frame_path, res_x, res_y)
                    time.sleep(0.06) 
        else:
            console.print("[bold orange1]EBO: Initiating awakening sequence...[/bold orange1]")
            cfg_awake = EMOTION_MAP["Awakening"]
            for i in range(self.max_frames):
                if self.stopped: 
                    return
                frame_path = f"{self.base_dir}/{cfg_awake['dir']}/{cfg_awake['prefix']}.{i:04d}.png"
                update_shared_image(frame_path, res_x, res_y)
                time.sleep(0.05)
            
            load_neutral_face()
            console.print("[bold green]EBO: Woke up successfully. Face reset to neutral.[/bold green]")

# === SPECIFIC WORKER CLASS ===
class SpecificWorker(GenericWorker):
    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]
        
        self.current_emotion = "Neutral" 
        self.anim_thread = None
        self.talk_thread = None
        self.listening_thread = None
        self.sleep_thread = None 
        
        self.is_talking = False
        self.is_listening = False
        self.is_sleeping = False 

        self.blink_thread = None
        self._start_blinking_if_needed()
        
        load_neutral_face()
        
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

    def _start_blinking_if_needed(self):
        if (self.current_emotion in ["Neutral", "Pupil_Movement"]) and not self.is_sleeping and not self.is_talking:
            if self.blink_thread is None or not self.blink_thread.is_alive():
                self.blink_thread = BlinkThread(BASE_DIR, self, total_frames=3)
                self.blink_thread.start()

    def _stop_blinking(self):
        if self.blink_thread and self.blink_thread.is_alive():
            self.blink_thread.stopped = True 

    def _transition_to_emotion(self, next_emotion):
        if self.is_sleeping:
            console.print("[bold red]EBO: Robot is sleeping! Emotion transition ignored.[/bold red]")
            return

        if self.is_talking:
            console.print(f"[bold yellow]EBO: Cannot change emotion to {next_emotion} while speaking.[/bold yellow]")
            return

        if self.current_emotion == next_emotion:
            console.print(f"[bold yellow]EBO: Already displaying {next_emotion}. Request skipped.[/bold yellow]")
            return

        if self.anim_thread and self.anim_thread.is_alive():
            self.anim_thread.stopped = True
            self.anim_thread.join(timeout=0.1) 

        if self.current_emotion == "Pupil_Movement":
            console.print("[bold cyan]EBO: Re-centering pupils smoothly before emotion transition...[/bold cyan]")
            
            with shared_data['lock']:
                shared_data['target_pupil_x'] = 0.0
                shared_data['target_pupil_y'] = 0.0

            time.sleep(0.2)

            with shared_data['lock']:
                shared_data['current_pupil_x'] = 0.0
                shared_data['current_pupil_y'] = 0.0
                shared_data['pupil_alpha'] = 255
                shared_data['face_tracking_bg'] = None

        old_emotion = self.current_emotion
        self.current_emotion = next_emotion
        
        self.anim_thread = EmotionAnimationThread(
            target_emotion=next_emotion, 
            current_emotion=old_emotion, 
            worker_instance=self, 
            max_frames=16
        )
        self.anim_thread.start()

    @QtCore.Slot()
    def compute(self):
        try:
            # FPS Limiting
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()

            LERP_FACTOR = 0.2  

            with shared_data['lock']:
                normal_img = shared_data['image']
                tracking_bg = shared_data['face_tracking_bg']
                listening_overlay = shared_data['listening_frame']
                
                target_x = shared_data['target_pupil_x']
                target_y = shared_data['target_pupil_y']
                curr_x = shared_data['current_pupil_x']
                curr_y = shared_data['current_pupil_y']
                pupil_alpha = shared_data['pupil_alpha']

                curr_x += (target_x - curr_x) * LERP_FACTOR
                curr_y += (target_y - curr_y) * LERP_FACTOR

                shared_data['current_pupil_x'] = curr_x
                shared_data['current_pupil_y'] = curr_y

            screen.fill((0, 0, 0))
            
            if self.current_emotion == "Pupil_Movement" and tracking_bg is not None:
                bg_rect = tracking_bg.get_rect(center=(res_x // 2, res_y // 2))
                screen.blit(tracking_bg, bg_rect)
                
                if loaded_pupil_img is not None and pupil_alpha > 0:
                    temp_pupil = loaded_pupil_img.copy()
                    temp_pupil.set_alpha(pupil_alpha)
                    pupil_rect = temp_pupil.get_rect(
                        center=(res_x // 2 + int(curr_x), res_y // 2 + int(curr_y))
                    )
                    screen.blit(temp_pupil, pupil_rect)

            elif normal_img is not None:
                img_rect = normal_img.get_rect(center=(res_x // 2, res_y // 2))
                screen.blit(normal_img, img_rect)

            if self.is_listening and listening_overlay is not None:
                overlay_rect = listening_overlay.get_rect(center=(res_x // 2, res_y // 2))
                screen.blit(listening_overlay, overlay_rect)

            pygame.display.flip()

        except Exception:
            sys.exit()
        return True

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # === ROBOCOMP COMPONENT INTERFACE METHODS ===
    def EmotionalMotor_expressJoy(self):
        console.print("[bold green]EBO: Received expressJoy signal.[/bold green]")
        self._transition_to_emotion("Joy")
        return True

    def EmotionalMotor_expressAnger(self):
        console.print("[bold red]EBO: Received expressAnger signal.[/bold red]")
        self._transition_to_emotion("Anger")
        return True

    def EmotionalMotor_expressFear(self):
        console.print("[bold red]EBO: Received expressFear signal.[/bold red]")
        self._transition_to_emotion("Fear")
        return True

    def EmotionalMotor_expressDisgust(self): 
        console.print("[bold green]EBO: Received expressDisgust signal.[/bold green]")
        self._transition_to_emotion("Disgusted")
        return True

    def EmotionalMotor_expressSadness(self): 
        console.print("[bold green]EBO: Received expressSadness signal.[/bold green]")
        self._transition_to_emotion("Sad")
        return True

    def EmotionalMotor_expressSurprise(self): 
        console.print("[bold green]EBO: Received expressSurprise signal.[/bold green]")
        self._transition_to_emotion("Surprised")
        return True

    def EmotionalMotor_talking(self, t, texto): 
        console.print(f"\n[bold orange3][INTERFACE] EmotionalMotor_talking triggered! -> State(t): {t}, Text: '{texto}'[/bold orange3]")
        
        if self.is_sleeping:
            console.print("[bold red]EBO: Speech request rejected because EBO is asleep.[/bold red]")
            return True

        if not t or not texto or texto.strip() == "":
            console.print("[bold yellow][DEBUG] Signal set to False or empty text. Stopping active speech thread...[/bold yellow]")
            self.is_talking = False
            self.current_emotion = "Neutral"
            if self.talk_thread and self.talk_thread.is_alive():
                self.talk_thread.stopped = True
            return True

        if self.is_listening:
            self.EmotionalMotor_listening(False)

        if self.current_emotion == "Pupil_Movement":
            console.print("[bold cyan]EBO: Re-centering pupils smoothly before starting to talk...[/bold cyan]")
            
            with shared_data['lock']:
                shared_data['target_pupil_x'] = 0.0
                shared_data['target_pupil_y'] = 0.0

            time.sleep(0.18)

            with shared_data['lock']:
                shared_data['current_pupil_x'] = 0.0
                shared_data['current_pupil_y'] = 0.0
                shared_data['pupil_alpha'] = 255
                shared_data['face_tracking_bg'] = None

        self.is_talking = True 

        if self.anim_thread and self.anim_thread.is_alive():
            self.anim_thread.stopped = True

        if self.talk_thread and self.talk_thread.is_alive():
            self.talk_thread.stopped = True
            self.talk_thread.join(timeout=0.05)
            
        self.talk_thread = TalkingAnimationThread(texto, BASE_DIR, self)
        self.talk_thread.start()
        return True
    def EmotionalMotor_listening(self, setListening):
        console.print(f"\n[bold sky_blue3][INTERFACE] EmotionalMotor_listening triggered! -> {setListening}[/bold sky_blue3]")
        
        if self.is_sleeping and setListening:
            console.print("[bold red]EBO: Cannot trigger listening mode while robot is asleep.[/bold red]")
            return True

        if self.is_listening == setListening:
            return True

        self.is_listening = setListening

        if setListening:
            self.listening_thread = ListeningAnimationThread(BASE_DIR, max_frames=16)
            self.listening_thread.start()
            self._start_blinking_if_needed() 
        else:
            if self.listening_thread and self.listening_thread.is_alive():
                self.listening_thread.stopped = True
                self.listening_thread.join(timeout=0.1)
            
            console.print("[bold green]EBO: Listening mode deactivated.[/bold green]")

        return True

    def EmotionalMotor_isanybodythere(self, isAny):
        console.print(f"\n[bold yellow_on_blue][INTERFACE] EmotionalMotor_isanybodythere triggered! -> isAny: {isAny}[/bold yellow_on_blue]")
        
        target_sleep_state = not isAny
        if self.is_sleeping == target_sleep_state:
            return True

        self.is_sleeping = target_sleep_state

        if self.anim_thread and self.anim_thread.is_alive():
            self.anim_thread.stopped = True
        if self.talk_thread and self.talk_thread.is_alive():
            self.is_talking = False
            self.talk_thread.stopped = True
        if self.listening_thread and self.listening_thread.is_alive():
            self.is_listening = False
            self.listening_thread.stopped = True

        if self.sleep_thread and self.sleep_thread.is_alive():
            self.sleep_thread.stopped = True
            self.sleep_thread.join(timeout=0.1)

        if not isAny:
            self.current_emotion = "Sleeping"
            self.sleep_thread = SleepAnimationThread(BASE_DIR, go_to_sleep=True, max_frames=16)
            self.sleep_thread.start()
        else:
            self.current_emotion = "Neutral"
            self.sleep_thread = SleepAnimationThread(BASE_DIR, go_to_sleep=False, max_frames=16)
            self.sleep_thread.start()

        return True

    def EmotionalMotor_pupposition(self, x, y):
        console.print(f"\n[bold green_on_black][INTERFACE] EmotionalMotor_pupposition triggered! -> x: {x}, y: {y}[/bold green_on_black]")
        
        if self.is_sleeping:
            console.print("[bold red]EBO: Eyes movement locked because the robot is sleeping.[/bold red]")
            return True

        if self.is_talking or (self.anim_thread and self.anim_thread.is_alive()):
            console.print("[bold yellow]EBO: Eyes movement ignored during active speaking or transition.[/bold yellow]")
            return True

        if loaded_face_bg is None or loaded_pupil_img is None:
            console.print("[bold red]EBO: Error! face_background.png or pupils.png missing.[/bold red]")
            return True

        fx = float(x)
        fy = float(y)

        magnitude = math.sqrt(fx * fx + fy * fy)

        if magnitude > 1.0 and magnitude > 0:
            fx /= magnitude
            fy /= magnitude

        RADIUS_X = int(res_x * 0.04)
        RADIUS_Y = int(res_y * 0.04)

        offset_x = float(fx * RADIUS_X)
        offset_y = float(fy * RADIUS_Y)

        with shared_data['lock']:
            shared_data['image'] = None 
            shared_data['face_tracking_bg'] = loaded_face_bg 
            shared_data['target_pupil_x'] = offset_x
            shared_data['target_pupil_y'] = offset_y

        self.current_emotion = "Pupil_Movement"
        self._start_blinking_if_needed()

        console.print(f"[bold cyan]EBO: Base face loaded & pupil target updated -> X: {offset_x}px, Y: {offset_y}px[/bold cyan]")
        return True