from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
import logging

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния
(
    CHOOSING, AGE, HEIGHT, WEIGHT, GENDER, ACTIVITY, GOAL,
    CALORIE_CHOICE,
    TEST_START, TEST_Q1, TEST_Q2, TEST_Q3, TEST_Q4, TEST_Q5,
    TEST_RESULT,
    INFO_MAIN, INFO_WORK, INFO_PRICES, INFO_QUESTIONS
) = range(19)

# Хранилище результатов теста (chat_id -> score)
test_score = {}

# Клавиатура главного меню
main_menu_keyboard = [
    ['🔢 Рассчитать калорийность', '📝 Пройти тест личного ведения'],
    ['❓ Узнать про личное ведение']
]

main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=True)

# --- /start ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Привет! Я твой помощник по здоровому питанию и достижению целей!\n\n"
        "Что я умею:\n"
        "🔢 Рассчитать твою норму калорий и БЖУ\n"
        "📝 Провести тест на готовность к личному ведению\n"
        "💬 Рассказать о программе персонального сопровождения\n\n"
        "Выбери, что тебя интересует:",
        reply_markup=main_menu_markup
    )
    return CHOOSING

# --- Обработка выбора в главном меню ---

async def choosing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == '🔢 Рассчитать калорийность':
        await update.message.reply_text(
            "🎂 Сколько тебе лет?\nВведи цифрами (например: 25)",
            reply_markup=ReplyKeyboardRemove()
        )
        return AGE

    elif text == '📝 Пройти тест личного ведения':
        test_score[update.effective_chat.id] = 0
        await update.message.reply_text(
            "📝 Тест на готовность к личному ведению\n\n"
            "Сейчас я задам тебе 5 вопросов, которые помогут понять, насколько тебе подойдет персональное сопровождение в достижении целей.\n"
            "Отвечай честно — так результат будет наиболее точным 😊\n\n"
            "Готов(а) начать?",
            reply_markup=ReplyKeyboardMarkup([['✅ Да, начать тест', '⬅️ Назад в меню']], resize_keyboard=True, one_time_keyboard=True)
        )
        return TEST_START

    elif text == '❓ Узнать про личное ведение':
        return await info_main(update, context)

    elif text == '🔄 Начать заново' or text == '📱 Главное меню':
        return await start(update, context)

    else:
        await update.message.reply_text(
            "Я не понимаю эту команду 😅\n"
            "Воспользуйся меню ниже или напиши /start для возврата в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING

# --- Ветка расчёта калорийности ---

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit() or not (10 <= int(text) <= 100):
        await update.message.reply_text("Пожалуйста, введи корректный возраст от 10 до 100 лет")
        return AGE
    context.user_data['age'] = int(text)
    await update.message.reply_text("📏 Укажи свой рост в сантиметрах\nВведи цифрами (например: 165)")
    return HEIGHT

async def height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit() or not (50 <= int(text) <= 250):
        await update.message.reply_text("Пожалуйста, введи корректный рост от 50 до 250 см")
        return HEIGHT
    context.user_data['height'] = int(text)
    await update.message.reply_text("⚖️ Укажи свой текущий вес в килограммах\nВведи цифрами (например: 60)")
    return WEIGHT

async def weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not text.isdigit() or not (20 <= int(text) <= 300):
        await update.message.reply_text("Пожалуйста, введи корректный вес от 20 до 300 кг")
        return WEIGHT
    context.user_data['weight'] = int(text)
    keyboard = [['👩 Женский', '👨 Мужской']]
    await update.message.reply_text(
        "👤 Укажи свой пол:\nЭто нужно для точного расчета базового метаболизма",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GENDER

async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text not in ['👩 Женский', '👨 Мужской']:
        await update.message.reply_text("Пожалуйста, выбери пол с помощью кнопок")
        return GENDER
    context.user_data['gender'] = 'женский' if 'Женский' in text else 'мужской'

    keyboard = [
        ['🪑 Малоподвижный (офис, минимум спорта)'],
        ['🚶‍♀️ Лёгкая активность (1-2 тренировки в неделю)'],
        ['🏃‍♀️ Средняя активность (3-5 тренировок в неделю)'],
        ['🏋️‍♀️ Высокая активность (ежедневные тренировки или физ. работа)']
    ]
    await update.message.reply_text(
        "🏃‍♀️ Выбери свой уровень физической активности:\nЭто поможет рассчитать дневную потребность в калориях",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return ACTIVITY

async def activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    levels = {
        '🪑 малоподвижный (офис, минимум спорта)': 1.2,
        '🚶‍♀️ лёгкая активность (1-2 тренировки в неделю)': 1.375,
        '🏃‍♀️ средняя активность (3-5 тренировок в неделю)': 1.55,
        '🏋️‍♀️ высокая активность (ежедневные тренировки или физ. работа)': 1.725
    }
    text = update.message.text.strip().lower()
    if text not in levels:
        await update.message.reply_text("Пожалуйста, выбери уровень активности из списка")
        return ACTIVITY
    context.user_data['activity'] = levels[text]

    keyboard = [['📉 Похудение', '⚖️ Поддержание веса', '📈 Набор массы']]
    await update.message.reply_text(
        "🎯 Какая у тебя цель?\nВыбери основное направление, к которому стремишься",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return GOAL

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    goals = {'📉 похудение': 'похудение', '⚖️ поддержание веса': 'поддержание', '📈 набор массы': 'набор'}
    text = update.message.text.strip().lower()
    if text not in goals:
        await update.message.reply_text("Пожалуйста, выбери цель из списка")
        return GOAL
    context.user_data['goal'] = goals[text]

    # Расчеты
    age = context.user_data['age']
    height = context.user_data['height']
    weight = context.user_data['weight']
    gender = context.user_data['gender']
    activity = context.user_data['activity']

    if gender == 'женский':
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age + 5

    tdee = int(bmr * activity)

    # Калорийность по целям
    calories_map = {
        'похудение': tdee - 300,
        'поддержание': tdee,
        'набор': tdee + 300
    }
    context.user_data['calories_map'] = calories_map

    keyboard = [
        [f"📉 Похудение: {calories_map['похудение']} ккал (дефицит 300 ккал)"],
        [f"⚖️ Поддержание: {calories_map['поддержание']} ккал"],
        [f"📈 Набор массы: {calories_map['набор']} ккал (профицит 300 ккал)"]
    ]
    await update.message.reply_text(
        f"💡 Основываясь на твоих данных, вот рекомендации:\n\n"
        f"📊 Твой базовый метаболизм: {int(bmr)} ккал\n"
        f"🔥 Дневная потребность: {tdee} ккал\n\n"
        f"Выбери калорийность для подробного расчёта БЖУ:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CALORIE_CHOICE

def calc_bju(calories: int):
    prot = round(calories * 0.3 / 4)
    fat = round(calories * 0.225 / 9)
    carb = round(calories * 0.475 / 4)
    return prot, fat, carb

async def calorie_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip().lower()
    calories_map = context.user_data.get('calories_map', {})
    found = False
    for goal, cal in calories_map.items():
        if goal in text:
            prot, fat, carb = calc_bju(cal)
            await update.message.reply_text(
                f"🎉 Твой персональный план питания готов!\n\n"
                f"📊 {goal.capitalize()}: {cal} ккал/день\n\n"
                f"🥩 Белки: {prot} г (30%)\n"
                f"🥑 Жиры: {fat} г (22.5%)\n"
                f"🍞 Углеводы: {carb} г (47.5%)\n\n"
                f"💡 Рекомендации:\n"
                f"• Распредели питание на 3-4 приема пищи\n"
                f"• Пей достаточно воды (30-35 мл на 1 кг веса)\n"
                f"• Включай разнообразные продукты для получения всех витаминов\n\n"
                f"Хочешь узнать больше о том, как я могу помочь тебе достичь этих целей?",
                reply_markup=ReplyKeyboardMarkup([
                    ['📝 Пройти тест личного ведения', '💬 Узнать про личное ведение'],
                    ['🔄 Начать заново', '📱 Главное меню']
                ], resize_keyboard=True, one_time_keyboard=True)
            )
            found = True
            break
    if not found:
        await update.message.reply_text("Пожалуйста, выбери одну из предложенных кнопок")
        return CALORIE_CHOICE
    return CHOOSING

# --- Ветка теста на готовность ---

async def test_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == '✅ Да, начать тест':
        await update.message.reply_text(
            "🍰 Вопрос 1/5\n\nКак часто ты срываешься на сладкое или другую \"вредную\" еду?",
            reply_markup=ReplyKeyboardMarkup([
                ['😅 Часто (почти каждый день)', '🤔 Иногда (несколько раз в неделю)', '😌 Редко (раз в неделю или реже)']
            ], resize_keyboard=True, one_time_keyboard=True)
        )
        return TEST_Q1
    elif text == '⬅️ Назад в меню' or text == '⬅️ Назад':
        return await start(update, context)
    else:
        await update.message.reply_text(
            "Пожалуйста, выбери из кнопок или вернись в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING

async def test_q1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {
        '😅 часто (почти каждый день)': 2,
        '🤔 иногда (несколько раз в неделю)': 1,
        '😌 редко (раз в неделю или реже)': 0
    }
    ans = update.message.text.strip().lower()
    if ans not in answers:
        await update.message.reply_text(
            "Пожалуйста, выбери из кнопок или вернись в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING
    test_score[update.effective_chat.id] += answers[ans]
    await update.message.reply_text(
        "🤯 Вопрос 2/5\n\nЕсть ли у тебя ощущение, что ты всё знаешь о правильном питании, но не можешь внедрить в жизнь?",
        reply_markup=ReplyKeyboardMarkup([
            ['😔 Да, знаю что делать, но не получается', '🤷‍♀️ Нет, у меня проблемы с знаниями']
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return TEST_Q2

async def test_q2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {
        '😔 да, знаю что делать, но не получается': 2,
        '🤷‍♀️ нет, у меня проблемы с знаниями': 0
    }
    ans = update.message.text.strip().lower()
    if ans not in answers:
        await update.message.reply_text(
            "Пожалуйста, выбери из кнопок или вернись в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING
    test_score[update.effective_chat.id] += answers[ans]
    await update.message.reply_text(
        "🤝 Вопрос 3/5\n\nХочется ли тебе поддержки, мотивации или контроля со стороны?",
        reply_markup=ReplyKeyboardMarkup([
            ['💪 Да, нужна поддержка', '🙅‍♀️ Нет, справлюсь сам(а)']
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return TEST_Q3

async def test_q3(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {
        '💪 да, нужна поддержка': 2,
        '🙅‍♀️ нет, справлюсь сам(а)': 0
    }
    ans = update.message.text.strip().lower()
    if ans not in answers:
        await update.message.reply_text(
            "Пожалуйста, выбери из кнопок или вернись в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING
    test_score[update.effective_chat.id] += answers[ans]
    await update.message.reply_text(
        "📊 Вопрос 4/5\n\nГотов(а) ли ты тратить 2-3 минуты в день на ведение пищевого дневника и отчёт о прогрессе?",
        reply_markup=ReplyKeyboardMarkup([
            ['✅ Да, готов(а)', '❌ Нет, это не для меня']
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return TEST_Q4

async def test_q4(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {
        '✅ да, готов(а)': 2,
        '❌ нет, это не для меня': 0
    }
    ans = update.message.text.strip().lower()
    if ans not in answers:
        await update.message.reply_text(
            "Пожалуйста, выбери из кнопок или вернись в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING
    test_score[update.effective_chat.id] += answers[ans]
    await update.message.reply_text(
        "🎯 Вопрос 5/5\n\nУ тебя есть чёткая, конкретная цель? (например: \"похудеть на 5 кг к лету\" вместо \"хочу похудеть\")",
        reply_markup=ReplyKeyboardMarkup([
            ['🎯 Да, цель конкретная', '🤔 Нет, пока размыто']
        ], resize_keyboard=True, one_time_keyboard=True)
    )
    return TEST_Q5

async def test_q5(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answers = {
        '🎯 да, цель конкретная': 2,
        '🤔 нет, пока размыто': 0
    }
    ans = update.message.text.strip().lower()
    if ans not in answers:
        await update.message.reply_text(
            "Пожалуйста, выбери из кнопок или вернись в главное меню",
            reply_markup=main_menu_markup
        )
        return CHOOSING
    test_score[update.effective_chat.id] += answers[ans]

    score = test_score[update.effective_chat.id]
    if score >= 6:
        await update.message.reply_text(
            f"🎉 Отлично! Набрано баллов: {score}/10\n\n"
            "Ты большая молодец и похоже, что личное ведение будет отличным шагом к твоим целям! \n\n"
            "У тебя есть:\n"
            "✅ Понимание своих слабых мест\n"
            "✅ Готовность работать над собой\n"
            "✅ Мотивация к изменениям\n\n"
            "Я помогу тебе структурировать питание, найти подход к срывам и довести до желаемого результата.\n\n"
            "Хочешь узнать подробности и начать?",
            reply_markup=ReplyKeyboardMarkup([
                ['💬 Написать в Telegram: @iam_lsn', '💰 Узнать цены'],
                ['🔄 Пройти тест заново', '📱 Главное меню']
            ], resize_keyboard=True, one_time_keyboard=True)
        )
    else:
        await update.message.reply_text(
            f"💪 Набрано баллов: {score}/10\n\n"
            "Ты уже проделала большую работу и у тебя уже всё получается! \n\n"
            "Возможно, сейчас тебе больше подойдет самостоятельный путь с использованием полученных знаний о калорийности и БЖУ.\n\n"
            "Но если в процессе захочешь поддержки или возникнут вопросы — я всегда рядом!",
            reply_markup=ReplyKeyboardMarkup([
                ['💬 Написать в Telegram: @iam_lsn', '📚 Узнать про личное ведение'],
                ['🔄 Пройти тест заново', '📱 Главное меню']
            ], resize_keyboard=True, one_time_keyboard=True)
        )

    if update.effective_chat.id in test_score:
        del test_score[update.effective_chat.id]
    return CHOOSING

# --- Ветка информации о личном ведении ---

async def info_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ['📋 Как проходит работа', '💰 Узнать цены'],
        ['❓ Задать вопрос', '📝 Пройти тест готовности'],
        ['📱 Главное меню']
    ]
    await update.message.reply_text(
        "💎 Личное ведение по питанию\n\n"
        "Работаю с каждым клиентом индивидуально — от анализа привычек до достижения устойчивого результата. Никаких шаблонов, только персональный подход под ваши цели и образ жизни.\n\n"
        "🎯 Что получаете:\n"
        "• Персональную работу с рационом\n"
        "• Знания о питании\n"
        "• Постоянную поддержку\n"
        "• Ответы на все вопросы\n\n"
        "💻 Формат — структурированный чат в Telegram:\n"
        "🗨️ Ежедневное общение и вопросы\n"
        "📚 База знаний под рукой\n"
        "🔥 Мотивация каждый день\n"
        "📊 Отслеживание прогресса\n\n"
        "Все четко, без путаницы — работаем на ваш результат.\n"
        "Это инвестиция в долгосрочное здоровье, а не просто диета.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return INFO_MAIN

async def info_work(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ['💰 Узнать цены', '❓ Задать вопрос'],
        ['⬅️ Назад', '📱 Главное меню']
    ]
    await update.message.reply_text(
        "📋 Как проходит личное ведение:\n\n"
        "1. Анкета\n"
        "Заполняете подробную анкету о питании, здоровье, целях и образе жизни\n\n"
        "2. Анализ\n"
        "Изучаю ваши ответы, выявляю ключевые моменты и составляю стратегию\n\n"
        "3. Персональный план\n"
        "Получаете индивидуально рассчитанное КБЖУ с учетом ваших особенностей\n\n"
        "4. Сопровождение\n"
        "Ежедневная поддержка, корректировки, ответы на вопросы в процессе\n\n"
        "5. Контрольные точки\n"
        "Регулярно отслеживаем прогресс и вносим изменения при необходимости\n\n"
        "6. Работа с пищевыми привычками\n"
        "Разбираем триггеры, заменяем вредные привычки на полезные\n\n"
        "7. Закрепление результата\n"
        "Формируем устойчивые привычки для долгосрочного эффекта\n\n"
        "💻 Работа полностью онлайн",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return INFO_WORK

async def info_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ['💬 Написать в Telegram: @iam_lsn', '❓ Задать вопрос'],
        ['⬅️ Назад', '📱 Главное меню']
    ]
    await update.message.reply_text(
        "💰 Стоимость личного ведения:\n\n"
        "📅 1 месяц — 5000₽\n"
        "Идеально для: знакомства с подходом, решения конкретной задачи\n\n"
        "📅 3 месяца — 12000₽ (экономия 3000₽, скидка 20%)\n"
        "Идеально для: формирования привычек, стабильного результата\n\n"
        "📅 6 месяцев — 21000₽ (экономия 9000₽, скидка 30%)\n"
        "Идеально для: кардинальных изменений, долгосрочного результата\n\n"
        "🎁 Что входит во все пакеты:\n"
        "• Персональную работу с рационом\n"
        "• Знания о питании\n"
        "• Постоянную поддержку\n"
        "• Ответы на все вопросы\n"
        "• Структурированный чат в Telegram\n"
        "• Отслеживание прогресса\n\n"
        "Если есть вопросы — смело пиши!",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return INFO_PRICES

async def info_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [
        ['💬 Написать в Telegram: @iam_lsn'],
        ['⬅️ Назад', '📱 Главное меню']
    ]
    await update.message.reply_text(
        "❓ Есть вопросы? Задавай!\n\n"
        "Ты можешь:\n"
        "• Подписаться на мой канал и задать вопрос в комментариях: @iamolsn\n"
        "• Написать мне лично в Telegram: @iam_lsn\n\n"
        "Я отвечу на любые вопросы о программе, подходе, результатах и всем остальном 😊",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return INFO_QUESTIONS

# --- Обработка кнопок в разделе информации ---

async def info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text

    if text == '📋 Как проходит работа':
        return await info_work(update, context)
    elif text == '💰 Узнать цены':
        return await info_prices(update, context)
    elif text == '❓ Задать вопрос':
        return await info_questions(update, context)
    elif text == '📝 Пройти тест готовности':
        test_score[update.effective_chat.id] = 0
        await update.message.reply_text(
            "📝 Тест на готовность к личному ведению\n\n"
            "Сейчас я задам тебе 5 вопросов, которые помогут понять, насколько тебе подойдет персональное сопровождение в достижении целей.\n"
            "Отвечай честно — так результат будет наиболее точным 😊\n\n"
            "Готов(а) начать?",
            reply_markup=ReplyKeyboardMarkup(
                [['✅ Да, начать тест', '⬅️ Назад']],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return TEST_START
    elif text == '⬅️ Назад':
        return await info_main(update, context)
    elif text == '📱 Главное меню':
        return await start(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выбери одну из кнопок")
        return INFO_MAIN


# --- Начать заново ---

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await start(update, context)

# --- Команда /stop ---

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "👋 Пока! Было приятно помочь тебе!\n\n"
        "Если захочешь:\n"
        "• Рассчитать калорийность заново — напиши /start\n"
        "• Задать вопрос — пиши в Telegram: @iam_lsn\n\n"
        "Удачи в достижении целей! 💪",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# --- Обработка неизвестных сообщений ---

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я не понимаю эту команду 😅\n"
        "Воспользуйся меню ниже или напиши /start для возврата в главное меню",
        reply_markup=main_menu_markup
    )
    return CHOOSING

# --- Главная функция ---

def main():
    app = ApplicationBuilder().token("5284761727:AAG5nQPZNpWLN4Gc3fCpYGtGBT83wYLNK0U").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choosing)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight)],
            GENDER: [MessageHandler(filters.Regex('^(👩 Женский|👨 Мужской)$'), gender)],
            ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, activity)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, goal)],
            CALORIE_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, calorie_choice)],

            TEST_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_start)],
            TEST_Q1: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_q1)],
            TEST_Q2: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_q2)],
            TEST_Q3: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_q3)],
            TEST_Q4: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_q4)],
            TEST_Q5: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_q5)],

            INFO_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler)],
            INFO_WORK: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler)],
            INFO_PRICES: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler)],
            INFO_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, info_handler)],
        },
        fallbacks=[CommandHandler('stop', stop), CommandHandler('start', start)]
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.COMMAND, unknown))  # неизвестные команды

    app.run_polling()

if __name__ == '__main__':
    main()
