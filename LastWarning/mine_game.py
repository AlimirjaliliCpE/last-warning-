"""
هشدار آخر | شبیه‌ساز ایمنی معدن
Last Warning - Persian mine safety quiz game (pygame)

Install:   pip install pygame arabic-reshaper python-bidi
Run:       python mine_game.py

Folders next to this file (all optional, the game has fallbacks):
    images/   -> real photos (see IMAGE_KEYS below)
    fonts/    -> Vazirmatn-Regular.ttf (and Vazirmatn-Bold.ttf) for nicer Persian text
"""

import os
import sys
import math
import random
from functools import lru_cache

import pygame
import arabic_reshaper
from bidi.algorithm import get_display

pygame.init()

# ==================================================
# SETTINGS
# ==================================================

WIDTH, HEIGHT = 1100, 700
# When packed with PyInstaller, files are extracted to sys._MEIPASS
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(BASE_DIR, "images")
FONT_DIR = os.path.join(BASE_DIR, "fonts")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("هشدار آخر | شبیه‌ساز ایمنی معدن")
clock = pygame.time.Clock()

# Colors
BG = (12, 16, 23)
PANEL = (14, 18, 26, 205)
WHITE = (245, 247, 250)
GRAY = (170, 182, 195)
RED = (232, 55, 55)
DARK_RED = (112, 27, 34)
YELLOW = (255, 196, 55)
GREEN = (55, 210, 130)
DARK_GREEN = (24, 90, 62)
BLACK = (5, 8, 12)
BROWN = (99, 75, 55)
STEEL = (45, 55, 70)

TIMER_OPTIONS = [10, 15, 20, 30]
question_time = 15
FEEDBACK_AUTO_MS = 6000

# ==================================================
# PERSIAN TEXT HELPERS
# ==================================================


@lru_cache(maxsize=None)
def fa(text):
    """Reshape + reorder text so Persian shows correctly in pygame."""
    return get_display(arabic_reshaper.reshape(str(text)))


def fa_num(number):
    """Convert 0-9 digits to Persian digits."""
    return str(number).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def load_font(size, bold=False):
    # 1) font file inside the fonts/ folder
    names = ["Vazirmatn-Bold.ttf", "Vazir-Bold.ttf"] if bold else \
            ["Vazirmatn-Regular.ttf", "Vazir.ttf", "Vazir-Regular.ttf"]
    for name in names:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            return pygame.font.Font(path, size)

    # 2) system fonts that support Persian letters
    for name in ["vazirmatn", "tahoma", "segoeui", "arial",
                 "dejavusans", "notosansarabic", "notonaskharabic"]:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)

    return pygame.font.Font(None, size)


F_SMALL = load_font(20)
F_TEXT = load_font(24)
F_MED = load_font(32, bold=True)
F_BIG = load_font(46, bold=True)
F_TITLE = load_font(76, bold=True)


def draw_text(text, font, color, x, y, align="center"):
    """Draw one line. align: 'right', 'left' or 'center'. y is the vertical center."""
    image = font.render(fa(text), True, color)
    rect = image.get_rect()
    if align == "right":
        rect.midright = (x, y)
    elif align == "left":
        rect.midleft = (x, y)
    else:
        rect.center = (x, y)
    screen.blit(image, rect)
    return rect


