import os
import time
import requests
import spotipy
import subprocess
import glob
from spotipy.oauth2 import SpotifyOAuth
from requests.exceptions import RequestException
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# -------------------------------
# CONFIG
# -------------------------------

CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

CHECK_INTERVAL = 5  # saniye

# -------------------------------
# Spotify Auth
# -------------------------------

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-read-currently-playing",
        cache_path=".spotify_cache"
    )
)

LAST_IMAGE_URL = None


# -------------------------------
# Wallpaper Setter
# -------------------------------

def set_wallpaper(image_path):
    abs_path = os.path.abspath(image_path)

    result = subprocess.run(
        ["plasma-apply-wallpaperimage", abs_path],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Wallpaper updated.")
    else:
        print("Wallpaper not updated:", result.stderr)

    # Son 5 cover dosyası kalsın
    files = sorted(glob.glob("cover_*.jpg"), reverse=True)
    for f in files[5:]:
        try:
            os.remove(f)
        except:
            pass

def create_stylish_wallpaper(image_path, track_name, artist_name):
    base = Image.open(image_path).convert("RGB")

    # Ekran çözünürlüğü (manuel yazabilirsin)
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

    # Blur arkaplan
    background = base.resize((SCREEN_WIDTH, SCREEN_HEIGHT))
    background = background.filter(ImageFilter.GaussianBlur(25))

    overlay = Image.new("RGBA", background.size, (0, 0, 0, 120))
    background = Image.alpha_composite(background.convert("RGBA"), overlay)

    # Orta kapak
    cover_size = 600
    cover = base.resize((cover_size, cover_size))

    x = (SCREEN_WIDTH - cover_size) // 2
    y = (SCREEN_HEIGHT - cover_size) // 2 - 50

    background.paste(cover, (x, y))

    draw = ImageDraw.Draw(background)

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Yazı ortalama
    bbox = draw.textbbox((0, 0), track_name, font=font_big)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]


    bbox2 = draw.textbbox((0, 0), artist_name, font=font_small)
    w2 = bbox2[2] - bbox2[0]
    h2 = bbox2[3] - bbox2[1]


    final_name = f"styled_{int(time.time())}.jpg"
    background.convert("RGB").save(final_name, quality=95)

    return final_name
# -------------------------------
# Image Downloader
# -------------------------------

def download_image(url):
    filename = f"cover_{int(time.time())}.jpg"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except RequestException as e:
        print("image cannot downloaded:", e)
        return None

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename


# -------------------------------
# MAIN LOOP
# -------------------------------

print("Spotify Live Wallpaper started...\n")

try:
    while True:
        print("checking...")

        current = sp.current_user_playing_track()

        if current and current.get("item"):
            image_url = current["item"]["album"]["images"][0]["url"]

            if image_url != LAST_IMAGE_URL:
                print("New cover found!")

                new_file = download_image(image_url)

                if new_file:
                    styled = create_stylish_wallpaper(
                        new_file,
                        current["item"]["name"],
                        current["item"]["artists"][0]["name"]
                    )
                    set_wallpaper(styled)
                    LAST_IMAGE_URL = image_url


        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("\nexit.")
