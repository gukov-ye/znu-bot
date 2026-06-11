import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
DATA_DIR = os.environ.get("DATA_DIR", "/data")
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except OSError:
    DATA_DIR = "."
USERS_FILE = os.path.join(DATA_DIR, "users.txt")
BUTTON_STATS_FILE = os.path.join(DATA_DIR, "button_stats.json")

def load_button_stats() -> dict:
    if not os.path.exists(BUTTON_STATS_FILE):
        return {}
    with open(BUTTON_STATS_FILE) as f:
        return json.load(f)

def record_button_click(data: str):
    stats = load_button_stats()
    stats[data] = stats.get(data, 0) + 1
    with open(BUTTON_STATS_FILE, "w") as f:
        json.dump(stats, f, ensure_ascii=False)

def save_user(chat_id: int) -> bool:
    ids = load_users()
    if chat_id not in ids:
        with open(USERS_FILE, "a") as f:
            f.write(str(chat_id) + "\n")
        return True
    return False

def load_users() -> list[int]:
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return [int(line.strip()) for line in f if line.strip()]

SOON = "ℹ️ Інформація з'явиться незабаром. Слідкуй за оновленнями на <a href=\"https://pk.znu.edu.ua\">pk.znu.edu.ua</a>"
CONTACTS = (
    "\n\n📍 <b>Приймальна комісія</b>\nвул. Університетська, 66-Б (каб. 115)"
    "\n📧 Email: <a href=\"mailto:pk.znu.ua@gmail.com\">pk.znu.ua@gmail.com</a>"
    "\n🔗 <a href=\"https://beacons.ai/official_znu\">Соцмережі ЗНУ</a>"
)

FACULTIES = [
    ("bio", "🌿 Біологічний", "🌿 Біологічний факультет"),
    ("econ", "📊 Економічний", "📊 Економічний факультет"),
    ("math", "📐 Математичний", "📐 Математичний факультет"),
    ("journ", "📰 Журналістики", "📰 Факультет журналістики"),
    ("fif", "🌍 Іноземної філології", "🌍 Факультет іноземної філології"),
    ("history", "📜 Історії та міжнар. відносин", "📜 Факультет історії та міжнародних відносин"),
    ("spp", "🧠 Соц. педагогіки та психології", "🧠 Факультет соціальної педагогіки та психології"),
    ("fsu", "🏢 Соціології та управління", "🏢 Факультет соціології та управління"),
    ("management", "💼 Менеджменту", "💼 Факультет менеджменту"),
    ("fizvosp", "🏃 Фізвиховання, здоров'я та туризму", "🏃 Факультет фізичного виховання, здоров'я та туризму"),
    ("philology", "📖 Філологічний", "📖 Філологічний факультет"),
    ("law", "⚖️ Юридичний", "⚖️ Юридичний факультет"),
    ("institute", "⚙️ Інженерний інститут", "⚙️ Інженерний інститут"),
    ("liberalarts", "🌀 Liberal Arts and Science", "🌀 Liberal Arts and Science"),
]

SECTORS = [
    ("A", "🎓 Освіта і педагогіка"),
    ("B", "🎭 Мистецтво та гуманітарні"),
    ("C", "📰 Соціальні науки та журналістика"),
    ("D", "💼 Бізнес, управління, право"),
    ("E", "🔬 Природничі науки і математика"),
    ("F", "💻 IT та кібербезпека"),
    ("G", "🏗 Інженерія і будівництво"),
    ("H", "🌾 Сільське господарство"),
    ("I", "🩺 Здоров'я та соціальна сфера"),
    ("J", "🏨 Сфера послуг та туризм"),
    ("K", "🛡 Безпека"),
]

SUBSECTORS = {
    "A": [
        ("A_edu", "📚 Дошкільна та початкова"),
        ("A_sec", "📖 Середня освіта"),
        ("A_spe", "🎯 Спеціальна освіта"),
        ("A_spo", "⚽ Фізична культура і спорт"),
    ],
    "B": [
        ("B_art", "🎨 Мистецтво"),
        ("B_his", "📜 Історія"),
        ("B_phi", "📝 Філологія"),
    ],
    "D": [
        ("D_eco", "📊 Економіка, фінанси, облік"),
        ("D_man", "👔 Менеджмент"),
        ("D_gov", "🏛 Управління"),
        ("D_tra", "🛒 Торгівля"),
        ("D_law", "⚖️ Право"),
    ],
    "G": [
        ("G_ene", "⚡ Енергетика"),
        ("G_ele", "🔌 Електроніка та автоматика"),
        ("G_met", "🔧 Металургія та машинобудування"),
        ("G_bui", "🏛 Будівництво та архітектура"),
        ("G_env", "🌍 Захист довкілля"),
    ],
}

