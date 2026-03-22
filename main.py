import os
import asyncio
import logging
from flask import Flask, request
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================
# Налаштування
# =========================
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HEIGHT, WEIGHT = range(2)

CONTACT_URL = (
    "https://t.me/Zelenina_Oksana"
    "?text=Хочу%20на%20курс%20%D0%A3%D1%81%D0%B2%D1%96%D0%B4%D0%BE%D0%BC%D0%BB%D0%B5%D0%BD%D0%B5%20%D1%85%D0%B0%D1%80%D1%87%D1%83%D0%B2%D0%B0%D0%BD%D0%BD%D1%8F"
)

web_app = Flask(__name__)
telegram_app = None


# =========================
# Клавіатури
# =========================
def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["▶️ Старт"],
        ["📘 Детальніше про курс"],
        ["👤 Для кого курс"],
        ["📝 Як записатися"],
        ["🔄 Перерахувати ІМТ"],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def contact_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✍️ Написати в особисті повідомлення", url=CONTACT_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================
# Допоміжні функції
# =========================
def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Недостатня маса тіла"
    elif bmi < 25:
        return "Норма"
    elif bmi < 30:
        return "Надлишкова вага"
    return "Ожиріння"


def bmi_explanation(bmi: float) -> str:
    if bmi < 18.5:
        return (
            "Твоє тіло може бути в дефіциті ресурсів.\n"
            "У такій ситуації важливо не просто їсти більше, "
            "а вибудувати спокійні й зрозумілі відносини з їжею."
        )
    elif bmi < 25:
        return (
            "У тебе хороша база 👍\n"
            "Але навіть при нормальному ІМТ можуть бути труднощі:\n"
            "— переїдання\n"
            "— тяга до солодкого\n"
            "— тривога навколо їжі\n"
            "— коливання ваги"
        )
    elif bmi < 30:
        return (
            "Тіло вже накопичує зайву вагу, і худнути може бути складніше.\n"
            "Але тут важливі не жорсткі дієти, а система, яку реально втримати."
        )
    else:
        return (
            "Є додаткове навантаження на організм.\n"
            "У такій ситуації особливо важливо діяти м’яко, послідовно і без крайнощів."
        )


def normalize_number(text: str) -> str:
    return text.strip().replace(",", ".")


def is_menu_text(text: str) -> bool:
    menu_items = {
        "▶️ Старт",
        "📘 Детальніше про курс",
        "👤 Для кого курс",
        "📝 Як записатися",
        "🔄 Перерахувати ІМТ",
    }
    return text.strip() in menu_items


# =========================
# Текстові блоки
# =========================
COURSE_DETAILS_TEXT = (
    "📘 Курс «Усвідомлене харчування» — це не дієта і не марафон.\n\n"
    "На курсі ми працюємо над тим, щоб:\n"
    "— прибрати хаос у харчуванні\n"
    "— зменшити тягу до переїдання\n"
    "— перестати ділити їжу на «добру» і «погану»\n"
    "— вибудувати спокійну систему, яку можна втримати в реальному житті\n\n"
    "На курсі вас чекає:\n"
    "— 6 тижнів навчання\n"
    "— моя підтримка протягом усього курсу\n"
    "— розбір тарілок з нутріціологом\n"
    "— тренування від професійної тренерки Тетяни Баранової\n\n"
    "Це підхід без жорстких обмежень, без постійного почуття провини і без зривів."
)

FOR_WHOM_TEXT = (
    "👤 Курс підійде тобі, якщо ти:\n\n"
    "— постійно починаєш «нове життя» з понеділка\n"
    "— зриваєшся після обмежень\n"
    "— втомилась від дієт і контролю\n"
    "— хочеш нормальні, спокійні відносини з їжею\n"
    "— хочеш змінювати харчування без стресу\n\n"
    "Це не про ідеальність.\n"
    "Це про систему, яка працює довго."
)

SIGNUP_TEXT = (
    "Щоб записатися на курс «Усвідомлене харчування» 👇\n\n"
    "Натисни кнопку нижче і напиши мені в Telegram 💛"
)


# =========================
# Команди та меню
# =========================
async def send_course_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        COURSE_DETAILS_TEXT,
        reply_markup=main_keyboard(),
    )


async def send_for_whom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        FOR_WHOM_TEXT,
        reply_markup=main_keyboard(),
    )


async def send_signup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        SIGNUP_TEXT,
        reply_markup=contact_inline_keyboard(),
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Привіт 👋\n\n"
        "Я допоможу розрахувати індекс маси тіла (ІМТ) "
        "і покажу, куди рухатись далі.\n\n"
        "Введи свій зріст у сантиметрах.\n"
        "Наприклад: 165",
        reply_markup=main_keyboard(),
    )
    return HEIGHT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Окей, повертаємось у меню 👇",
        reply_markup=main_keyboard(),
    )
    return ConversationHandler.END


# =========================
# Обробка меню в будь-якому стані
# =========================
async def handle_menu_in_conversation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    current_state: int,
):
    text = update.message.text.strip()

    if text == "▶️ Старт" or text == "🔄 Перерахувати ІМТ":
        return await start(update, context)

    if text == "📘 Детальніше про курс":
        await send_course_details(update, context)
        return current_state

    if text == "👤 Для кого курс":
        await send_for_whom(update, context)
        return current_state

    if text == "📝 Як записатися":
        await send_signup(update, context)
        return current_state

    return None


