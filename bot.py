import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))
USERS_FILE = "users.txt"
BUTTON_STATS_FILE = "button_stats.json"

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

def save_user(chat_id: int):
    ids = load_users()
    if chat_id not in ids:
        with open(USERS_FILE, "a") as f:
            f.write(str(chat_id) + "\n")

def load_users() -> list[int]:
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE) as f:
        return [int(line.strip()) for line in f if line.strip()]

SOON = "ℹ️ Інформація з'явиться незабаром. Слідкуй за оновленнями на <a href=\"https://pk.znu.edu.ua\">pk.znu.edu.ua</a>"
CONTACTS = (
    "\n\n📍 <b>Приймальна комісія</b>\nвул. Університетська 66-Б (каб. 115)"
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

FACULTY_SPECS = {
    "bio": (
        "🎓 <b>Біологічний факультет</b>\n\n"
        "▫️ Біологія — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Екологія — денна (є бюджет)\n"
        "▫️ Хімія — денна (є бюджет)\n"
        "▫️ Мисливське господарство та рослинні ресурси — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Середня освіта (Біологія та здоров'я людини) — денна (є бюджет)"
    ),
    "econ": (
        "🎓 <b>Економічний факультет</b>\n\n"
        "▫️ Економічна кібернетика та аналітика даних — денна (є бюджет)\n"
        "▫️ Міжнародна економіка — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Фінанси і кредит — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Облік, оподаткування та аудит — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Маркетинг — денна (є бюджет), заочна (тільки контракт)"
    ),
    "history": (
        "🎓 <b>Факультет історії та міжнародних відносин</b>\n\n"
        "▫️ Історія — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Міжнародні відносини — денна (є бюджет)\n"
        "▫️ Середня освіта (Історія та громадянська освіта) — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Середня освіта (Географія) — денна (є бюджет), заочна (є бюджет)"
    ),
    "math": (
        "🎓 <b>Математичний факультет</b>\n\n"
        "▫️ Математика — денна (є бюджет)\n"
        "▫️ Прикладна фізика — денна (є бюджет)\n"
        "▫️ Комп'ютерне моделювання — денна (є бюджет)\n"
        "▫️ Програмна інженерія — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Комп'ютерні науки — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Кібербезпека та захист інформації — денна (є бюджет)\n"
        "▫️ Середня освіта (Математика) — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Середня освіта (Фізика та астрономія) — денна (є бюджет)\n"
        "▫️ Середня освіта (Інформатика) — денна (є бюджет)"
    ),
    "journ": (
        "🎓 <b>Факультет журналістики</b>\n\n"
        "▫️ Журналістика — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Редагування та моделювання медійного контенту — денна (є бюджет)\n"
        "▫️ Реклама і зв'язки з громадськістю — денна (є бюджет)"
    ),
    "fif": (
        "🎓 <b>Факультет іноземної філології</b>\n\n"
        "▫️ Середня освіта (Мова і література (англійська)) — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Мова і література (англійська) — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Переклад (англійський) — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Німецька мова і література, англійська мова — денна (є бюджет)\n"
        "▫️ Іспанська мова і література, англійська мова — денна (є бюджет)\n"
        "▫️ Французька мова і література, англійська мова — денна (є бюджет)"
    ),
    "management": (
        "🎓 <b>Факультет менеджменту</b>\n\n"
        "▫️ Менеджмент міжнародного бізнесу — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Менеджмент організацій — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Торгівля та комерційна логістика — денна (є бюджет)\n"
        "▫️ Економіка та управління бізнесом — денна (тільки контракт), заочна (тільки контракт)"
    ),
    "spp": (
        "🎓 <b>Факультет соціальної педагогіки та психології</b>\n\n"
        "▫️ Дошкільна освіта — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Початкова освіта — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Логопедія — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Графічний дизайн — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Театральне мистецтво — денна (є бюджет)\n"
        "▫️ Психологія — денна (є бюджет), заочна (тільки контракт)"
    ),
    "fsu": (
        "🎓 <b>Факультет соціології та управління</b>\n\n"
        "▫️ Соціологія — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Соціологія медіації і кримінології — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Політологія — денна (є бюджет)\n"
        "▫️ Публічне управління та адміністрування — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Європейські філософські студії і креативні індустрії — денна (є бюджет)\n"
        "▫️ Соціальна робота — денна (є бюджет), заочна (тільки контракт)"
    ),
    "philology": (
        "🎓 <b>Філологічний факультет</b>\n\n"
        "▫️ Українська мова та література — денна (є бюджет)\n"
        "▫️ Польська мова і література, англійська мова — денна (є бюджет)\n"
        "▫️ Прикладна лінгвістика — денна (є бюджет)\n"
        "▫️ Середня освіта (Українська мова і література) — денна (є бюджет), заочна (є бюджет)"
    ),
    "fizvosp": (
        "🎓 <b>Факультет фізичного виховання, здоров'я та туризму</b>\n\n"
        "▫️ Спорт — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Фізичне виховання — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Фізична терапія, ерготерапія — денна (є бюджет)\n"
        "▫️ Готельно-ресторанна справа — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Туризм — денна (є бюджет)\n"
        "▫️ Охорона праці — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Середня освіта (Фізична культура) — денна (є бюджет)"
    ),
    "law": (
        "🎓 <b>Юридичний факультет</b>\n\n"
        "▫️ Право — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Правоохоронна діяльність — денна (тільки контракт), заочна (тільки контракт)"
    ),
    "institute": (
        "🎓 <b>Інженерний навчально-науковий інститут ім. Ю.М. Потебні</b>\n\n"
        "▫️ Архітектура та містобудування — денна (є бюджет)\n"
        "▫️ Промислове і цивільне будівництво — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Міське будівництво та господарство — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Металургія — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Машини та агрегати металургійного виробництва — денна (є бюджет)\n"
        "▫️ Автоматизація, комп'ютерно-інтегровані технології та робототехніка — денна (є бюджет)\n"
        "▫️ Електроенергетика, електротехніка та електромеханіка — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Теплоенергетика — денна (є бюджет)\n"
        "▫️ Відновлювані джерела енергії та гідроенергетика — денна (є бюджет)\n"
        "▫️ Мікро- та наносистемна техніка — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Технології захисту навколишнього середовища — денна (є бюджет)\n"
        "▫️ Програмне забезпечення систем — денна (є бюджет), заочна (є бюджет)\n"
        "▫️ Інформаційна економіка — денна (є бюджет)\n"
        "▫️ Публічне управління та адміністрування — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Облік і аудит — денна (є бюджет), заочна (тільки контракт)\n"
        "▫️ Фінанси держави та підприємницьких структур — денна (є бюджет), заочна (тільки контракт)"
    ),
    "liberalarts": (
        "🌀 <b>Liberal Arts and Science</b>\n\n"
        "▫️ Liberal Arts and Science — денна (тільки контракт)"
    ),
}

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🎓 Вступ на 1 курс", callback_data="bachelor")],
        [InlineKeyboardButton("📚 Магістратура", callback_data="master")],
        [InlineKeyboardButton("ℹ️ Інше", callback_data="other")],
    ]
    return InlineKeyboardMarkup(keyboard)