SUBSECTOR_SPECS = {
    "A_edu": (
        "📚 <b>Дошкільна та початкова освіта</b>\n\n"
        "▫️ A2 <b>Дошкільна освіта</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Зубцова Юлія Євгенівна — 050 861 88 99\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12325\">📄 Програма</a>\n\n"
        "▫️ A3 <b>Початкова освіта</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Зубцова Юлія Євгенівна — 050 861 88 99\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12326\">📄 Програма</a>"
    ),
    "A_sec": (
        "📖 <b>Середня освіта</b>\n\n"
        "▫️ A4 <b>Українська мова і література</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Бакаленко Ірина Миколаївна — 066 238 85 31\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12327\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Історія та громадянська освіта</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Ігнатуша Олександр Миколайович — 068 480 93 95\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12329\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Математика</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Гречнєва Марина Олександрівна — 097 730 32 74\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12330\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Біологія та здоров'я людини</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Перетятько Вікторія Віталіївна — 097 528 07 80\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12331\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Географія</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Ігнатуша Олександр Миколайович — 068 480 93 95\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/13123\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Фізика та астрономія</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Андрєєв Андрій Миколайович — 066 254 51 49\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12332\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Інформатика</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Решевська Катерина Сергіївна — 096 669 42 06\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12333\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Фізична культура</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Соколова Ольга Валентинівна — 050 456 73 36\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12334\">📄 Програма</a>\n\n"
        "▫️ A4 <b>Мова і література (англійська)</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Надточій Наталя Олександрівна — 063 187 64 21\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12328\">📄 Програма</a>"
    ),
    "A_spe": (
        "🎯 <b>Спеціальна освіта</b>\n\n"
        "▫️ A6 <b>Логопедія</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Заверико Наталія Віталіївна — 050 987 77 83\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12335\">📄 Програма</a>"
    ),
    "A_spo": (
        "⚽ <b>Фізична культура і спорт</b>\n\n"
        "▫️ A7 <b>Спорт</b> ⭐\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Сватьєв Андрій Вячеславович — 067 901 81 11\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12337\">📄 Програма</a>\n\n"
        "▫️ A7 <b>Фізичне виховання</b> ⭐\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Коваленко Юлія Олексіївна — 050 471 89 05\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12336\">📄 Програма</a>\n\n"
        "⭐ — потрібен творчий конкурс"
    ),
    "B_art": (
        "🎨 <b>Мистецтво</b>\n\n"
        "▫️ B2 <b>Графічний дизайн</b> ⭐\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Чемерис Ганна Юріївна — 068 446 84 96\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12339\">📄 Програма</a>\n\n"
        "▫️ B6 <b>Театральне мистецтво</b> ⭐\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Петрик Тетяна Дмитрівна — 050 484 87 68\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12340\">📄 Програма</a>\n\n"
        "⭐ — потрібен творчий конкурс"
    ),
    "B_his": (
        "📜 <b>Історія</b>\n\n"
        "▫️ B9 <b>Історія</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Головко Юлія Іванівна — 063 827 58 15\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12352\">📄 Програма</a>"
    ),
    "B_phi": (
        "📝 <b>Філологія</b>\n\n"
        "▫️ B11 <b>Українська мова та література</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Бондаренко Ірина Станіславівна — 095 821 50 55\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12355\">📄 Програма</a>\n\n"
        "▫️ B11 <b>Польська мова і література, англійська мова</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Бакаленко Ірина Миколаївна — 066 238 85 31\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12357\">📄 Програма</a>\n\n"
        "▫️ B11 <b>Мова і література (англійська)</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Шевчук Оксана Василівна — 095 581 72 01\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12358\">📄 Програма</a>\n\n"
        "▫️ B11 <b>Переклад (англійський)</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Запольських Світлана Петрівна — 066 325 93 26\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12360\">📄 Програма</a>\n\n"
        "▫️ B11 <b>Німецька мова і література, англійська мова</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Вапіров Сергій Юрійович — 068 822 42 49\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12359\">📄 Програма</a>\n\n"
        "▫️ B11 <b>Іспанська мова і література, англійська мова</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Тєлкова Оксана Василівна — 095 690 40 40\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12363\">📄 Програма</a>\n\n"
        "▫️ B11 <b>Французька мова і література, англійська мова</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Тарасюк Інна Василівна — 067 976 53 40\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12362\">📄 Програма</a>"
    ),
    "D_eco": (
        "📊 <b>Економіка, фінанси, облік</b>\n\n"
        "▫️ D1 <b>Облік, оподаткування та аудит</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Меліхова Тетяна Олегівна — 099 250 18 22\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12378\">📄 Програма</a>\n\n"
        "▫️ D2 <b>Фінанси і кредит</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Гельман Валентина Миколаївна — 096 790 17 10\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12379\">📄 Програма</a>\n\n"
        "▫️ D5 <b>Маркетинг</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Гельман Валентина Миколаївна — 096 790 17 10\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12384\">📄 Програма</a>"
    ),
    "D_man": (
        "👔 <b>Менеджмент</b>\n\n"
        "▫️ D3 <b>Менеджмент міжнародного бізнесу</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Маркова Світлана Вікторівна — 068 863 73 15\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12383\">📄 Програма</a>\n\n"
        "▫️ D3 <b>Менеджмент організацій</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Павлюк Тетяна Сергіївна — 050 557 44 50\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12383\">📄 Програма</a>\n\n"
        "▫️ D3 <b>Економіка та управління бізнесом</b>\n"
        "   📋 денна (тільки контракт), заочна (тільки контракт)\n"
        "   👤 Голомб Вікторія Володимирівна — 097 806 62 15"
    ),
    "D_gov": (
        "🏛 <b>Управління</b>\n\n"
        "▫️ D4 <b>Публічне управління та адміністрування</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Ажажа Марина Андріївна — 066 911 84 05\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12407\">📄 Програма</a>"
    ),
    "D_tra": (
        "🛒 <b>Торгівля</b>\n\n"
        "▫️ D7 <b>Торгівля та комерційна логістика</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Павлюк Тетяна Сергіївна — 050 557 44 50\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12385\">📄 Програма</a>"
    ),
    "D_law": (
        "⚖️ <b>Право</b>\n\n"
        "▫️ D8 <b>Право</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 066 781 20 11\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12387\">📄 Програма</a>"
    ),
    "G_ene": (
        "⚡ <b>Енергетика</b>\n\n"
        "▫️ G3 <b>Електроенергетика, електротехніка та електромеханіка</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Коваленко Віктор Леонідович — 099 621 96 38\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12488\">📄 Програма</a>\n\n"
        "▫️ G4 <b>Теплоенергетика</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Єрофеєва Аліна Анатоліївна — 097 769 19 53\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12489\">📄 Програма</a>\n\n"
        "▫️ G4 <b>Відновлювані джерела енергії та гідроенергетика</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Коваленко Віктор Леонідович — 099 621 96 38\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12490\">📄 Програма</a>"
    ),
    "G_ele": (
        "🔌 <b>Електроніка та автоматика</b>\n\n"
        "▫️ G5 <b>Мікро- та наносистемна техніка</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Небеснюк Оксана Юріївна — 066 540 98 69\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12492\">📄 Програма</a>\n\n"
        "▫️ G7 <b>Автоматизація, комп'ютерно-інтегровані технології та робототехніка</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Барішенко Олена Миколаївна — 067 911 01 80\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12491\">📄 Програма</a>"
    ),
    "G_met": (
        "🔧 <b>Металургія та машинобудування</b>\n\n"
        "▫️ G10 <b>Металургія</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Бєлоконь Юрій Олександрович — 096 112 95 54\n\n"
        "▫️ G11 <b>Машини та агрегати металургійного виробництва</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Власов Андрій Олександрович — 095 467 82 72\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12486\">📄 Програма</a>"
    ),
    "G_bui": (
        "🏛 <b>Будівництво та архітектура</b>\n\n"
        "▫️ G17 <b>Архітектура та містобудування</b> ⭐\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Фостащенко Олена Миколаївна — 066 851 50 41\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12495\">📄 Програма</a>\n\n"
        "▫️ G19 <b>Міське будівництво та господарство</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Фостащенко Олена Миколаївна — 066 851 50 41\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12497\">📄 Програма</a>\n\n"
        "▫️ G19 <b>Промислове і цивільне будівництво</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Арутюнян Ірина Андріївна — 068 578 39 93\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12497\">📄 Програма</a>\n\n"
        "⭐ — потрібен творчий конкурс"
    ),
    "G_env": (
        "🌍 <b>Захист довкілля</b>\n\n"
        "▫️ G2 <b>Технології захисту навколишнього середовища</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Бєлоконь Карина Володимирівна — 097 735 71 41\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12494\">📄 Програма</a>"
    ),
}

