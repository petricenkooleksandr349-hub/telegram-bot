import os
import asyncio
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
# Flask для Render + webhook
# =========================
web_app = Flask(__name__)

telegram_app: Application | None = None

HEIGHT, WEIGHT = range(2)

CONTACT_URL = (
    "https://t.me/Zelenina_Oksana"
    "?text=Хочу%20на%20курс%20%D0%A3%D1%81%D0%B2%D1%96%D0%B4%D0%BE%D0%BC%D0%BB%D0%B5%D0%BD%D0%B5%20%D1%85%D0%B0%D1%80%D1%87%D1%83%D0%B2%D0%B0%D0%BD%D0%BD%D1%8F"
)


def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        ["▶️ Старт"],
        ["📘 Детальніше про курс"],
        ["👤 Для кого курс"],
        ["📝 Як записатися"],
        ["🔄 Перерахувати ІМТ"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def contact_inline_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✍️ Написати в особисті повідомлення", url=CONTACT_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)


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


def detect_menu_action(text: str) -> str | None:
    lowered = text.strip().lower()

    if "старт" in lowered or lowered == "/start":
        return "restart"
    if "детальніше" in lowered and "курс" in lowered:
        return "course_details"
    if "для кого" in lowered:
        return "for_whom"
    if "як записатися" in lowered:
        return "signup"
    if "перерахувати" in lowered:
        return "restart"
    if lowered in ["/cancel", "скасувати", "❌ скасувати"]:
        return "cancel"

    return None


async def send_course_details(update: Update):
    await update.message.reply_text(
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
        "Це підхід без жорстких обмежень, без постійного почуття провини і без зривів.",
        reply_markup=main_keyboard(),
    )


async def send_for_whom(update: Update):
    await update.message.reply_text(
        "👤 Курс підійде тобі, якщо ти:\n\n"
        "— постійно починаєш «нове життя» з понеділка\n"
        "— зриваєшся після обмежень\n"
        "— втомилась від дієт і контролю\n"
        "— хочеш нормальні, спокійні відносини з їжею\n"
        "— хочеш змінювати харчування без стресу\n\n"
        "Це не про ідеальність.\n"
        "Це про систему, яка працює довго.",
        reply_markup=main_keyboard(),
    )


async def send_signup(update: Update):
    await update.message.reply_text(
        "Щоб записатися на курс «Усвідомлене харчування» 👇\n\n"
        "Натисни кнопку нижче і напиши мені в Telegram 💛",
        reply_markup=contact_inline_keyboard(),
    )


async def process_menu_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
    stay_state: int | None = None,
):
    if action == "course_details":
        await send_course_details(update)
        return stay_state

    if action == "for_whom":
        await send_for_whom(update)
        return stay_state

    if action == "signup":
        await send_signup(update)
        return stay_state

    if action == "restart":
        return await start(update, context)

    if action == "cancel":
        return await cancel(update, context)

    return stay_state


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


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()

    action = detect_menu_action(raw_text)
    if action:
        return await process_menu_action(update, context, action, stay_state=HEIGHT)

    text = raw_text.replace(",", ".")

    try:
        height = float(text)
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введи зріст числом.\n"
            "Наприклад: 165\n\n"
            "Або скористайся кнопками меню нижче.",
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


async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text.strip()

    action = detect_menu_action(raw_text)
    if action:
        return await process_menu_action(update, context, action, stay_state=WEIGHT)

    text = raw_text.replace(",", ".")

    try:
        weight = float(text)
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введи вагу числом.\n"
            "Наприклад: 70\n\n"
            "Або скористайся кнопками меню нижче.",
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

    height_cm = context.user_data["height"]
    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)

    category = bmi_category(bmi)
    explanation = bmi_explanation(bmi)

    message = f"""
📊 Твій результат:

Зріст: {height_cm:.1f} см
Вага: {weight:.1f} кг

👉 ІМТ: {bmi:.1f}
👉 Категорія: {category}

💡 Що це означає:
{explanation}

Важливо:
ІМТ — це лише базовий орієнтир.
Реальна проблема часто не в цифрі на вагах, а у відносинах з їжею:
— зриви
— заборони
— постійний контроль
— почуття провини після їжі

Саме тому я створила курс
«Усвідомлене харчування» 💛

Це курс для тих, хто хоче:
✔ перестати жити в режимі «схуднення з понеділка»
✔ вийти із замкненого кола зривів і заборон
✔ навчитися їсти спокійно, без страху і крайнощів
""".strip()

    context.user_data.clear()

    await update.message.reply_text(message, reply_markup=main_keyboard())
    await update.message.reply_text(
        "Обери, що тобі цікаво 👇",
        reply_markup=main_keyboard(),
    )

    return ConversationHandler.END


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = detect_menu_action(update.message.text)

    if action == "course_details":
        await send_course_details(update)

    elif action == "for_whom":
        await send_for_whom(update)

    elif action == "signup":
        await send_signup(update)

    elif action == "restart":
        return await start(update, context)

    elif action == "cancel":
        return await cancel(update, context)

    else:
        await update.message.reply_text(
            "Обери потрібний пункт меню 👇",
            reply_markup=main_keyboard(),
        )


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
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    telegram_app.add_handler(conv_handler)
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await telegram_app.initialize()
    await telegram_app.start()


@web_app.route("/", methods=["GET"])
def home():
    return "Бот працює!"


@web_app.route("/webhook", methods=["POST"])
def webhook():
    global telegram_app

    if telegram_app is None:
        return "Telegram app not initialized", 500

    data = request.get_json(force=True)

    async def process():
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)

    asyncio.run(process())
    return "ok", 200


if __name__ == "__main__":
    asyncio.run(setup_telegram())

    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
