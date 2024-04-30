import logging

from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from sqlalchemy.orm import Session

from config import DATABASE, TELEGRAM_TOKEN
from yagpt_request import analyze_answers

from data import db_session
from data.users import User
from data.results import Result

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fun_finder.log',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

(
    AGE, GENDER, PRIORITY, PRICE, SCHEDULE, CITY,
    CHILD_QUESTION_1, CHILD_QUESTION_2, CHILD_QUESTION_3,
    CHILD_QUESTION_4, CHILD_QUESTION_5, CHILD_QUESTION_6,
    CHILD_QUESTION_7, CHILD_QUESTION_8, CHILD_QUESTION_9,
    CHILD_QUESTION_10, CHILD_QUESTION_11, CHILD_QUESTION_12,
    AI_ANSWER, RESULT_LIST
) = range(1, 21)
ANSWERS = ['😡', '☹️', '🙂', '😍']
MARKUP = ReplyKeyboardMarkup(
    [ANSWERS], one_time_keyboard=False, resize_keyboard=True
)
CHILD_QUESTION_TEXT = 'Хотел(а) бы ты этим заниматься?'

db_sess: Session = None


async def start(update: Update, _):
    user = db_sess.query(User).filter(
        User.user_id == update.effective_user.id
    ).first()
    if not user:
        user = User(user_id=update.effective_user.id)
        db_sess.add(user)
        db_sess.commit()

    img = open('img/img_hola.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=(
            'Привет!\n\nМеня зовут Женя, и я помогу вам с '
            'подбором секций и кружков для вашего ребёнка. '
            'Ответьте, пожалуйста, на 6 вопросов о своих требованиях '
            'к секциям, а потом дайте ребёку пройти тестирование '
            'для оценки его склонностей и интересов\n\n'
            'Чтобы начать тестирование напиши что-нибудь'
        ),
        reply_markup=ReplyKeyboardRemove()
    )
    img.close()

    return AGE


async def age_question(update: Update, _):
    await update.message.reply_text(
        'Укажите возраст Вашего ребёнка (5-12)'
    )

    return GENDER