SECTOR_SPECS = {
    "C": (
        "📰 <b>Соціальні науки та журналістика</b>\n\n"
        "▫️ C1 <b>Економічна кібернетика та аналітика даних</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Гельман Валентина Миколаївна — 096 790 17 10\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12366\">📄 Програма</a>\n\n"
        "▫️ C1 <b>Міжнародна економіка</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Гельман Валентина Миколаївна — 096 790 17 10\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12367\">📄 Програма</a>\n\n"
        "▫️ C2 <b>Політологія</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Руднєва Анна Олегівна — 095 338 25 63\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12370\">📄 Програма</a>\n\n"
        "▫️ C3 <b>Міжнародні відносини</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Черкасов Станіслав Сергійович — 097 515 22 63\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12839\">📄 Програма</a>\n\n"
        "▫️ C4 <b>Психологія</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Железнякова Юлія Володимирівна — 067 618 14 97\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12372\">📄 Програма</a>\n\n"
        "▫️ C5 <b>Соціологія</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Приймак Юлія Олександрівна — 097 730 17 50\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12373\">📄 Програма</a>\n\n"
        "▫️ C7 <b>Журналістика</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Тернова Алла Іллівна — 067 892 80 40\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12375\">📄 Програма</a>"
    ),
    "E": (
        "🔬 <b>Природничі науки і математика</b>\n\n"
        "▫️ E1 <b>Біологія</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Новосад Наталя Василівна — 096 084 52 32\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12388\">📄 Програма</a>\n\n"
        "▫️ E2 <b>Екологія</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Домбровський Костянтин Олегович — 097 398 13 05\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12391\">📄 Програма</a>\n\n"
        "▫️ E3 <b>Хімія</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Корнет Марина Миколаївна — 097 802 56 31\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12392\">📄 Програма</a>\n\n"
        "▫️ E6 <b>Прикладна фізика</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Андрєєв Андрій Миколайович — 066 254 51 49\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12393\">📄 Програма</a>\n\n"
        "▫️ E7 <b>Математика</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Гречнєва Марина Олександрівна — 097 730 32 74\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12395\">📄 Програма</a>"
    ),
    "F": (
        "💻 <b>IT та кібербезпека</b>\n\n"
        "▫️ F1 <b>Комп'ютерне моделювання</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Гречнєва Марина Олександрівна — 097 730 32 74\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12397\">📄 Програма</a>\n\n"
        "▫️ F2 <b>Програмна інженерія</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Гречнєва Марина Олександрівна — 097 730 32 74\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12398\">📄 Програма</a>\n\n"
        "▫️ F3 <b>Комп'ютерні науки</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Решевська Катерина Сергіївна — 096 669 42 06\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12399\">📄 Програма</a>\n\n"
        "▫️ F5 <b>Кібербезпека та захист інформації</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Решевська Катерина Сергіївна — 096 669 42 06\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12983\">📄 Програма</a>"
    ),
    "H": (
        "🌾 <b>Сільське господарство</b>\n\n"
        "▫️ H4 <b>Мисливське господарство та рослинні ресурси</b>\n"
        "   📋 денна (є бюджет), заочна (є бюджет)\n"
        "   👤 Дударєва Галина Федорівна — 067 731 01 74\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12401\">📄 Програма</a>"
    ),
    "I": (
        "🩺 <b>Здоров'я та соціальна сфера</b>\n\n"
        "▫️ I7 <b>Фізична терапія, ерготерапія</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Кальонова Ірина Валентинівна — 095 540 71 59\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12402\">📄 Програма</a>\n\n"
        "▫️ I10 <b>Соціальна робота</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Маловічко Олена Владиславівна — 066 913 34 73\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12404\">📄 Програма</a>"
    ),
    "J": (
        "🏨 <b>Сфера послуг та туризм</b>\n\n"
        "▫️ J2 <b>Готельно-ресторанна справа</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Конох Олена Євгенівна — 067 146 01 44\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12405\">📄 Програма</a>\n\n"
        "▫️ J3 <b>Туризм</b>\n"
        "   📋 денна (є бюджет)\n"
        "   👤 Маковецька Наталія Валеріївна — 066 337 37 13\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/12406\">📄 Програма</a>\n\n"
        "▫️ J4 <b>Охорона праці</b>\n"
        "   📋 денна (є бюджет), заочна (тільки контракт)\n"
        "   👤 Манідіна Євгенія Анатоліївна — 097 881 46 92\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/4743/12499\">📄 Програма</a>"
    ),
    "K": (
        "🛡 <b>Безпека</b>\n\n"
        "▫️ K9 <b>Правоохоронна діяльність</b>\n"
        "   📋 денна (тільки контракт), заочна (тільки контракт)\n"
        "   👤 066 781 20 11\n"
        "   <a href=\"https://www.znu.edu.ua/ukr/pk/4362/bakalavr/13012\">📄 Програма</a>"
    ),
}

FACULTY_SPECS = {
    "bio": (
        "🎓 <b>Біологічний факультет</b>\n\n"
        "▫️ <b>Біологія</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Екологія</b> — денна (є бюджет)\n"
        "▫️ <b>Хімія</b> — денна (є бюджет)\n"
        "▫️ <b>Мисливське господарство та рослинні ресурси</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Середня освіта (Біологія та здоров'я людини)</b> — денна (є бюджет)"
    ),
    "econ": (
        "🎓 <b>Економічний факультет</b>\n\n"
        "▫️ <b>Економічна кібернетика та аналітика даних</b> — денна (є бюджет)\n"
        "▫️ <b>Міжнародна економіка</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Фінанси і кредит</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Облік, оподаткування та аудит</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Маркетинг</b> — денна (є бюджет), заочна (тільки контракт)"
    ),
    "history": (
        "🎓 <b>Факультет історії та міжнародних відносин</b>\n\n"
        "▫️ <b>Історія</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Міжнародні відносини</b> — денна (є бюджет)\n"
        "▫️ <b>Середня освіта (Історія та громадянська освіта)</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Середня освіта (Географія)</b> — денна (є бюджет), заочна (є бюджет)"
    ),
    "math": (
        "🎓 <b>Математичний факультет</b>\n\n"
        "▫️ <b>Математика</b> — денна (є бюджет)\n"
        "▫️ <b>Прикладна фізика</b> — денна (є бюджет)\n"
        "▫️ <b>Комп'ютерне моделювання</b> — денна (є бюджет)\n"
        "▫️ <b>Програмна інженерія</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Комп'ютерні науки</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Кібербезпека та захист інформації</b> — денна (є бюджет)\n"
        "▫️ <b>Середня освіта (Математика)</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Середня освіта (Фізика та астрономія)</b> — денна (є бюджет)\n"
        "▫️ <b>Середня освіта (Інформатика)</b> — денна (є бюджет)"
    ),
    "journ": (
        "🎓 <b>Факультет журналістики</b>\n\n"
        "▫️ <b>Журналістика</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Редагування та моделювання медійного контенту</b> — денна (є бюджет)\n"
        "▫️ <b>Реклама і зв'язки з громадськістю</b> — денна (є бюджет)"
    ),
    "fif": (
        "🎓 <b>Факультет іноземної філології</b>\n\n"
        "▫️ <b>Середня освіта (Мова і література (англійська))</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Мова і література (англійська)</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Переклад (англійський)</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Німецька мова і література, англійська мова</b> — денна (є бюджет)\n"
        "▫️ <b>Іспанська мова і література, англійська мова</b> — денна (є бюджет)\n"
        "▫️ <b>Французька мова і література, англійська мова</b> — денна (є бюджет)"
    ),
    "management": (
        "🎓 <b>Факультет менеджменту</b>\n\n"
        "▫️ <b>Менеджмент міжнародного бізнесу</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Менеджмент організацій</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Торгівля та комерційна логістика</b> — денна (є бюджет)\n"
        "▫️ <b>Економіка та управління бізнесом</b> — денна (тільки контракт), заочна (тільки контракт)"
    ),
    "spp": (
        "🎓 <b>Факультет соціальної педагогіки та психології</b>\n\n"
        "▫️ <b>Дошкільна освіта</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Початкова освіта</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Логопедія</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Графічний дизайн</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Театральне мистецтво</b> — денна (є бюджет)\n"
        "▫️ <b>Психологія</b> — денна (є бюджет), заочна (тільки контракт)"
    ),
    "fsu": (
        "🎓 <b>Факультет соціології та управління</b>\n\n"
        "▫️ <b>Соціологія</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Соціологія медіації і кримінології</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Політологія</b> — денна (є бюджет)\n"
        "▫️ <b>Публічне управління та адміністрування</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Європейські філософські студії і креативні індустрії</b> — денна (є бюджет)\n"
        "▫️ <b>Соціальна робота</b> — денна (є бюджет), заочна (тільки контракт)"
    ),
    "philology": (
        "🎓 <b>Філологічний факультет</b>\n\n"
        "▫️ <b>Українська мова та література</b> — денна (є бюджет)\n"
        "▫️ <b>Польська мова і література, англійська мова</b> — денна (є бюджет)\n"
        "▫️ <b>Прикладна лінгвістика</b> — денна (є бюджет)\n"
        "▫️ <b>Середня освіта (Українська мова і література)</b> — денна (є бюджет), заочна (є бюджет)"
    ),
    "fizvosp": (
        "🎓 <b>Факультет фізичного виховання, здоров'я та туризму</b>\n\n"
        "▫️ <b>Спорт</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Фізичне виховання</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Фізична терапія, ерготерапія</b> — денна (є бюджет)\n"
        "▫️ <b>Готельно-ресторанна справа</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Туризм</b> — денна (є бюджет)\n"
        "▫️ <b>Охорона праці</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Середня освіта (Фізична культура)</b> — денна (є бюджет)"
    ),
    "law": (
        "🎓 <b>Юридичний факультет</b>\n\n"
        "▫️ <b>Право</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Правоохоронна діяльність</b> — денна (тільки контракт), заочна (тільки контракт)"
    ),
    "institute": (
        "🎓 <b>Інженерний навчально-науковий інститут ім. Ю.М. Потебні</b>\n\n"
        "▫️ <b>Архітектура та містобудування</b> — денна (є бюджет)\n"
        "▫️ <b>Промислове і цивільне будівництво</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Міське будівництво та господарство</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Металургія</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Машини та агрегати металургійного виробництва</b> — денна (є бюджет)\n"
        "▫️ <b>Автоматизація, комп'ютерно-інтегровані технології та робототехніка</b> — денна (є бюджет)\n"
        "▫️ <b>Електроенергетика, електротехніка та електромеханіка</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Теплоенергетика</b> — денна (є бюджет)\n"
        "▫️ <b>Відновлювані джерела енергії та гідроенергетика</b> — денна (є бюджет)\n"
        "▫️ <b>Мікро- та наносистемна техніка</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Технології захисту навколишнього середовища</b> — денна (є бюджет)\n"
        "▫️ <b>Програмне забезпечення систем</b> — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ <b>Інформаційна економіка</b> — денна (є бюджет)\n"
        "▫️ <b>Публічне управління та адміністрування</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Облік і аудит</b> — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ <b>Фінанси держави та підприємницьких структур</b> — денна (є бюджет), заочна (тільки контракт)"
    ),
    "liberalarts": (
        "🌀 <b>Liberal Arts and Science</b>\n\n"
        "▫️ <b>Liberal Arts and Science</b> — денна (тільки контракт)"
    ),
}