def other_menu():
    keyboard = [
        [InlineKeyboardButton("🏠 Гуртожиток", callback_data="other_dorm")],
        [InlineKeyboardButton("🏙️ Студентське містечко", callback_data="other_studmisto")],
        [InlineKeyboardButton("🎭 Позанавчальні активності", callback_data="other_activities")],
        [InlineKeyboardButton("📞 Контакти", callback_data="other_contacts")],
        [InlineKeyboardButton("Назад", callback_data="start")],
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
        [InlineKeyboardButton("Спеціальності ЗНУ", callback_data="spec_bachelor")],
        [InlineKeyboardButton("Питання вступу", callback_data="bach_questions")],
        [InlineKeyboardButton("Назад", callback_data="start")],
    ]
    return InlineKeyboardMarkup(keyboard)

def master_menu():
    keyboard = [
        [InlineKeyboardButton("Спеціальності ЗНУ", callback_data="spec_master")],
        [InlineKeyboardButton("Питання вступу", callback_data="master_questions")],
        [InlineKeyboardButton("Назад", callback_data="start")],
    ]
    return InlineKeyboardMarkup(keyboard)

def bach_questions_menu():
    keyboard = [
        [InlineKeyboardButton("Етапи вступної кампанії", callback_data="bq_stages")],
        [InlineKeyboardButton("Кабінет вступника", callback_data="bq_cabinet")],
        [InlineKeyboardButton("НМТ", callback_data="bq_nmt")],
        [InlineKeyboardButton("Мотиваційний лист", callback_data="bq_motivation")],
        [InlineKeyboardButton("Творчий конкурс", callback_data="bq_creative")],
        [InlineKeyboardButton("Гранти на навчання", callback_data="bq_noexam")],
        [InlineKeyboardButton("Вартість навчання", callback_data="bq_price")],
        [InlineKeyboardButton("Пільгові категорії", callback_data="bq_benefits")],
        [InlineKeyboardButton("Назад", callback_data="bachelor")],
    ]
    return InlineKeyboardMarkup(keyboard)

