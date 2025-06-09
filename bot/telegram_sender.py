from telegram import Bot
from html import escape

from config import TELEGRAM_TOKEN, TELEGRAM_CHANNEL


async def send_to_telegram(subject, from_, body, attachments=None):
    """
    Отправка в Telegram.
    """
    bot = Bot(token=TELEGRAM_TOKEN)

    escaped_from = escape(from_)
    escaped_subject = escape(subject)

    message = (
        "<b>Получено новое письмо</b>\n\n"
        f"<b>От:</b> {escaped_from}\n"
        f"<b>Тема:</b> {escaped_subject}\n\n"
        f"<b>Содержание:</b>\n{body}"
    )

    MAX_MESSAGE_LENGTH = 4096
    if len(message) > MAX_MESSAGE_LENGTH:
        for i in range(0, len(message), MAX_MESSAGE_LENGTH):
            await bot.send_message(chat_id=TELEGRAM_CHANNEL, text=message[i:i+MAX_MESSAGE_LENGTH], parse_mode='HTML')
    else:
        await bot.send_message(chat_id=TELEGRAM_CHANNEL, text=message, parse_mode='HTML')

    if attachments:
        for attachment in attachments:
            attachment.seek(0)
            if attachment.name.lower().endswith((".jpg", ".jpeg", ".png")):
                await bot.send_photo(chat_id=TELEGRAM_CHANNEL, photo=attachment)
            else:
                await bot.send_document(chat_id=TELEGRAM_CHANNEL, document=attachment)