def other_menu():
    keyboard = [
        [InlineKeyboardButton("🏠 Гуртожиток", callback_data="other_dorm")],
        [InlineKeyboardButton("🏙️ Студентське містечко", callback_data="other_studmisto")],
        [InlineKeyboardButton("🎭 Позанавчальні активності", callback_data="other_activities")],
        [InlineKeyboardButton("📞 Контакти", callback_data="other_contacts")],
        [InlineKeyboardButton("Назад", callback_data="bachelor")],
    ]
    return InlineKeyboardMarkup(keyboard)

def activities_menu():
    keyboard = [
        [InlineKeyboardButton("🏛️ Студрада", callback_data="act_studrada")],
        [InlineKeyboardButton("🎨 Творчість", callback_data="act_creativity")],
        [InlineKeyboardButton("⚽ Спорт", callback_data="act_sport")],
        [InlineKeyboardButton("Назад", callback_data="other")],
    ]
    return InlineKeyboardMarkup(keyboard)

def sectors_menu():
    keyboard = [[InlineKeyboardButton(label, callback_data="sector_" + sid)] for sid, label in SECTORS]
    keyboard.append([InlineKeyboardButton("🌀 Liberal Arts and Science", callback_data="spec_liberalarts")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="bachelor")])
    return InlineKeyboardMarkup(keyboard)

def subsectors_menu(sector_id):
    keyboard = [[InlineKeyboardButton(label, callback_data="sub_" + sid)] for sid, label in SUBSECTORS[sector_id]]
    keyboard.append([InlineKeyboardButton("Назад", callback_data="spec_bachelor")])
    return InlineKeyboardMarkup(keyboard)

def faculties_menu(back):
    keyboard = [[InlineKeyboardButton(short, callback_data="faculty_" + fid + "_" + back)] for fid, short, full in FACULTIES]
    keyboard.append([InlineKeyboardButton("Назад", callback_data=back)])
    return InlineKeyboardMarkup(keyboard)

def faculty_menu(fid, back):
    keyboard = [
        [InlineKeyboardButton("Спеціальності", callback_data="fac_" + fid + "_spec_" + back)],
        [InlineKeyboardButton("Контакти", callback_data="fac_" + fid + "_about_" + back)],
        [InlineKeyboardButton("Назад", callback_data="spec_" + back)],
    ]
    return InlineKeyboardMarkup(keyboard)

def bachelor_menu():
    keyboard = [
        [InlineKeyboardButton("🎓 Спеціальності ЗНУ", callback_data="spec_bachelor")],
        [InlineKeyboardButton("📋 Все про вступ", callback_data="bach_questions")],
        [InlineKeyboardButton("ℹ️ Інше", callback_data="other")],
    ]
    return InlineKeyboardMarkup(keyboard)

def bach_questions_menu():
    keyboard = [
        [InlineKeyboardButton("📅 Етапи вступної кампанії", callback_data="bq_stages")],
        [InlineKeyboardButton("💻 Кабінет вступника", callback_data="bq_cabinet")],
        [InlineKeyboardButton("📝 НМТ", callback_data="bq_nmt")],
        [InlineKeyboardButton("✉️ Мотиваційний лист", callback_data="bq_motivation")],
        [InlineKeyboardButton("🎨 Творчий конкурс", callback_data="bq_creative")],
        [InlineKeyboardButton("🎓 Гранти на навчання", callback_data="bq_noexam")],
        [InlineKeyboardButton("💰 Вартість навчання", callback_data="bq_price")],
        [InlineKeyboardButton("🛡️ Пільгові категорії", callback_data="bq_benefits")],
        [InlineKeyboardButton("📄 Документи для вступу", callback_data="bq_docs")],
        [InlineKeyboardButton("🏛 Регіональний коефіцієнт", callback_data="bq_regional")],
        [InlineKeyboardButton("Назад", callback_data="bachelor")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_menu(destination):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=destination)]])

