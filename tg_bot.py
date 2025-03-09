#!/usr/bin/env python3

import os
import logging
import smtplib
import telegram

from environs import Env
from email.message import EmailMessage

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler
)


# Логирование
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Этапы диалога
CHOOSING, AWAITING_FILE = range(2)


def start(update: Update, context: CallbackContext) -> int:
    departments = context.bot_data['DEPARTMENTS']
    keyboard = [[department] for department in departments]
    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    update.message.reply_text(
        'Привет! Выберите отдел, в который хотите отправить фотографию:',
        reply_markup=reply_markup,
    )
    return CHOOSING


def choose_department(update: Update, context: CallbackContext) -> int:
    departments = context.bot_data['DEPARTMENTS']
    selected_department = update.message.text
    if selected_department not in departments:
        update.message.reply_text('Выберите отдел из списка.')
        return CHOOSING

    context.user_data['department'] = selected_department
    update.message.reply_text(
        f'Вы выбрали: {selected_department}. Теперь отправьте фотографию, добавив к ней ФИО в качестве описания.',
        reply_markup=ReplyKeyboardRemove(),
    )
    return AWAITING_FILE


def send_email(context: CallbackContext, file_path: str, department: str, caption: str):
    email_settings = context.bot_data['email_settings']
    smtp_server = email_settings['SMTP_SERVER']
    smtp_port = email_settings['SMTP_PORT']
    sender_email = email_settings['SENDER_EMAIL']
    sender_email_password = email_settings['SENDER_EMAIL_PASSWORD']
    receiver_email = email_settings['RECEIVER_EMAIL']

    msg = EmailMessage()
    subject_text = f'Фото для отдела: {department} | {caption}'

    msg['Subject'] = subject_text
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with open(file_path, 'rb') as file:
            file_data = file.read()
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_name)[1].lower()
            msg.add_attachment(file_data, maintype='image', subtype=file_ext, filename=file_name)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_email_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            server.quit()

        return True

    except Exception as e:
        logger.error(f'Ошибка отправки письма: {e}')
        return False


def handle_photo(update: Update, context: CallbackContext) -> int:
    photo = update.message.photo[-1]
    caption = update.message.caption
    department = context.user_data.get('department')

    if not department:
        update.message.reply_text('Произошла ошибка. Попробуйте начать заново командой /start.')
        return ConversationHandler.END
    if not caption:
        update.message.reply_text('Произошла ошибка. Попробуйте начать заново командой /start и обязательно добавьте ФИО в качестве описания к отправляемой фотографии.')
        return ConversationHandler.END

    file = photo.get_file()
    file_path = f'/tmp/{photo.file_id}.jpg'
    file.download(file_path)

    if send_email(context, file_path, department, caption):
        update.message.reply_text('Фотография успешно отправлена!')
    else:
        update.message.reply_text('Ошибка при отправке фотографии. Попробуйте позже.')

    os.remove(file_path)
    return ConversationHandler.END


def invalid_file(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Данный тип данных не принимается. Пожалуйста, отправьте именно фотографию.')


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Отмена операции.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()

    bot_token = env.str('TELEGRAM_BOT_TOKEN')

    # Список отделов
    DEPARTMENTS = env.list('DEPARTMENTS')

    # Настройки почты
    SMTP_SERVER = env.str('SMTP_SERVER', 'smtp.yandex.ru')
    SMTP_PORT = env.int('SMTP_PORT', 587)
    SENDER_EMAIL = env.str('SENDER_EMAIL')
    SENDER_EMAIL_PASSWORD = env.str('SENDER_EMAIL_PASSWORD')
    RECEIVER_EMAIL = env.str('RECEIVER_EMAIL')

    logging.basicConfig(
        level=logging.INFO,
        format='''
            %(levelname)s : %(asctime)s : %(process)d : %(thread)d
            %(pathname)s
            %(filename)s : %(name)s : %(funcName)s : %(lineno)d
            %(message)s
         ''',
    )

    # Создаем обновлятор, который будет получать обновления от Telegram
    updater = telegram.ext.Updater(bot_token, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.bot_data['email_settings'] = {
        'SMTP_SERVER': SMTP_SERVER,
        'SMTP_PORT': SMTP_PORT,
        'SENDER_EMAIL': SENDER_EMAIL,
        'SENDER_EMAIL_PASSWORD': SENDER_EMAIL_PASSWORD,
        'RECEIVER_EMAIL': RECEIVER_EMAIL,
    }
    dispatcher.bot_data['DEPARTMENTS'] = DEPARTMENTS

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [MessageHandler(Filters.text & ~Filters.command, choose_department)],
            AWAITING_FILE: [
                MessageHandler(Filters.photo, handle_photo),
                MessageHandler(Filters.all & ~Filters.photo & ~Filters.command, invalid_file)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conversation_handler)

    # Запускаем бота
    updater.start_polling()

    # Бот будет работать до принудительной остановки
    updater.idle()


if __name__ == '__main__':
    main()