# =========================
# Крок 1: зріст
# =========================
async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    menu_result = await handle_menu_in_conversation(update, context, HEIGHT)
    if menu_result is not None:
        return menu_result

    try:
        height = float(normalize_number(text))
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введи зріст числом.\n"
            "Наприклад: 165",
            reply_markup=main_keyboard(),
        )
        return HEIGHT

    if height < 100 or height > 250:
        await update.message.reply_text(
            "Введи реальний зріст у сантиметрах.\n"
            "Наприклад: 165",
            reply_markup=main_keyboard(),
        )
        return HEIGHT

    context.user_data["height"] = height

    await update.message.reply_text(
        f"Зріст зафіксовано: {height:.1f} см\n\n"
        "Тепер введи свою вагу в кілограмах.\n"
        "Наприклад: 70",
        reply_markup=main_keyboard(),
    )
    return WEIGHT


# =========================
# Крок 2: вага
# =========================
async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    menu_result = await handle_menu_in_conversation(update, context, WEIGHT)
    if menu_result is not None:
        return menu_result

    try:
        weight = float(normalize_number(text))
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введи вагу числом.\n"
            "Наприклад: 70",
            reply_markup=main_keyboard(),
        )
        return WEIGHT

    if weight < 20 or weight > 300:
        await update.message.reply_text(
            "Введи реальну вагу в кілограмах.\n"
            "Наприклад: 70",
            reply_markup=main_keyboard(),
        )
        return WEIGHT

    height_cm = context.user_data.get("height")
    if not height_cm:
        await update.message.reply_text(
            "Сталася помилка в розрахунку. Натисни «▶️ Старт» і почнемо заново.",
            reply_markup=main_keyboard(),
        )
        return ConversationHandler.END

    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)
    category = bmi_category(bmi)
    explanation = bmi_explanation(bmi)

    result_text = (
        "📊 Твій результат:\n\n"
        f"Зріст: {height_cm:.1f} см\n"
        f"Вага: {weight:.1f} кг\n\n"
        f"👉 ІМТ: {bmi:.1f}\n"
        f"👉 Категорія: {category}\n\n"
        "💡 Що це означає:\n"
        f"{explanation}\n\n"
        "Важливо:\n"
        "ІМТ — це лише базовий орієнтир.\n"
        "Реальна проблема часто не в цифрі на вагах, а у відносинах з їжею:\n"
        "— зриви\n"
        "— заборони\n"
        "— постійний контроль\n"
        "— почуття провини після їжі\n\n"
        "Саме тому я створила курс «Усвідомлене харчування» 💛\n\n"
        "Це курс для тих, хто хоче:\n"
        "✔ перестати жити в режимі «схуднення з понеділка»\n"
        "✔ вийти із замкненого кола зривів і заборон\n"
        "✔ навчитися їсти спокійно, без страху і крайнощів"
    )

    context.user_data.clear()

    await update.message.reply_text(
        result_text,
        reply_markup=main_keyboard(),
    )

    await update.message.reply_text(
        "Обери, що тобі цікаво далі 👇",
        reply_markup=main_keyboard(),
    )

    return ConversationHandler.END


# =========================
# Обробка меню поза діалогом
# =========================
async def menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await start(update, context)


async def fallback_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "📘 Детальніше про курс":
        await send_course_details(update, context)
        return

    if text == "👤 Для кого курс":
        await send_for_whom(update, context)
        return

    if text == "📝 Як записатися":
        await send_signup(update, context)
        return

    if text == "▶️ Старт" or text == "🔄 Перерахувати ІМТ":
        await start(update, context)
        return

    await update.message.reply_text(
        "Обери потрібний пункт меню 👇",
        reply_markup=main_keyboard(),
    )


# =========================
# Flask routes
# =========================
@web_app.route("/", methods=["GET"])
def home():
    return "Бот працює!", 200


@web_app.route("/webhook", methods=["POST"])
def webhook():
    global telegram_app

    if telegram_app is None:
        logger.error("telegram_app is not initialized")
        return "Telegram app not initialized", 500

    try:
        data = request.get_json(force=True)

        async def process():
            update = Update.de_json(data, telegram_app.bot)
            await telegram_app.process_update(update)

        asyncio.run(process())
        return "ok", 200

    except Exception as e:
        logger.exception("Помилка у webhook: %s", e)
        return f"Webhook error: {e}", 500


# =========================
# Ініціалізація Telegram
# =========================
async def setup_telegram():
    global telegram_app

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Не знайдено TELEGRAM_BOT_TOKEN у змінних середовища.")

    telegram_app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^▶️ Старт$"), start),
            MessageHandler(filters.Regex("^🔄 Перерахувати ІМТ$"), start),
        ],
        states={
            HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_height),
            ],
            WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True,
    )

    telegram_app.add_handler(conv_handler)

    telegram_app.add_handler(
        MessageHandler(filters.Regex("^📘 Детальніше про курс$"), send_course_details)
    )
    telegram_app.add_handler(
        MessageHandler(filters.Regex("^👤 Для кого курс$"), send_for_whom)
    )
    telegram_app.add_handler(
        MessageHandler(filters.Regex("^📝 Як записатися$"), send_signup)
    )
    telegram_app.add_handler(
        MessageHandler(filters.Regex("^▶️ Старт$"), menu_start)
    )
    telegram_app.add_handler(
        MessageHandler(filters.Regex("^🔄 Перерахувати ІМТ$"), menu_start)
    )
    telegram_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_menu)
    )

    await telegram_app.initialize()
    await telegram_app.start()
    logger.info("Telegram app initialized successfully")


# =========================
# Запуск
# =========================
if __name__ == "__main__":
    asyncio.run(setup_telegram())

    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