async def gender_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    age = update.message.text
    if not age.isdigit() or int(age) < 5 or int(age) > 12:
        await update.message.reply_text(
            'Укажите возраст Вашего ребёнка (5-12)'
        )

        return GENDER
    context.user_data['parent_answers'] = {'age': age}

    await update.message.reply_text(
        'Укажите пол Вашего ребёнка',
        reply_markup=ReplyKeyboardMarkup(
            [['мальчик👦', 'девочка👧']],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    return PRIORITY


async def priority_question(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    gender = update.message.text
    if gender not in ['мальчик👦', 'девочка👧']:
        await update.message.reply_text(
            'Укажите пол Вашего ребёнка',
            reply_markup=ReplyKeyboardMarkup(
                [['мальчик👦', 'девочка👧']],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return PRIORITY
    context.user_data['parent_answers']['gender'] = gender[:-1]

    await update.message.reply_text(
        (
            'Какое направление развития Вы '
            'считаете приоритетным для своего ребенка?'
        ),
        reply_markup=ReplyKeyboardMarkup(
            [
                ['спорт🏃‍♂️'],
                ['творчество🎭'],
                ['наука🔬']
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

    return PRICE


async def price_question(update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ['спорт🏃‍♂️', 'творчество🎭', 'наука🔬']:
        await update.message.reply_text(
            (
                'Какое направление развития Вы '
                'считаете приоритетным для своего ребенка?'
            ),
            reply_markup=ReplyKeyboardMarkup(
                [
                    ['спорт🏃‍♂️'],
                    ['творчество🎭'],
                    ['наука🔬']
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return PRICE
    context.user_data['parent_answers']['priority'] = text[:-1]

    await update.message.reply_text(
        (
            'Какую сумму вы планируете тратить '
            'на секции Вашего ребёка каждый месяц?'
        ),
        reply_markup=ReplyKeyboardMarkup(
            [
                ['До 5 тыс.р.', '5-10 тыс. р.'],
                ['10-30 тыс. р.', 'больше 30 тыс. р.']
            ],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )

    return SCHEDULE


async def schedule_question(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in \
        ['До 5 тыс.р.', '5-10 тыс. р.',
         '10-30 тыс. р.', 'больше 30 тыс. р.']:
        await update.message.reply_text(
            (
                'Какую сумму вы планируете тратить '
                'на секции Вашего ребёка каждый месяц?'
            ),
            reply_markup=ReplyKeyboardMarkup(
                [
                    ['До 5 тыс.р.', '5-10 тыс. р.'],
                    ['10-30 тыс. р.', 'больше 30 тыс. р.']
                ],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )

        return SCHEDULE
    context.user_data['parent_answers']['price'] = text

    await update.message.reply_text(
        (
            'Какое количество занятий в неделю Вы '
            'считаете оптимальным для Вашего ребёнка? (1-7)'
        ),
        reply_markup=ReplyKeyboardRemove()
    )

    return CITY


async def city_question(update: Update,
                        context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit() or int(text) < 1 or int(text) > 7:
        await update.message.reply_text(
            (
                'Какое количество занятий в неделю Вы '
                'считаете оптимальным для Вашего ребёнка? (1-7)'
            ),
            reply_markup=ReplyKeyboardRemove()
        )

        return CITY
    context.user_data['parent_answers']['schedule'] = text

    await update.message.reply_text(
        'Укажите свой город и район'
    )

    return CHILD_QUESTION_1


async def child_question_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    context.user_data['parent_answers']['city'] = text

    await update.message.reply_text(
        'А теперь передайте телефон ребёнку 😊'
    )

    img = open('img/img_art.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_2


async def child_question_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_1
    context.user_data['child_answers'] = [ANSWERS.index(text)]

    img = open('img/img_book.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_3


async def child_question_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_2
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_chemistry.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_4


async def child_question_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_3
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_chess.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_5


async def child_question_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_4
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_dance.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_6


async def child_question_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_5
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_football.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_7


async def child_question_7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_6
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_guitar.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_8


async def child_question_8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_7
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_maths.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_9


async def child_question_9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_8
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_physics.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_10


async def child_question_10(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_9
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_piano.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_11


async def child_question_11(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_10
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_skate.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return CHILD_QUESTION_12


async def child_question_12(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_11
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    img = open('img/img_tennis.jpg', 'rb')
    await update.message.reply_photo(
        photo=img,
        caption=CHILD_QUESTION_TEXT,
        reply_markup=MARKUP
    )
    img.close()

    return AI_ANSWER


async def ai_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text not in ANSWERS:
        return CHILD_QUESTION_6
    context.user_data['child_answers'] += [ANSWERS.index(text)]

    answer = analyze_answers(
        context.user_data['child_answers'],
        context.user_data['parent_answers']
    )

    user = db_sess.query(User).filter(
        User.user_id == update.effective_user.id
    ).first()
    result = Result(
        analyze_answer=answer,
        user_id=user.id
    )
    db_sess.add(result)
    db_sess.commit()

    await update.message.reply_text(
        answer,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    await update.message.reply_text(
        'Тестирование закончено, чтобы пройти его еще раз, отправьте /start'
    )

    return ConversationHandler.END


async def get_results(update: Update,
                      context: ContextTypes.DEFAULT_TYPE):
    user = db_sess.query(User).filter(
        User.user_id == update.effective_user.id
    ).first()
    results = db_sess.query(Result).filter(
        Result.user_id == user.id
    ).all()
    answer = []
    for num, result in zip(range(1, len(results) + 1), results):
        answer.append(f'{num}. {result.date}')
    answer = (
        'Введите номер ответа, который хотите пересмотреть:\n\n'
        '\n'.join(answer)
    )

    context.user_data['results_count'] = len(results)

    await update.message.reply_text(
        answer
    )

    return RESULT_LIST


async def result_list(update: Update,
                      context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not 1 <= int(text) <= context.user_data['results_count']:
        await update.message.reply_text(
            f"Введите число от 1 до {context.user_data['results_count']}"
        )
        return RESULT_LIST

    user = db_sess.query(User).filter(
        User.user_id == update.effective_user.id
    ).first()
    results = db_sess.query(Result).filter(
        Result.user_id == user.id
    ).all()

    await update.message.reply_text(
        results[int(text) - 1].analyze_answer,
        parse_mode='Markdown'
    )

    return ConversationHandler.END


async def cancel(update: Update, _):
    await update.message.reply_text(
        "Действие отменено",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    global db_sess
    db_session.global_init(DATABASE)
    db_sess = db_session.create_session()

    start_handler = CommandHandler('start', start)
    history_handler = CommandHandler('history', get_results)
    cancel_handler = CommandHandler('cancel', cancel)

    test_handler = ConversationHandler(
        entry_points=[start_handler],
        states={
            AGE: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                age_question
            )],
            GENDER: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                gender_question
            )],
            PRIORITY: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                priority_question
            )],
            PRICE: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                price_question
            )],
            SCHEDULE: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                schedule_question
            )],
            CITY: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                city_question
            )],
            CHILD_QUESTION_1: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_1
            )],
            CHILD_QUESTION_2: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_2
            )],
            CHILD_QUESTION_3: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_3
            )],
            CHILD_QUESTION_4: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_4
            )],
            CHILD_QUESTION_5: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_5
            )],
            CHILD_QUESTION_6: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_6
            )],
            CHILD_QUESTION_7: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_7
            )],
            CHILD_QUESTION_8: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_8
            )],
            CHILD_QUESTION_9: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_9
            )],
            CHILD_QUESTION_10: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_10
            )],
            CHILD_QUESTION_11: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_11
            )],
            CHILD_QUESTION_12: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                child_question_12
            )],
            AI_ANSWER: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                ai_answer
            )]
        },
        fallbacks=[cancel_handler],
        allow_reentry=True
    )

    hist_conv_handler = ConversationHandler(
        entry_points=[history_handler],
        states={
            RESULT_LIST: [MessageHandler(
                filters.TEXT & (~filters.COMMAND),
                result_list
            )]
        },
        fallbacks=[cancel_handler],
        allow_reentry=True
    )

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(test_handler)
    application.add_handler(hist_conv_handler)
    application.run_polling()

    db_sess.close()


if __name__ == '__main__':
    main()