def wrap_text(text, font, max_width):
    """Split a logical Persian string into lines that fit max_width."""
    lines = []
    current = ""
    for word in text.split():
        test = (current + " " + word).strip()
        if font.size(fa(test))[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def draw_wrapped(text, font, color, x, y_top, max_width, line_height,
                 align="right", max_lines=4):
    lines = wrap_text(text, font, max_width)[:max_lines]
    for i, line in enumerate(lines):
        draw_text(line, font, color, x, y_top + i * line_height, align)
    return len(lines)


# ==================================================
# IMAGES
# ==================================================
# Put your real photos in the images/ folder with these names
# (.jpg, .jpeg, .png or .webp):
#   tunnel   -> menu / result background and fallback background
#   cable, gas, vehicle, ppe, roof, fire, dust, blast -> one per scenario
#   worker   -> PNG of a miner with transparent background (optional)

_image_cache = {}


def _find_image_path(name):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        path = os.path.join(IMAGE_DIR, name + ext)
        if os.path.exists(path):
            return path
    return None


def load_background(name):
    """Load a photo scaled to cover the whole window (cropped in the center)."""
    if name in _image_cache:
        return _image_cache[name]

    result = None
    path = _find_image_path(name)
    if path:
        try:
            img = pygame.image.load(path).convert()
            scale = max(WIDTH / img.get_width(), HEIGHT / img.get_height())
            new_size = (int(img.get_width() * scale) + 1,
                        int(img.get_height() * scale) + 1)
            img = pygame.transform.smoothscale(img, new_size)
            x = (img.get_width() - WIDTH) // 2
            y = (img.get_height() - HEIGHT) // 2
            result = img.subsurface((x, y, WIDTH, HEIGHT)).copy()
        except pygame.error:
            result = None

    _image_cache[name] = result
    return result


def load_worker(height):
    key = ("worker", height)
    if key in _image_cache:
        return _image_cache[key]

    result = None
    path = _find_image_path("worker")
    if path:
        try:
            img = pygame.image.load(path).convert_alpha()
            ratio = height / img.get_height()
            result = pygame.transform.smoothscale(
                img, (int(img.get_width() * ratio), height))
        except pygame.error:
            result = None

    _image_cache[key] = result
    return result


DARK_OVERLAY = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
DARK_OVERLAY.fill((0, 0, 0, 95))


def draw_fallback_background():
    """Simple tunnel drawing, used only when no photo is available."""
    screen.fill(BG)
    pygame.draw.polygon(screen, (32, 37, 45),
                        [(0, 0), (WIDTH, 0), (WIDTH, 470),
                         (880, 535), (220, 535), (0, 470)])
    for x in range(45, WIDTH, 175):
        pygame.draw.line(screen, BROWN, (x, 35), (x, 450), 10)
        pygame.draw.line(screen, BROWN, (x, 35), (x + 65, 95), 7)
    pygame.draw.rect(screen, (45, 43, 40), (0, 500, WIDTH, 200))
    pygame.draw.line(screen, GRAY, (0, 570), (WIDTH, 570), 5)
    pygame.draw.line(screen, GRAY, (0, 615), (WIDTH, 615), 5)


def draw_background(name="tunnel"):
    img = load_background(name) or load_background("tunnel")
    if img:
        screen.blit(img, (0, 0))
        screen.blit(DARK_OVERLAY, (0, 0))
    else:
        draw_fallback_background()


def draw_fallback_worker(x, y):
    """Small drawn miner, used only when images/worker.png is missing."""
    s = 1.6
    def p(dx, dy):
        return (int(x + dx * s), int(y + dy * s))

    pygame.draw.line(screen, (35, 40, 48), p(-10, 38), p(-18, 78), 20)
    pygame.draw.line(screen, (35, 40, 48), p(10, 38), p(20, 78), 20)
    pygame.draw.rect(screen, (222, 156, 35),
                     (*p(-22, -5), int(44 * s), int(49 * s)), border_radius=10)
    pygame.draw.rect(screen, WHITE, (*p(-21, 10), int(42 * s), 7))
    pygame.draw.rect(screen, WHITE, (*p(-21, 28), int(42 * s), 7))
    pygame.draw.circle(screen, (193, 143, 107), p(0, -22), int(19 * s))
    pygame.draw.rect(screen, YELLOW, (*p(-23, -34), int(46 * s), 12),
                     border_radius=5)
    pygame.draw.circle(screen, WHITE, p(3, -29), 5)


def draw_worker():
    img = load_worker(300)
    if img:
        screen.blit(img, (60, 548 - img.get_height()))
    else:
        draw_fallback_worker(150, 380)


# ==================================================
# UI HELPERS
# ==================================================


def panel(rect, color=PANEL, border=None, radius=14):
    surf = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(surf, color, (0, 0, rect[2], rect[3]), border_radius=radius)
    screen.blit(surf, (rect[0], rect[1]))
    if border:
        pygame.draw.rect(screen, border, rect, 2, border_radius=radius)


def button(text, rect, mouse_pos, color=DARK_RED, number=None, hover=True):
    hovered = hover and rect.collidepoint(mouse_pos)
    fill = tuple(min(255, c + 45) for c in color) if hovered else color
    pygame.draw.rect(screen, fill, rect, border_radius=12)
    pygame.draw.rect(screen, (190, 200, 210) if hovered else (120, 130, 140),
                     rect, 2, border_radius=12)

    if number is None:
        draw_text(text, F_TEXT, WHITE, rect.centerx, rect.centery)
        return

    # Number badge on the right side (Persian reads right-to-left)
    badge = (rect.right - 38, rect.centery)
    pygame.draw.circle(screen, YELLOW, badge, 20)
    draw_text(fa_num(number), F_MED, BLACK, badge[0], badge[1] - 2)

    text_right = rect.right - 75
    text_width = rect.width - 100
    lines = wrap_text(text, F_SMALL, text_width)[:3]
    top = rect.centery - (len(lines) - 1) * 13
    for i, line in enumerate(lines):
        draw_text(line, F_SMALL, WHITE, text_right, top + i * 26, "right")


# ==================================================
# SCENARIOS (Persian)
# "image" is the file name (without extension) inside images/
# ==================================================

SCENARIOS = [
    {
        "title": "کابل برق آسیب‌دیده",
        "description": "در نزدیکی یک منطقه خیس، یک کابل برق آسیب‌دیده پیدا کرده‌اید.",
        "options": [
            "نادیده می‌گیرم و به کارم ادامه می‌دهم",
            "فاصله می‌گیرم و خطر را گزارش می‌دهم",
        ],
        "correct": 1,
        "explanation": "از محل دور شوید، به دیگران هشدار دهید و موضوع را گزارش کنید. "
                       "فقط افراد مجاز باید خطر برق را ایزوله کنند.",
        "image": "cable",
    },
    {
        "title": "آلارم ردیاب گاز",
        "description": "ردیاب گاز شما در عمق معدن آلارم می‌دهد.",
        "options": [
            "طبق روال اضطراری عمل می‌کنم و تخلیه می‌شوم",
            "به کار ادامه می‌دهم و بعداً بررسی می‌کنم",
        ],
        "correct": 0,
        "explanation": "آلارم را جدی بگیرید و طبق دستورالعمل اضطراری و تخلیه معدن عمل کنید. "
                       "گازهایی مثل متان و مونوکسیدکربن بسیار خطرناک‌اند.",
        "image": "gas",
    },
    {
        "title": "حرکت خطرناک ماشین‌آلات",
        "description": "یک خودروی معدنی به سمت همکارتان که در مسیر آن ایستاده نزدیک می‌شود.",
        "options": [
            "از نزدیک پشت خودرو می‌دوم",
            "از مسیر دور می‌مانم و به اپراتور هشدار می‌دهم",
        ],
        "correct": 1,
        "explanation": "از مسیر حرکت و نقاط کور خودروها دور بمانید و قوانین ترافیکی معدن را رعایت کنید.",
        "image": "vehicle",
    },
    {
        "title": "نبود تجهیزات حفاظتی",
        "description": "همکارتان می‌خواهد بدون عینک ایمنی وارد محل کار شود.",
        "options": [
            "ورود را تا فراهم شدن تجهیزات متوقف می‌کنم",
            "چون کار کوتاه است اجازه ورود می‌دهم",
        ],
        "correct": 0,
        "explanation": "تجهیزات حفاظتی الزامی را باید حتی برای کارهای کوتاه هم استفاده کرد.",
        "image": "ppe",
    },
    {
        "title": "احتمال ناپایداری سقف",
        "description": "ریزش سنگ‌ریزه و ترک‌هایی را در سقف تونل مشاهده می‌کنید.",
        "options": [
            "برای بررسی ترک‌ها نزدیک‌تر می‌روم",
            "از منطقه خطر خارج می‌شوم و فوراً گزارش می‌دهم",
        ],
        "correct": 1,
        "explanation": "از منطقه آسیب‌دیده خارج شوید، به دیگران هشدار دهید و طبق روال "
                       "کنترل زمین معدن عمل کنید.",
        "image": "roof",
    },
    {
        "title": "دود و آتش‌سوزی",
        "description": "هنگام کار، دود غلیظی از یک تجهیزات برقی بلند می‌شود.",
        "options": [
            "بدون اعلام خطر سعی می‌کنم خودم همه‌چیز را مهار کنم",
            "اعلام خطر می‌کنم و از مسیر امن خارج می‌شوم",
        ],
        "correct": 1,
        "explanation": "ابتدا اعلام خطر کنید و مسیر خروج امن را حفظ کنید. اطفای حریق فقط "
                       "برای افراد آموزش‌دیده و در شرایط امن است.",
        "image": "fire",
    },
    {
        "title": "گرد و غبار زیاد",
        "description": "غلظت گرد و غبار بالا رفته و دید در تونل کم شده است.",
        "options": [
            "ماسک مناسب می‌زنم و به سرپرست اطلاع می‌دهم",
            "ماسک را برمی‌دارم تا راحت‌تر نفس بکشم",
        ],
        "correct": 0,
        "explanation": "گرد و غبار معدن به ریه آسیب می‌زند. از ماسک مناسب استفاده کنید و "
                       "ضعف تهویه یا آب‌پاشی را گزارش دهید.",
        "image": "dust",
    },
    {
        "title": "ناحیه آتشباری",
        "description": "آژیر آتشباری به صدا درآمده و هنوز علامت پایان خطر اعلام نشده است.",
        "options": [
            "از محدوده دور می‌مانم تا علامت امن اعلام شود",
            "برای دیدن نتیجه به محدوده نزدیک می‌شوم",
        ],
        "correct": 0,
        "explanation": "تا اعلام رسمی پایان خطر، از محدوده آتشباری دور بمانید.",
        "image": "blast",
    },
]

# ==================================================
# GAME STATE
# ==================================================

state = "menu"  # menu, settings, game, feedback, result
question_order = []
q_number = 0
current_options = []  # list of (text, is_correct), shuffled for each question
score = 0
lives = 3
alert = 0
correct_count = 0
time_left = question_time
question_start = 0
feedback_start = 0
feedback_message = ""
feedback_color = GREEN
selected_answer = None  # index of clicked button, -1 for timeout

# Button rectangles
OPTION_RECTS = [pygame.Rect(555, 560, 515, 88),   # option 1 (right side)
                pygame.Rect(30, 560, 515, 88)]    # option 2 (left side)
MENU_START = pygame.Rect(390, 340, 320, 65)
MENU_SETTINGS = pygame.Rect(390, 425, 320, 65)
MENU_EXIT = pygame.Rect(390, 510, 320, 65)
SET_CHANGE = pygame.Rect(390, 400, 320, 65)
SET_BACK = pygame.Rect(390, 500, 320, 65)
RES_AGAIN = pygame.Rect(365, 465, 370, 65)
RES_MENU = pygame.Rect(365, 545, 370, 65)


def current_scenario():
    return SCENARIOS[question_order[q_number]]


def load_question():
    global current_options, time_left, question_start, selected_answer
    s = current_scenario()
    current_options = [(text, i == s["correct"])
                       for i, text in enumerate(s["options"])]
    random.shuffle(current_options)
    time_left = question_time
    selected_answer = None
    question_start = pygame.time.get_ticks()


def start_game():
    global state, question_order, q_number, score, lives, alert, correct_count
    question_order = list(range(len(SCENARIOS)))
    random.shuffle(question_order)
    q_number = 0
    score = 0
    lives = 3
    alert = 0
    correct_count = 0
    load_question()
    state = "game"


def choose_answer(index):
    """index = 0 or 1 (button), or -1 when time is over."""
    global state, score, lives, alert, correct_count
    global feedback_start, feedback_message, feedback_color, selected_answer

    if state != "game":
        return

    selected_answer = index

    if index >= 0 and current_options[index][1]:
        bonus = int(time_left) * 3
        score += 100 + bonus
        alert = max(0, alert - 1)
        correct_count += 1
        feedback_message = f"درست بود! {fa_num(100 + bonus)}+ امتیاز"
        feedback_color = GREEN
    else:
        lives -= 1
        alert = min(10, alert + 3)
        score = max(0, score - 25)
        if index == -1:
            feedback_message = "زمان تمام شد!"
        else:
            feedback_message = "تصمیم اشتباه بود!"
        feedback_color = RED

    feedback_start = pygame.time.get_ticks()
    state = "feedback"


def next_question():
    global q_number, state
    if lives <= 0 or q_number >= len(question_order) - 1:
        state = "result"
        return
    q_number += 1
    load_question()
    state = "game"


# ==================================================
# DRAWING THE SCREENS
# ==================================================


def draw_hud():
    panel((20, 12, WIDTH - 40, 84))

    draw_text("هشدار آخر", F_MED, RED, WIDTH - 45, 38, "right")
    draw_text(f"مرحله {fa_num(q_number + 1)} از {fa_num(len(question_order))}",
              F_SMALL, WHITE, WIDTH - 45, 70, "right")

    draw_text(f"امتیاز: {fa_num(score)}", F_TEXT, WHITE, 45, 36, "left")
    label = draw_text("جان‌ها:", F_SMALL, GRAY, 45, 70, "left")
    for i in range(3):
        color = GREEN if i < lives else (70, 75, 82)
        pygame.draw.circle(screen, color, (label.right + 22 + i * 26, 70), 9)

    # Alert meter
    draw_text("سطح هشدار", F_SMALL, YELLOW, WIDTH // 2, 32)
    pygame.draw.rect(screen, (65, 65, 70), (450, 52, 200, 18), border_radius=6)
    if alert > 0:
        pygame.draw.rect(screen, RED, (450, 52, alert * 20, 18), border_radius=6)


def draw_question(reveal=False):
    s = current_scenario()

    panel((30, 105, 1040, 128))
    draw_text(s["title"], F_MED, YELLOW, 1050, 135, "right")
    draw_wrapped(s["description"], F_TEXT, WHITE, 1050, 182, 860, 32,
                 "right", max_lines=2)

    # Timer number (left side of the panel)
    remaining = max(0, time_left)
    timer_color = RED if remaining <= 5 else WHITE
    draw_text(fa_num(math.ceil(remaining)), F_BIG, timer_color, 90, 150)
    draw_text("ثانیه", F_SMALL, GRAY, 90, 195)

    # Timer bar
    fraction = remaining / question_time if question_time else 0
    bar_color = GREEN if fraction > 0.5 else YELLOW if fraction > 0.25 else RED
    pygame.draw.rect(screen, (50, 55, 62), (30, 240, 1040, 9), border_radius=4)
    pygame.draw.rect(screen, bar_color,
                     (30, 240, int(1040 * fraction), 9), border_radius=4)

    # Answer buttons
    mouse_pos = pygame.mouse.get_pos()
    for i, rect in enumerate(OPTION_RECTS):
        text, is_correct = current_options[i]
        if reveal:
            if is_correct:
                color = DARK_GREEN
            elif i == selected_answer:
                color = DARK_RED
            else:
                color = (40, 44, 50)
        else:
            color = STEEL
        button(text, rect, mouse_pos, color, number=i + 1, hover=not reveal)

    if not reveal:
        draw_text("روی گزینه کلیک کنید یا کلید ۱ و ۲ را بزنید",
                  F_SMALL, GRAY, WIDTH // 2, 672)


def draw_scene():
    draw_background(current_scenario()["image"])
    draw_worker()
    draw_hud()
    draw_question(reveal=(state == "feedback"))


def draw_menu(mouse):
    draw_background("tunnel")
    panel((270, 70, 560, 530), border=RED, radius=24)

    draw_text("هشدار آخر", F_TITLE, RED, WIDTH // 2, 160)
    draw_text("شبیه‌ساز ایمنی معدن", F_TEXT, GRAY, WIDTH // 2, 235)

    button("شروع بازی", MENU_START, mouse)
    button("تنظیمات", MENU_SETTINGS, mouse, STEEL)
    button("خروج", MENU_EXIT, mouse, (75, 30, 35))

    draw_text("تصمیم درست بگیر", F_SMALL, YELLOW, WIDTH // 2, 630)


def draw_settings(mouse):
    draw_background("tunnel")
    panel((250, 120, 600, 470), radius=20)

    draw_text("تنظیمات", F_TITLE, RED, WIDTH // 2, 205)
    draw_text("زمان هر سوال", F_TEXT, WHITE, WIDTH // 2, 305)
    draw_text(f"{fa_num(question_time)} ثانیه", F_MED, YELLOW, WIDTH // 2, 350)

    button("تغییر زمان", SET_CHANGE, mouse)
    button("بازگشت به منو", SET_BACK, mouse, STEEL)


def draw_feedback_box():
    panel((110, 262, 880, 280), color=(0, 0, 0, 225), border=feedback_color,
          radius=18)
    draw_text(feedback_message, F_BIG, feedback_color, WIDTH // 2, 312)
    draw_wrapped(current_scenario()["explanation"], F_TEXT, WHITE,
                 WIDTH // 2, 380, 800, 36, "center", max_lines=4)
    draw_text("برای ادامه کلیک کنید یا Enter بزنید", F_SMALL, GRAY,
              WIDTH // 2, 515)


def draw_result(mouse):
    draw_background("tunnel")
    panel((240, 80, 620, 540), radius=20)

    draw_text("پایان ماموریت", F_MED, RED, WIDTH // 2, 135)

    percent = correct_count / max(1, len(question_order))
    if lives <= 0:
        draw_text("ماموریت ناموفق بود", F_BIG, RED, WIDTH // 2, 205)
    elif percent >= 0.8:
        draw_text("آفرین! افسر ایمنی حرفه‌ای", F_MED, GREEN, WIDTH // 2, 205)
    else:
        draw_text("خوب بود، کمی بیشتر تمرین کن", F_MED, YELLOW, WIDTH // 2, 205)

    draw_text(f"امتیاز نهایی: {fa_num(score)}", F_BIG, WHITE, WIDTH // 2, 280)
    draw_text(f"پاسخ‌های درست: {fa_num(correct_count)} از {fa_num(len(question_order))}",
              F_TEXT, WHITE, WIDTH // 2, 340)
    draw_text(f"جان‌های باقی‌مانده: {fa_num(lives)}", F_TEXT, YELLOW, WIDTH // 2, 385)
    draw_text(f"سطح هشدار: {fa_num(alert)} از {fa_num(10)}", F_TEXT, RED,
              WIDTH // 2, 430)

    button("بازی دوباره", RES_AGAIN, mouse)
    button("منوی اصلی", RES_MENU, mouse, STEEL)


# ==================================================
# MAIN LOOP
# ==================================================

while True:
    mouse = pygame.mouse.get_pos()
    now = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if state == "menu":
                    pygame.quit()
                    sys.exit()
                else:
                    state = "menu"

            elif state == "game":
                if event.key in (pygame.K_1, pygame.K_KP1, pygame.K_RIGHT):
                    choose_answer(0)
                elif event.key in (pygame.K_2, pygame.K_KP2, pygame.K_LEFT):
                    choose_answer(1)

            elif state == "feedback":
                if event.key == pygame.K_RETURN:
                    next_question()

            elif state == "result":
                if event.key == pygame.K_r:
                    start_game()
                elif event.key == pygame.K_RETURN:
                    state = "menu"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "menu":
                if MENU_START.collidepoint(event.pos):
                    start_game()
                elif MENU_SETTINGS.collidepoint(event.pos):
                    state = "settings"
                elif MENU_EXIT.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            elif state == "settings":
                if SET_CHANGE.collidepoint(event.pos):
                    position = TIMER_OPTIONS.index(question_time) \
                        if question_time in TIMER_OPTIONS else 0
                    question_time = TIMER_OPTIONS[(position + 1) % len(TIMER_OPTIONS)]
                elif SET_BACK.collidepoint(event.pos):
                    state = "menu"

            elif state == "game":
                if OPTION_RECTS[0].collidepoint(event.pos):
                    choose_answer(0)
                elif OPTION_RECTS[1].collidepoint(event.pos):
                    choose_answer(1)

            elif state == "feedback":
                next_question()

            elif state == "result":
                if RES_AGAIN.collidepoint(event.pos):
                    start_game()
                elif RES_MENU.collidepoint(event.pos):
                    state = "menu"

    if state == "menu":
        draw_menu(mouse)

    elif state == "settings":
        draw_settings(mouse)

    elif state == "game":
        elapsed = (now - question_start) / 1000
        time_left = max(0, question_time - elapsed)
        if time_left <= 0:
            choose_answer(-1)
        draw_scene()

    elif state == "feedback":
        draw_scene()
        draw_feedback_box()
        if now - feedback_start > FEEDBACK_AUTO_MS:
            next_question()

    elif state == "result":
        draw_result(mouse)

    pygame.display.flip()
    clock.tick(60)