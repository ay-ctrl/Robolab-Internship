import os
import tkinter as tk
from PIL import Image, ImageTk

class AnimeFaceEngine:
    def __init__(self, window, sprite_path, display_w=480, display_h=480):
        self.window = window
        self.window.title("Siber Maskot Yüz Motoru - Animasyon Destekli")
        
        self.display_w = display_w
        self.display_h = display_h
        
        # 1. Büyük Sprite Sheet'i Yüklüyoruz
        self.sprite_path = sprite_path
        self.sprite_sheet = Image.open(self.sprite_path).convert("RGB")
        print(f"Sprite sheet başarıyla yüklendi: {sprite_path}")
        
        # 5 sütun x 4 satır = 20 yüzlük matris
        self.cols = 5  
        self.rows = 4  
        self.cell_w = self.sprite_sheet.width // self.cols  
        self.cell_h = self.sprite_sheet.height // self.rows 
        
        # --- ESKİ SABİT İFADELER ---
        self.expressions = {
            "NEUTRAL": (0, 0),  # 1. sütun, 1. satır (0. İndeks)
            "HAPPY":   (1, 0),  # 2. sütun, 1. satır (1. İndeks)
            "SAD":     (2, 0),  # 3. sütun, 1. satır (2. İndeks)
            "ANGRY":   (3, 0)   # 4. sütun, 1. satır (3. İndeks)
        }
        self.current_expression = "NEUTRAL"
        
        # --- YENİ ANİMASYON SİSTEMİ ---
        self.is_playing_animation = False  # Şu an animasyon oynuyor mu, yoksa sabit resim mi?
        self.smile_frames = [2, 3, 11]     # İstediğin özel dizilim
        self.current_frame_index = 0
        self.animation_speed = 150         # Karelerin geçiş hızı (milisaniye)
        
        # 2. Arayüz Elemanları
        self.canvas = tk.Canvas(window, width=self.display_w, height=self.display_h, bg="black")
        self.canvas.pack(pady=10)
        
        self.info_label = tk.Label(
            window, 
            text="Mod: Sabit Resim (İfade: NEUTRAL)\n(1,2,3,4 Sabit İfadeler | P harfi: Canlı Gülme Animasyonu!)", 
            font=("Arial", 11)
        )
        self.info_label.pack(pady=5)
        
        # ESKİ KISAYOLLAR (Aynen Korundu)
        self.window.bind("1", lambda e: self.set_static_expression("NEUTRAL"))
        self.window.bind("2", lambda e: self.set_static_expression("HAPPY"))
        self.window.bind("3", lambda e: self.set_static_expression("SAD"))
        self.window.bind("4", lambda e: self.set_static_expression("ANGRY"))
        
        # YENİ KISAYOL (P harfi ile animasyon başlatma, 'p' veya 'P' fark etmez)
        self.window.bind("<p>", lambda e: self.start_smile_animation())
        self.window.bind("<P>", lambda e: self.start_smile_animation())
        
        # Ana motor döngüsünü başlat
        self.main_loop()

    def set_static_expression(self, expression_name):
        """Eski sistem: Animasyonu durdurur ve seçilen sabit ifadeye geçer."""
        if expression_name in self.expressions:
            self.is_playing_animation = False  # Animasyon modundan çık
            self.current_expression = expression_name
            self.info_label.config(text=f"Mod: Sabit Resim (İfade: {expression_name})\n(1,2,3,4 Sabit İfadeler | P harfi: Canlı Gülme Animasyonu!)")

    def start_smile_animation(self):
        """Yeni sistem: P tuşuna basınca gülme animasyonunu tetikler."""
        if not self.is_playing_animation:
            self.is_playing_animation = True
            self.current_frame_index = 0
            self.info_label.config(text="Mod: CANLI ANİMASYON (smile)\n(Çıkmak ve sabitlemek için 1, 2, 3, 4 tuşlarına basabilirsin)")

    def index_to_grid(self, face_index):
        """0-19 arasındaki indeks numarasını sütun ve satıra çevirir."""
        col = face_index % self.cols
        row = face_index // self.cols
        return col, row

    def main_loop(self):
        """Hem sabit kareleri çizen hem de animasyonu akıtan ana döngü."""
        
        if self.is_playing_animation:
            # --- ANİMASYON MODU ---
            # Liste içerisinden o anki kare numarasını al (2, 3 veya 12)
            face_index = self.smile_frames[self.current_frame_index]
            col_idx, row_idx = self.index_to_grid(face_index)
            
            # Kareyi ilerlet, sona geldiyse başa sar
            self.current_frame_index += 1
            if self.current_frame_index >= len(self.smile_frames):
                self.current_frame_index = 0
        else:
            # --- ESKİ SABİT MOD ---
            col_idx, row_idx = self.expressions[self.current_expression]
            
        # Kırpma ve Ekrana Basma İşlemleri (Ortak alan)
        left = col_idx * self.cell_w
        top = row_idx * self.cell_h
        right = left + self.cell_w
        bottom = top + self.cell_h
        
        cropped_face = self.sprite_sheet.crop((left, top, right, bottom))
        resized_face = cropped_face.resize((self.display_w, self.display_h))
        
        self.tk_image = ImageTk.PhotoImage(resized_face)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        
        # Döngünün hızı animasyon modundaysa hızlı aksın, sabit modda işlemciyi yormasın diye 150ms idealdir
        self.window.after(self.animation_speed, self.main_loop)

if __name__ == "__main__":
    root = tk.Tk()
    
    # 1. Orijinal resmin adı
    ORIJINAL_RESIM = "spritesheet_face.jpg" 
    # Kırpılmış yeni resmin kaydedileceği geçici isim
    KIRPILMIS_RESIM = "spritesheet_face_temiz.jpg"

    # 2. Resmi aç ve kenarlarından kırp
    img = Image.open(ORIJINAL_RESIM)
    
    # --- AYARLARI BURADAN DEĞİŞTİR ---
    sol_at = 300   # En soldan kaç piksel kesilsin?
    ust_at = 300   # En üstten kaç piksel kesilsin?
    sag_at = 300  # En sağdan kaç piksel kesilsin?
    alt_at = 300   # En alttan kaç piksel kesilsin?
    # ---------------------------------

    # Kırpma kutusunu hesapla (sol, üst, sağ, alt)
    kutu = (sol_at, ust_at, img.width - sag_at, img.height - alt_at)
    temiz_img = img.crop(kutu)
    
    # Kırpılmış yeni temiz resmi diske kaydet
    temiz_img.save(KIRPILMIS_RESIM)
    print(f"Resim kırpıldı! Eski: {img.width}x{img.height} -> Yeni: {temiz_img.width}x{temiz_img.height}")

    # 3. Motoru artık bu kırpılmış temiz resimle başlatıyoruz
    app = AnimeFaceEngine(root, sprite_path=KIRPILMIS_RESIM, display_w=480, display_h=480)
    root.mainloop()