def master_questions_menu():
    keyboard = [
        [InlineKeyboardButton("Етапи вступної кампанії", callback_data="mq_stages")],
        [InlineKeyboardButton("Кабінет вступника", callback_data="mq_cabinet")],
        [InlineKeyboardButton("ЄВІ", callback_data="mq_evi")],
        [InlineKeyboardButton("ЄФФВ", callback_data="mq_effv")],
        [InlineKeyboardButton("Мотиваційний лист", callback_data="mq_motivation")],
        [InlineKeyboardButton("Творчий конкурс", callback_data="mq_creative")],
        [InlineKeyboardButton("Пільгові категорії", callback_data="mq_benefits")],
        [InlineKeyboardButton("Вартість навчання", callback_data="mq_price")],
        [InlineKeyboardButton("Вступ без іспитів", callback_data="mq_noexam")],
        [InlineKeyboardButton("Назад", callback_data="master")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_menu(destination):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data=destination)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Вітаю! Я бот для вступників ЗНУ.\n\n"
        "Тут ти знайдеш:\n"
        "- інформацію про вступ на бакалаврат і магістратуру\n"
        "- спеціальності та контакти факультетів\n"
        "- корисне про студентське життя в ЗНУ\n\n"
        "Обери розділ:"
    )
    if update.message:
        save_user(update.message.chat_id)
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="HTML")
    else:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="HTML", disable_web_page_preview=True)

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

    if data == "start":
        await query.edit_message_text(
            "👋 Вітаю! Я бот для вступників ЗНУ.\n\n"
            "Тут ти знайдеш:\n"
            "- інформацію про вступ на бакалаврат і магістратуру\n"
            "- спеціальності та контакти факультетів\n"
            "- корисне про студентське життя в ЗНУ\n\n"
            "Обери розділ:",
            reply_markup=main_menu(), parse_mode="HTML"
        )

    elif data == "bachelor":
        await query.edit_message_text(
            "🎓 <b>Бакалаврат</b>\n\nОберіть розділ:",
            reply_markup=bachelor_menu(), parse_mode="HTML"
        )

    elif data == "master":
        await query.edit_message_text(
            "📚 <b>Магістратура</b>\n\nОберіть розділ:",
            reply_markup=master_menu(), parse_mode="HTML"
        )

    elif data == "spec_bachelor":
        await query.edit_message_text(
            "📋 <b>Спеціальності ЗНУ — Бакалаврат</b>\n\nОберіть факультет:",
            reply_markup=faculties_menu("bachelor"), parse_mode="HTML"
        )

    elif data == "spec_master":
        await query.edit_message_text(
            "📋 <b>Спеціальності ЗНУ — Магістратура</b>\n\nОберіть факультет:",
            reply_markup=faculties_menu("master"), parse_mode="HTML"
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
            "❓ <b>Питання вступу — Бакалаврат</b>\n\nОберіть тему:",
            reply_markup=bach_questions_menu(), parse_mode="HTML"
        )

    elif data == "master_questions":
        await query.edit_message_text(
            "❓ <b>Питання вступу — Магістратура</b>\n\nОберіть тему:",
            reply_markup=master_questions_menu(), parse_mode="HTML"
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
            reply_markup=back_menu("other"), parse_mode="HTML"
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
            "📝 <b>НМТ — Національний мультипредметний тест</b>\n\n"
            "<b>Основна сесія:</b>\n"
            "• Реєстрація: 5.03 – 2.04\n"
            "• Зміна даних: до 7.04 (за потреби)\n"
            "• Тестування: 20.05 – 25.06\n"
            "• Результати: до 03.07\n\n"
            "<b>Додаткова сесія:</b>\n"
            "• Реєстрація: 11–16.05\n"
            "• Зміна даних: до 21.05 (за потреби)\n"
            "• Тестування: 17–24.07\n"
            "• Результати: до 29.07\n\n"
            "<b>Обов'язкові предмети:</b>\n"
            "• Українська мова\n"
            "• Математика\n"
            "• Історія України\n\n"
            "<b>Предмет на вибір (один з):</b>\n"
            "• Українська література\n"
            "• Іноземна мова (англійська, німецька, французька, іспанська)\n"
            "• Біологія\n"
            "• Фізика\n"
            "• Хімія\n"
            "• Географія",
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

    elif data == "mq_motivation":
        await query.edit_message_text(
            "✉️ <b>Мотиваційний лист</b>\n\n"
            "Мотиваційні листи у 2026 році скасовані та більше не є обов'язковим документом для вступу до закладів вищої освіти України.",
            reply_markup=back_menu("master_questions"), parse_mode="HTML"
        )

    elif data == "bq_price":
        await query.edit_message_text(
            "💰 <b>Вартість навчання</b>\n\n"
            "Вартість навчання на 2026 рік ще не визначена.\n\n"
            "📄 <a href=\"https://pk.znu.edu.ua/2025/vartis-2025/pzso_vart__st__.pdf?v=1749198540\">Ознайомитись з вартістю навчання 2025 року</a>\n\n"
            "ℹ️ Актуальна інформація з'явиться на <a href=\"https://pk.znu.edu.ua\">сайті приймальної комісії</a>.",
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
        )

    elif data == "bq_creative":
        await query.edit_message_text(
            "🎨 <b>Творчий конкурс</b>\n\n"
            "Творчий конкурс — це додаткове вступне випробування, яке проводиться для вступників на спеціальності, що потребують перевірки творчих або фізичних здібностей. Він враховується при формуванні конкурсного балу.\n\n"
            "Творчі конкурси в ЗНУ проводяться за напрямами:\n"
            "— Архітектура та містобудування\n"
            "— Сценічне мистецтво\n"
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
            "📋 <a href=\"https://pk.znu.edu.ua/4500.ukr.html\">Програми творчих конкурсів 2025</a>",
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
            reply_markup=back_menu("bach_questions"), parse_mode="HTML"
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

    elif data.startswith("bq_"):
        await query.edit_message_text(SOON, reply_markup=back_menu("bach_questions"), parse_mode="HTML")

    elif data == "mq_evi":
        await query.edit_message_text(
            "📜 <b>ЄВІ — Єдиний вступний іспит</b>\n\n"
            "Для вступу на магістратуру необхідно скласти ЄВІ, який складається з двох частин:\n"
            "🧠 <b>ТЗНК</b> — тест загальної навчальної компетентності (~75 хвилин, 33 бали)\n"
            "🌍 <b>Іноземна мова</b> (~45 хвилин, 30 балів)\n\n"
            "<b>Структура ТЗНК (33 завдання):</b>\n"
            "— 10 завдань: заповнення пропусків у мікротекстах\n"
            "— 23 завдання: вибір однієї відповіді\n\n"
            "<b>Структура іноземної мови (30 завдань):</b>\n"
            "— 5 завдань: вибір однієї відповіді\n"
            "— 3 завдання: логічні пари\n"
            "— 19 завдань: заповнення пропусків у тексті\n\n"
            "📅 <b>Ключові дати ЄВІ 2026:</b>\n\n"
            "<b>Основна сесія:</b>\n"
            "• Реєстрація: 23 квітня – 14 травня\n"
            "• Тестування: 26 червня – 14 липня\n"
            "• Результати: до 23 липня\n\n"
            "<b>Додаткова сесія:</b>\n"
            "• Реєстрація: 26 – 28 травня\n"
            "• Тестування: 3 – 21 серпня\n"
            "• Результати: до 21 серпня\n\n"
            "📋 <b>Як зареєструватися:</b>\n"
            "1. Підготувати документи: паспорт/ID, диплом або довідку, РНОКПП, фотокартку, документи для спецумов (за потреби), заповнену заяву-анкету\n"
            "2. Подати документи до приймальної комісії (особисто або дистанційно)\n"
            "3. Отримати екзаменаційний лист на email\n"
            "4. Перевірити кабінет учасника на сайті УЦОЯО\n\n"
            "ℹ️ Реєстрація на ЄВІ триває з <b>23 квітня</b> до <b>14 травня</b>. Уся актуальна інформація на "
            "<a href=\"https://pk.znu.edu.ua/4535.ukr.html\">сайті приймальної комісії ЗНУ</a>.",
            reply_markup=back_menu("master_questions"), parse_mode="HTML"
        )

    elif data == "mq_effv":
        await query.edit_message_text(
            "📜 <b>ЄФВВ — Єдине фахове вступне випробування</b>\n\n"
            "ЄФВВ — це предметний тест, який складають вступники на магістратуру замість або додатково до ЄВІ, залежно від спеціальності.\n\n"
            "📚 <b>Предметні тести за спеціальностями ЗНУ:</b>\n"
            "— Історія мистецтва → Історія та археологія, Графічний дизайн, Перформативні мистецтва\n"
            "— Мовознавство → Філологія\n"
            "— Економіка та міжнародна економіка → Економіка та міжнародні економічні відносини\n"
            "— Політологія та міжнародні відносини → Політологія, Міжнародні відносини\n"
            "— Психологія та соціологія → Психологія, Соціологія\n"
            "— Педагогіка та психологія → Психологія\n"
            "— Облік та фінанси → Облік і оподаткування, Фінанси та банківська справа\n"
            "— Управління та адміністрування → Менеджмент, Маркетинг, Торгівля\n"
            "— Право та міжнародне право → Право\n"
            "— Інформаційні технології → Прикладна математика, Інженерія ПЗ, Комп'ютерні науки\n\n"
            "🎯 <a href=\"https://zno.osvita.ua/master/\">Попрактикуватись онлайн (тести попередніх років)</a>\n\n"
            "ℹ️ Детальна інформація на <a href=\"https://pk.znu.edu.ua/4537.ukr.html\">сайті приймальної комісії ЗНУ</a>.",
            reply_markup=back_menu("master_questions"), parse_mode="HTML"
        )

    elif data == "mq_stages":
        await query.edit_message_text(
            "📅 <b>Етапи вступної кампанії 2026 — Магістратура</b>\n\n"
            "🔹 <b>1 липня</b> — реєстрація електронних кабінетів вступників\n\n"
            "🔹 <b>Реєстрація заяв на вступні випробування у ЗНУ</b> (співбесіда з іноземної мови замість ЄВІ, фаховий іспит):\n"
            "— бюджет: 1–27 липня (до 18:00)\n"
            "— контракт: 1 липня – 17 серпня (до 18:00)\n\n"
            "🔹 <b>Складання вступних випробувань:</b>\n"
            "— бюджет: 28 липня – 7 серпня\n"
            "— контракт: 28 липня – 20 серпня\n\n"
            "🔹 <b>Реєстрація заяв на вступ:</b>\n"
            "— основна сесія: 7–22 серпня (до 18:00)\n\n"
            "🔹 <b>Виконання вимог до зарахування:</b>\n"
            "— бюджет: до 28 серпня (18:00)\n"
            "— контракт: до 3 вересня (17:00)\n\n"
            "🔹 <b>Зарахування:</b>\n"
            "— бюджет: 29 серпня\n"
            "— контракт: не пізніше 7 вересня\n\n"
            "❗️ Електронні кабінети працюють до 15 жовтня 2026 включно",
            reply_markup=back_menu("master_questions"), parse_mode="HTML"
        )

    elif data.startswith("mq_"):
        await query.edit_message_text(SOON, reply_markup=back_menu("master_questions"), parse_mode="HTML")

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
