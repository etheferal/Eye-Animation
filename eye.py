import math
import os
import sys
import time
import numpy as np

# Windows terminalinde ANSI renk ve imleç kodlarını aktif etmek için
if os.name == 'nt':
    os.system('')

# Ekranı temizle ve imleci gizle
sys.stdout.write('\033[?25l\033[2J')
sys.stdout.flush()

# ASCII karakter seti (yoğunluğa göre)
CHARS = np.array(
    list(" .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$")
)

# Terminal ızgara boyutları (genişlik x yükseklik)
WIDTH, HEIGHT = 75, 26

# Koordinat ızgarası (-1 ile 1 arasında ölçeklendirilmiş)
y_indices, x_indices = np.indices((HEIGHT, WIDTH))
x = (x_indices - WIDTH / 2) / (WIDTH / 2)
# Karakterlerin dikey/yatay oran farkını düzeltmek için 2 kat ölçek
y = (y_indices - HEIGHT / 2) / (HEIGHT / 2) * 2.0


def render_frame(t):
    # Göz kırpma döngüsü (0.0: tamamen kapalı, 1.0: tamamen açık)
    blink = np.sin(t * 2.5) ** 8
    lid_open = np.clip(1.0 - blink * 1.15, 0.02, 1.0)

    # Göz bebeği hareketi (sağa-sola ve hafif yukarı-aşağı)
    pupil_x = 0.35 * np.sin(t * 1.5)
    pupil_y = 0.15 * np.cos(t * 3.0)

    # Göz kapaklarının eliptik sınırları
    upper_lid = lid_open * np.sqrt(np.clip(1.0 - (x * 0.9) ** 2, 0, None))
    lower_lid = -lid_open * np.sqrt(np.clip(1.0 - (x * 0.9) ** 2, 0, None))

    # Gözün içi (göz kapakları arası bölge)
    eye_mask = (
        (y < upper_lid) & (y > lower_lid) & (x > -1.0) & (x < 1.0)
    ).astype(np.float32)

    # Göz bebeği ve iris mesafesi
    dx = x - pupil_x
    dy = y - pupil_y
    dist_iris = np.sqrt(dx**2 + (dy * 1.1) ** 2)

    # Katmanlar: Göz bebeği (pupil), iris, sklera (göz beyazı), deri (skin)
    pupil_mask = (dist_iris < 0.18) * eye_mask
    iris_mask = ((dist_iris >= 0.18) & (dist_iris < 0.48)) * eye_mask
    sclera_mask = ((dist_iris >= 0.48) & (eye_mask > 0)).astype(np.float32)
    skin_mask = (eye_mask == 0).astype(np.float32)

    # RGB Renk Matrisleri
    r = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    g = np.zeros((HEIGHT, WIDTH), dtype=np.float32)
    b = np.zeros((HEIGHT, WIDTH), dtype=np.float32)

    # 1. Göz Bebeği (Koyu Kırmızı/Siyahımsı tonlar)
    r += pupil_mask * 40
    g += pupil_mask * 10
    b += pupil_mask * 15

    # 2. İris (Turuncu / Ateş Kırmızısı ışıma)
    iris_fade = 1.0 - (dist_iris - 0.18) / 0.30
    r += iris_mask * (210 + 45 * iris_fade)
    g += iris_mask * (80 + 70 * iris_fade)
    b += iris_mask * (30 * iris_fade)

    # 3. Göz Beyazı / Sklera (Kırmızı damarlı açık renk)
    r += sclera_mask * 180
    g += sclera_mask * 160
    b += sclera_mask * 160

    # 4. Deri / Çevre (Karanlık ve kırmızımsı gölgeler)
    lid_dist = np.minimum(np.abs(y - upper_lid), np.abs(y - lower_lid))
    skin_fade = np.clip(np.exp(-lid_dist * 2.5), 0, 1)
    r += skin_mask * (80 * skin_fade + 15)
    g += skin_mask * (30 * skin_fade + 5)
    b += skin_mask * (35 * skin_fade + 10)

    # Parlaklık (Intensity) ve Karakter Seçimi
    intensity = (r * 0.299 + g * 0.587 + b * 0.114) / 255.0
    char_indices = np.clip(
        (intensity * (len(CHARS) - 1)).astype(int), 0, len(CHARS) - 1
    )
    frame_chars = CHARS[char_indices]

    # Tampon (Buffer) oluşturma ve ekrana basma
    output = ["\033[H"]  # İmleci terminalin sol üst köşesine alır
    for i in range(HEIGHT):
        row = []
        for j in range(WIDTH):
            ch = frame_chars[i, j]
            red = int(np.clip(r[i, j], 0, 255))
            green = int(np.clip(g[i, j], 0, 255))
            blue = int(np.clip(b[i, j], 0, 255))
            # TrueColor ANSI kodu: \033[38;2;R;G;Bm
            row.append(f"\033[38;2;{red};{green};{blue}m{ch}")
        output.append("".join(row))

    output.append("\033[0m")
    sys.stdout.write("\n".join(output))
    sys.stdout.flush()


def main():
    try:
        t = 0.0
        while True:
            render_frame(t)
            time.sleep(0.04)  # ~25 FPS
            t += 0.05
    except KeyboardInterrupt:
        # Programdan Ctrl+C ile çıkıldığında imleci geri getir ve sıfırla
        sys.stdout.write("\033[?25h\033[0m\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()