async def notify_admin_new_user(context: ContextTypes.DEFAULT_TYPE, user):
    if not ADMIN_ID:
        return
    if user.username:
        display = f"@{user.username}"
    else:
        name_parts = [user.first_name, user.last_name]
        full_name = " ".join(p for p in name_parts if p)
        display = full_name or "Без імені"
    now = datetime.now(ZoneInfo("Europe/Kyiv"))
    date_str = now.strftime("%d.%m.%Y %H:%M")
    total = len(load_users())
    msg = (
        f"🆕 <b>Новий користувач у боті</b>\n\n"
        f"👤 {display}\n"
        f"🆔 ID: {user.id}\n"
        f"📅 Дата: {date_str}\n"
        f"👥 Всього користувачів: {total}"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="HTML")
    except Exception:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 <b>Вітаю! Я бот для вступників ЗНУ.</b>\n\n"
        "Тут ти знайдеш:\n"
        "— інформацію про вступ на бакалаврат\n"
        "— спеціальності та контакти факультетів\n"
        "— корисне про студентське життя в ЗНУ\n\n"
        "Обери розділ:"
    )
    if update.message:
        is_new = save_user(update.message.chat_id)
        if is_new:
            try:
                await notify_admin_new_user(context, update.effective_user)
            except Exception:
                pass
        await update.message.reply_text(text, reply_markup=bachelor_menu(), parse_mode="HTML")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=bachelor_menu(), parse_mode="HTML", disable_web_page_preview=True)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Немає доступу.")
        return
    text = update.message.text.partition(" ")[2]
    if not text:
        await update.message.reply_text("Використання: /broadcast <текст повідомлення>")
        return
    users = load_users()
    success, failed = 0, 0
    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            success += 1
        except Exception:
            failed += 1
    await update.message.reply_text(f"✅ Надіслано: {success}\n❌ Помилок: {failed}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    record_button_click(data)

    if data in ("start", "bachelor"):
        await query.edit_message_text(
            "👋 <b>Вітаю! Я бот для вступників ЗНУ.</b>\n\n"
            "Тут ти знайдеш:\n"
            "— інформацію про вступ на бакалаврат\n"
            "— спеціальності та контакти факультетів\n"
            "— корисне про студентське життя в ЗНУ\n\n"
            "Обери розділ:",
            reply_markup=bachelor_menu(), parse_mode="HTML"
        )

    elif data == "spec_bachelor":
        await query.edit_message_text(
            "📋 <b>Спеціальності ЗНУ — Бакалаврат</b>\n\nОберіть галузь знань:",
            reply_markup=sectors_menu(), parse_mode="HTML"
        )

    elif data == "spec_liberalarts":
        await query.edit_message_text(
            "🌀 <b>Liberal Arts and Science</b>\n\n"
            "Міждисциплінарна освітня програма, яка поєднує гуманітарні, соціальні та природничі науки в єдиному навчальному просторі.\n\n"
            "Ти сам формуєш свій освітній шлях — обираєш курси з різних галузей знань та розвиваєш критичне мислення, комунікацію та здатність вирішувати складні задачі.\n\n"
            "📌 <b>Форма навчання:</b> денна (тільки контракт)\n\n"
            "<b>Соціальні мережі програми:</b>\n"
            "• <a href=\"https://www.instagram.com/las_znu/\">Instagram</a>\n"
            "• <a href=\"https://www.facebook.com/las.znu/\">Facebook</a>\n"
            "• <a href=\"https://www.tiktok.com/@las_znu\">TikTok</a>\n"
            "• <a href=\"https://t.me/las_znu\">Telegram</a>",
            reply_markup=back_menu("spec_bachelor"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data.startswith("sector_"):
        sid = data[7:]
        if sid in SUBSECTORS:
            sector_name = next(label for s, label in SECTORS if s == sid)
            await query.edit_message_text(
                f"<b>{sector_name}</b>\n\nОберіть підкатегорію:",
                reply_markup=subsectors_menu(sid), parse_mode="HTML"
            )
        else:
            spec_text = SECTOR_SPECS.get(sid, SOON)
            await query.edit_message_text(
                spec_text,
                reply_markup=back_menu("spec_bachelor"), parse_mode="HTML", disable_web_page_preview=True
            )

    elif data.startswith("sub_"):
        sub_id = data[4:]
        sector_id = sub_id.split("_")[0]
        spec_text = SUBSECTOR_SPECS.get(sub_id, SOON)
        await query.edit_message_text(
            spec_text,
            reply_markup=back_menu("sector_" + sector_id), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data.startswith("faculty_"):
        parts = data.split("_", 2)
        fid = parts[1]
        back = parts[2]
        if fid == "liberalarts":
            await query.edit_message_text(
                "🌍 <b>Liberal Arts and Science</b>\n\n"
                "Міждисциплінарна освітня програма, яка поєднує гуманітарні, соціальні та природничі науки в єдиному навчальному просторі.\n\n"
                "Ти сам формуєш свій освітній шлях — обираєш курси з різних галузей знань та розвиваєш критичне мислення, комунікацію та здатність вирішувати складні задачі.\n\n"
                "📌 Форма навчання: денна (тільки контракт)\n\n"
                "Соціальні мережі програми:\n"
                "• <a href=\"https://www.instagram.com/las_znu/\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/las.znu/\">Facebook</a>\n"
                "• <a href=\"https://www.tiktok.com/@las_znu\">TikTok</a>\n"
                "• <a href=\"https://t.me/las_znu\">Telegram</a>",
                reply_markup=back_menu("spec_" + back), parse_mode="HTML", disable_web_page_preview=True
            )
        else:
            name = next((full for i, short, full in FACULTIES if i == fid), "Факультет")
            await query.edit_message_text(
                f"<b>{name}</b>\n\n📌 Оберіть розділ:",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )

    elif data.startswith("fac_"):
        parts = data.split("_")
        fid = parts[1]
        back = parts[3]
        name = next((full for i, short, full in FACULTIES if i == fid), "Факультет")
        if fid == "bio" and parts[2] == "about":
            await query.edit_message_text(
                "<b>🌿 Біологічний факультет</b>\n\n"
                "🏛 Корпус 3\n"
                "📞 Телефон деканату: <b>061-228-75-78</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/biofacultyznu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/biofacultyznu/\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/biofacultyznu/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/Fs2xAEMXBUA\">Огляд корпусу</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "institute" and parts[2] == "about":
            await query.edit_message_text(
                "<b>⚙️ Інженерний навчально-науковий інститут ім. Ю.М. Потебні ЗНУ</b>\n\n"
                "🏛 Корпус 10 (просп. Соборний, 224)\n"
                "📞 Телефон: <b>061-227-12-52</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/senate_enginerka\">Telegram</a>\n"
                "• <a href=\"https://instagram.com/senate.enginerka\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/IngenerkaZNU/\">Facebook</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "law" and parts[2] == "about":
            await query.edit_message_text(
                "<b>⚖️ Юридичний факультет</b>\n\n"
                "🏛 Корпус 5 (просп. Соборний, 74)\n"
                "📞 Телефон деканату: <b>061-228-76-16</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/p_r_a_v_o\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/sslawznu\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/sslawznu/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/APSe5jPkC7E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "philology" and parts[2] == "about":
            await query.edit_message_text(
                "<b>📖 Філологічний факультет</b>\n\n"
                "🏛 Корпус 2 (вул. Університетська, 66-Б)\n"
                "📞 Телефон деканату: <b>061-289-12-94</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/philologists_znu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/philologists_znu\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/philologistsznu/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/dMr51mmi29E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "fizvosp" and parts[2] == "about":
            await query.edit_message_text(
                "<b>🏃 Факультет фізичного виховання, здоров'я та туризму</b>\n\n"
                "🏛 Корпус 4 (вул. Дніпровська, 33-А)\n"
                "📞 Телефон деканату: <b>061-228-75-54</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/ffvzt_znu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/ffvzt_znu\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/groups/1679075008974997/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/cnuX-_pdgKg\">Відеоекскурсія корпусом</a>\n"
                "🏋️ <a href=\"https://youtu.be/Y8FcyXhQG_8\">Спортивно-оздоровчий комплекс</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "management" and parts[2] == "about":
            await query.edit_message_text(
                "<b>💼 Факультет менеджменту</b>\n\n"
                "🏛 Корпус 6 (вул. Університетська, 55-А)\n"
                "📞 Телефон деканату: <b>061-289-41-10</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/managment_ZNU\">Telegram</a>\n"
                "• <a href=\"https://instagram.com/management.znu\">Instagram</a>\n"
                "• <a href=\"https://m.facebook.com/104631997668199/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/dMr51mmi29E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "fsu" and parts[2] == "about":
            await query.edit_message_text(
                "<b>🏢 Факультет соціології та управління</b>\n\n"
                "🏛 Корпус 6 (вул. Університетська, 55-А)\n"
                "📞 Телефон деканату: <b>061-289-41-04</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/fsu_znu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/fsu_znu/\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/fsu.znu/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/dMr51mmi29E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "spp" and parts[2] == "about":
            await query.edit_message_text(
                "<b>🧠 Факультет соціальної педагогіки та психології</b>\n\n"
                "🏛 Корпус 8 (вул. Гоголя, 118)\n"
                "📞 Телефон деканату: <b>061-228-75-45</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/spp_znu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/znu.spp\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/profile.php?id=100057342643799\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/APSe5jPkC7E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "history" and parts[2] == "about":
            await query.edit_message_text(
                "<b>📜 Факультет історії та міжнародних відносин</b>\n\n"
                "🏛 Корпус 5\n"
                "📞 Телефон деканату: <b>061-228-76-43</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/histfacznu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/histfacznu\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/histfacznu/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/APSe5jPkC7E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "fif" and parts[2] == "about":
            await query.edit_message_text(
                "<b>🌍 Факультет іноземної філології</b>\n\n"
                "🏛 Корпус 2\n"
                "📞 Телефон деканату: <b>061-289-12-09</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/fif_znu\">Telegram</a>\n"
                "• <a href=\"https://www.instagram.com/fif_znu_official/\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/FIF.znu.edu.ua/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/dMr51mmi29E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "journ" and parts[2] == "about":
            await query.edit_message_text(
                "<b>📰 Факультет журналістики</b>\n\n"
                "🏛 Корпус 2\n"
                "📞 Телефон деканату: <b>061-289-41-11</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/fjznu\">Telegram</a>\n"
                "• <a href=\"https://instagram.com/znu_zhurfak\">Instagram</a>\n"
                "• <a href=\"https://m.facebook.com/zhurfak.znu\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/dMr51mmi29E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "math" and parts[2] == "about":
            await query.edit_message_text(
                "<b>📐 Математичний факультет</b>\n\n"
                "🏛 Корпус 1\n"
                "📞 Телефон деканату: <b>061-289-12-60</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/mathfakznu\">Telegram</a>\n"
                "• <a href=\"https://instagram.com/studradamath\">Instagram</a>\n"
                "• <a href=\"https://www.facebook.com/mathznu/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/8afdX9sFx8E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif fid == "econ" and parts[2] == "about":
            await query.edit_message_text(
                "<b>📊 Економічний факультет</b>\n\n"
                "🏛 Корпус 5\n"
                "📞 Телефон деканату: <b>097-391-50-82</b>\n\n"
                "<b>Соцмережі:</b>\n"
                "• <a href=\"https://t.me/ef_tag\">Telegram</a>\n"
                "• <a href=\"https://instagram.com/ef_tag\">Instagram</a>\n"
                "• <a href=\"https://m.facebook.com/308017463378246/\">Facebook</a>\n\n"
                "🎥 <a href=\"https://youtu.be/APSe5jPkC7E\">Відеоекскурсія корпусом</a>",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        elif parts[2] == "spec":
            spec_text = FACULTY_SPECS.get(fid, f"<b>{name}</b>\n\n{SOON}")
            await query.edit_message_text(
                spec_text,
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )
        else:
            await query.edit_message_text(
                f"<b>{name}</b>\n\n{SOON}",
                reply_markup=faculty_menu(fid, back), parse_mode="HTML"
            )

    elif data == "bach_questions":
        await query.edit_message_text(
            "❓ <b>Все про вступ</b>\n\nОберіть тему:",
            reply_markup=bach_questions_menu(), parse_mode="HTML"
        )

    elif data == "other":
        await query.edit_message_text(
            "ℹ️ <b>Інше</b>\n\nОберіть розділ:",
            reply_markup=other_menu(), parse_mode="HTML"
        )

    elif data == "other_activities":
        await query.edit_message_text(
            "🎭 <b>Позанавчальні активності</b>\n\nОберіть розділ:",
            reply_markup=activities_menu(), parse_mode="HTML"
        )

    elif data == "act_studrada":
        await query.edit_message_text(
            "🏛️ <b>Студентська рада ЗНУ</b>\n\n"
            "Студентська рада — це голос студентів університету. Вона захищає права студентів, організовує заходи та допомагає newcomers адаптуватись до університетського життя.\n\n"
            "🔗 <b>Соцмережі:</b>\n"
            "• <a href=\"https://www.instagram.com/studradaznu\">Instagram</a>\n"
            "• <a href=\"https://www.tiktok.com/@studrada_znu\">TikTok</a>\n"
            "• <a href=\"https://t.me/srznu\">Telegram</a>",
            reply_markup=back_menu("other_activities"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "act_creativity":
        await query.edit_message_text(
            "🎨 <b>Центр культури та комунікацій ЗНУ</b>\n\n"
            "Підтримує творчі ініціативи студентів, організовує культурні заходи та розвиває університетську спільноту.\n\n"
            "📍 IV корп., вул. Дніпровська 33-А (к. 111/114б)\n"
            "📧 <a href=\"mailto:culture.znu@gmail.com\">culture.znu@gmail.com</a>\n\n"
            "🔗 <b>Соцмережі:</b>\n"
            "• <a href=\"https://www.instagram.com/culture.znu\">Instagram</a>\n"
            "• <a href=\"https://www.facebook.com/culture.znu\">Facebook</a>\n"
            "• <a href=\"https://www.youtube.com/channel/UCpEQlTANDEEYmteL3WotRdw\">YouTube</a>",
            reply_markup=back_menu("other_activities"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "act_sport":
        await query.edit_message_text(
            "⚽ <b>Спорт у ЗНУ</b>\n\n"
            "В університеті активно розвивається студентський спорт — від секцій до змагань.\n\n"
            "🏋️ <b>Секції:</b>\n"
            "• Атлетична гімнастика\n"
            "• Волейбол\n"
            "• Мініфутбол\n"
            "• Настільний теніс\n\n"
            "🏆 Щороку проводиться <b>університетська спартакіада</b>, а збірні ЗНУ представляють університет на змаганнях різного рівня.",
            reply_markup=back_menu("other_activities"), parse_mode="HTML"
        )

    elif data == "other_studmisto":
        keyboard = [
            [InlineKeyboardButton("🗺️ Карта кампусу", url="https://maps.app.goo.gl/D737mp1sPsNMQA6g6")],
            [InlineKeyboardButton("🎥 Відеоогляд корпусів", url="https://youtube.com/playlist?list=PL-tYqt5WXMgR8sYkANdk_Gn8getqnBCWP")],
            [InlineKeyboardButton("Назад", callback_data="other")],
        ]
        await query.edit_message_text(
            "🏙️ <b>Студентське містечко ЗНУ</b>\n\n"
            "ЗНУ має розгалужений кампус із корпусами в різних частинах міста. "
            "Скористайся картою або перегляньте відеоогляди корпусів:",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML"
        )

    elif data == "other_contacts":
        await query.edit_message_text(
            "📞 <b>Контакти приймальної комісії ЗНУ</b>"
            + CONTACTS,
            reply_markup=back_menu("other"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "other_dorm":
        await query.edit_message_text(
            "🏠 <b>Гуртожиток ЗНУ</b>\n\n"
            "💰 Вартість у 2025 році: <b>8 000 грн/рік</b>\n"
            "📅 Поселення зазвичай відбувається у <b>серпні</b>\n\n"
            "ℹ️ Актуальна інформація на 2026 рік з'явиться у соцмережах ЗНУ пізніше.\n\n"
            "📎 <a href=\"https://sites.znu.edu.ua/liberal_edu/studmisto/156.ukr.html\">Інформація про гуртожитки ЗНУ</a>",
            reply_markup=back_menu("other"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "bq_stages":
        await query.edit_message_text(
            "📅 <b>Етапи вступної кампанії 2026 — Бакалаврат</b>\n\n"
            "🔹 <b>1 липня</b> — реєстрація електронних кабінетів вступників\n\n"
            "🔹 <b>Реєстрація на творчі конкурси та співбесіди:</b>\n"
            "— бюджет: 3–10 липня (до 18:00)\n"
            "— контракт: 3–25 липня (до 18:00)\n\n"
            "🔹 <b>Складання творчих конкурсів та співбесід:</b>\n"
            "— бюджет: 8–19 липня\n"
            "— контракт: 8 липня – 1 серпня\n\n"
            "🔹 <b>Реєстрація заяв на вступ:</b>\n"
            "— основна сесія: 19 липня – 1 серпня (до 18:00)\n\n"
            "🔹 <b>Виконання вимог до зарахування:</b>\n"
            "— бюджет: до 11 серпня (18:00)\n"
            "— контракт: до 19 серпня (17:00)\n\n"
            "🔹 <b>Зарахування:</b>\n"
            "— бюджет: до 11 серпня\n"
            "— контракт: не пізніше 19 серпня\n\n"
            "❗️ Електронні кабінети працюють до 15 жовтня 2026 включно",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_nmt":
        await query.edit_message_text(
            "📝 <b>Коефіцієнти НМТ</b>\n\n"
            "Конкурсний бал розраховується на основі результатів НМТ з 4 предметів, помножених на коефіцієнти, що залежать від спеціальності.\n\n"
            "📊 <b>Формула конкурсного балу:</b>\n"
            "<code>КБ = (П1×К1 + П2×К2 + П3×К3 + П4×К4) × РК × ГК</code>\n\n"
            "Де:\n"
            "• <b>П1–П4</b> — бали з предметів НМТ (100–200)\n"
            "• <b>К1–К4</b> — коефіцієнти для конкретної спеціальності\n"
            "• <b>РК</b> — регіональний коефіцієнт <b>1,07</b> (для всіх вступників до ЗНУ)\n"
            "• <b>ГК</b> — галузевий коефіцієнт (для пріоритетних спеціальностей)\n\n"
            "📚 <b>Приклад розрахунку:</b>\n"
            "Вступ на «Дошкільну освіту» з балами:\n"
            "▫️ Українська мова — 160 × 0,35\n"
            "▫️ Математика — 150 × 0,35\n"
            "▫️ Історія — 170 × 0,4\n"
            "▫️ Біологія — 165 × 0,4\n\n"
            "<i>= 56 + 52,5 + 68 + 66 = 242,5 × 1,07 ≈ 259,5</i>\n\n"
            "🗓 ЗНУ приймає результати НМТ за <b>2023, 2024, 2025 та 2026</b> роки. Коефіцієнти можуть відрізнятись залежно від року.\n\n"
            "📄 <a href=\"https://pk.znu.edu.ua/2026/pp2026/dodatok_7_do_pp_perel__k_predmet__v_nmt.pdf\">Повний перелік коефіцієнтів — Додаток 7</a>",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_motivation":
        await query.edit_message_text(
            "✉️ <b>Мотиваційний лист</b>\n\n"
            "Мотиваційні листи у 2026 році скасовані та більше не є обов'язковим документом для вступу до закладів вищої освіти України.",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_benefits":
        await query.edit_message_text(
            "🛡️ <b>Пільги для мешканців прифронтових громад та ТОТ</b>\n\n"
            "<b>1. ТОТ та активні бойові дії</b>\n"
            "Вступники, зареєстровані на ТОТ або територіях активних бойових дій, вступають за Квотою-2. "
            "Можуть складати усну співбесіду замість НМТ. Виділяється до 40% бюджетних місць.\n\n"
            "<b>2. Території можливих бойових дій</b>\n"
            "Мешканці м. Запоріжжя та відповідних громад мають пріоритетне право на переведення на вакантні бюджетні місця. "
            "Якщо вступили на контракт за НМТ — держава переведе на безкоштовне навчання за наявності місць.\n\n"
            "<b>3. Загальна підтримка (РК)</b>\n"
            "Незалежно від прописки, обравши ЗНУ, ти отримуєш Регіональний коефіцієнт <b>1,07</b>. "
            "Конкурсний бал автоматично помножиться — це забезпечить перевагу у всеукраїнському рейтингу.\n\n"
            "<b>Як підтвердити право на пільгу?</b>\n\n"
            "• <b>Крок 1</b> — Отримай Витяг з реєстру територіальної громади (Додаток 13).\n"
            "• <b>Крок 2</b> — Звернись до Приймальної комісії ЗНУ до моменту подання першої електронної заяви.\n\n"
            "⚠️ <b>Увага!</b> Вступники з ТОТ без українського документа про освіту або паспорта вступають через "
            "Освітній центр «Крим-Україна, Донбас-Україна» при ЗНУ.",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_price":
        await query.edit_message_text(
            "💰 <b>Вартість навчання</b>\n\n"
            "Вартість навчання на 2026 рік ще не визначена.\n\n"
            "📄 <a href=\"https://pk.znu.edu.ua/2025/vartis-2025/pzso_vart__st__.pdf?v=1749198540\">Ознайомитись з вартістю навчання 2025 року</a>\n\n"
            "ℹ️ Актуальна інформація з'явиться на <a href=\"https://pk.znu.edu.ua\">сайті приймальної комісії</a>.",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "bq_creative":
        await query.edit_message_text(
            "🎨 <b>Творчий конкурс</b>\n\n"
            "Творчий конкурс — це додаткове вступне випробування, яке проводиться для вступників на спеціальності, що потребують перевірки творчих або фізичних здібностей. Він враховується при формуванні конкурсного балу.\n\n"
            "<b>Творчі конкурси в ЗНУ проводяться за спеціальностями:</b>\n"
            "— Архітектура та містобудування\n"
            "— Театральне мистецтво\n"
            "— Фізичне виховання\n"
            "— Дизайн\n\n"
            "📅 <b>Дати у 2026 році:</b>\n\n"
            "<b>Реєстрація:</b>\n"
            "— бюджет: 3–10 липня (до 18:00)\n"
            "— контракт: 3–25 липня (до 18:00)\n\n"
            "<b>Складання:</b>\n"
            "— бюджет: 8–19 липня\n"
            "— контракт: до 1 серпня\n\n"
            "🏛 Формат: очний (в межах одного дня)\n\n"
            "❗️ Для спеціальності «Фізична культура і спорт» обов'язкова медична довідка про відсутність протипоказань до фізичних навантажень.\n\n"
            "🗓 <a href=\"https://pk.znu.edu.ua/4496.ukr.html\">Розклад творчих конкурсів</a>\n"
            "📋 <a href=\"https://pk.znu.edu.ua/4500.ukr.html\">Програми творчих конкурсів 2026</a>",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "bq_cabinet":
        await query.edit_message_text(
            "💻 <b>Електронний кабінет вступника</b>\n\n"
            "Електронний кабінет вступника — це персональна онлайн-сторінка абітурієнта на сайті vstup.edbo.gov.ua, яка слугує основним інструментом для:\n"
            "— подачі заяв до закладів вищої освіти\n"
            "— завантаження документів\n"
            "— відстеження результатів конкурсу\n"
            "— прийняття рішення про зарахування\n\n"
            "📅 Реєстрація кабінетів стартує <b>1 липня</b>.\n\n"
            "🔗 <a href=\"https://vstup.edbo.gov.ua\">Перейти до кабінету вступника</a>",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML", disable_web_page_preview=True
        )

    elif data == "bq_noexam":
        await query.edit_message_text(
            "🎓 <b>Гранти на навчання</b>\n\n"
            "Держава компенсує частину вартості навчання вступникам з високими балами НМТ!\n\n"
            "🟢 <b>140 балів з 2-х предметів</b> → Грант <b>17 000 грн/рік</b>\n"
            "Для спеціальностей державної підтримки.\n\n"
            "🟢 <b>150 балів з 2-х предметів</b> → Грант <b>17 000 грн/рік</b>\n"
            "Для будь-яких спеціальностей.\n\n"
            "🟡 <b>170 балів з 2-х предметів</b> → Грант <b>28 000 грн/рік</b>\n"
            "Для будь-яких спеціальностей. Максимальний рівень фінансування.\n\n"
            "ℹ️ Грант нараховується автоматично при зарахуванні на контракт за наявності відповідних балів НМТ.",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_docs":
        await query.edit_message_text(
            "📄 <b>Документи для вступу — Бакалаврат</b>\n\n"
            "<b>Основні документи:</b>\n\n"
            "<b>1. Паспорт та витяг з реєстру територіальної громади</b>\n"
            "Копія документа, що посвідчує особу (паспорт-книжечка з відміткою про реєстрацію або паспорт у формі ID-картки) та витяг з реєстру територіальної громади.\n\n"
            "<b>2. Індивідуальний податковий номер (ІПН)</b>\n"
            "Копія документа про присвоєння ідентифікаційного номера фізичної особи.\n\n"
            "<b>3. Документи про освіту</b>\n"
            "Копія документа про освіту, на основі якого відбувається вступ, та додатка до нього.\n\n"
            "<b>4. Фотокартки</b>\n"
            "4 кольорові фото розміром 3х4 см.\n\n"
            "<b>5. Сертифікат та результати НМТ</b>\n"
            "Результати 2026/2025/2024/2023 років, сформовані в особистому кабінеті учасника НМТ.\n\n"
            "<b>6. Військово-обліковий документ</b>\n"
            "Копія одного з документів:\n"
            "— Посвідчення про приписку\n"
            "— Військовий квиток\n"
            "— Тимчасове посвідчення військовозобов'язаного\n"
            "— Електронний документ (з Резерв+) у роздрукованому вигляді\n\n"
            "⚠️ <i>Особи віком 25 років і старші приписку надавати не можуть!</i>\n\n"
            "——————————————\n"
            "<b>Додаткові документи (за потреби):</b>\n\n"
            "📌 <b>Для діючих військовослужбовців</b>\n"
            "Підтвердження проходження військової служби та дозвіл військового командування на навчання без відриву від служби.\n\n"
            "📌 <b>Пільгові категорії</b>\n"
            "Юридичний висновок для вступників, які мають право на спеціальні умови вступу.\n\n"
            "📌 <b>Спеціальність «Фізична культура і спорт»</b>\n"
            "Обов'язкова медична довідка № 086/о про відсутність протипоказань до фізичних навантажень.\n\n"
            "❗️ <i>У разі розбіжності прізвища, імені або по батькові в документах — надати свідоцтво про шлюб, зміну імені тощо.</i>\n\n"
            "🚫 <b>Скріншоти з застосунку «Дія» не приймаються!</b>",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_regional":
        await query.edit_message_text(
            "🏛 <b>Регіональний коефіцієнт</b>\n\n"
            "Регіональний коефіцієнт (РК) — це множник конкурсного балу, який залежить від <b>місцезнаходження закладу освіти</b>.\n\n"
            "Його мета — підтримка рівномірного розвитку вишів у регіонах.\n\n"
            "📌 <b>Для ЗНУ:</b>\n\n"
            "Регіональний коефіцієнт = <b>1,07</b>\n\n"
            "Це може додати до <b>10 балів</b> до конкурсного балу.\n\n"
            "📚 <b>Як це працює?</b>\n\n"
            "Конкурсний бал автоматично множиться на 1,07 при поданні заяви до ЗНУ.\n\n"
            "<i>Приклад:</i>\n"
            "Вступник з конкурсним балом 150 × 1,07 = <b>160,5 балу</b>\n\n"
            "❗️ Коефіцієнт враховується <b>автоматично</b> при поданні заяви. Жодних додаткових дій не потрібно.",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data.startswith("bq_"):
        await query.edit_message_text(SOON, reply_markup=back_menu("bach_questions"), parse_mode="HTML")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Немає доступу.")
        return
    users = load_users()
    button_stats = load_button_stats()
    text = f"📊 <b>Статистика</b>\n\n👥 Користувачів: <b>{len(users)}</b>\n"
    if button_stats:
        sorted_buttons = sorted(button_stats.items(), key=lambda x: x[1], reverse=True)
        total_clicks = sum(button_stats.values())
        lines = "\n".join(f"  <code>{k}</code> — {v}" for k, v in sorted_buttons)
        text += f"\n🔘 <b>Кнопки</b> (всього натискань: {total_clicks}):\n{lines}"
    else:
        text += "\n🔘 Кнопок ще не натискали."
    await update.message.reply_text(text, parse_mode="HTML")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("Використання: /reply <chat_id> <текст відповіді>")
        return
    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Невірний chat_id.")
        return
    text = update.message.text.partition(context.args[0])[2].strip()
    await context.bot.send_message(
        chat_id=target_id,
        text=f"💬 <b>Відповідь приймальної комісії:</b>\n\n{text}",
        parse_mode="HTML"
    )
    await update.message.reply_text("✅ Відповідь надіслано.")

async def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не встановлено!")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("reply", reply))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Бот запущено!")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
