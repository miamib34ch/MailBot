import imaplib
import email
from email.header import decode_header
import logging
import ssl
import io
import re
from bs4 import BeautifulSoup

from telegram_sender import send_to_telegram
from config import IMAP_SERVER, EMAIL_ACCOUNT, EMAIL_PASSWORD


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def decode_mime_header(header):
    """
    Декодирует заголовок письма.
    """
    if header is None:
        return ''

    decoded_header = decode_header(header)
    header_parts = []
    for part, encoding in decoded_header:
        if isinstance(part, bytes):
            if encoding:
                part = part.decode(encoding)
            else:
                part = part.decode('utf-8')
        header_parts.append(part)
    return ''.join(header_parts)


def extract_links(soup):
    """
    Извлекает все ссылки из HTML, возвращая их в виде словаря {текст ссылки: href}.
    """
    links = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        link_text = a.get_text(strip=True) or href
        links[link_text] = href
    return links


def restore_links(text, links):
    """
    Восстанавливает ссылки в тексте в формате HTML для Telegram.
    """
    for link_text, href in links.items():
        text = text.replace(link_text, f'<a href="{href}">{link_text}</a>')
    return text


def remove_replied_message(text):
    """
    Удаляет часть сообщения, на которую ответили (например, начиная с 'from:').
    """
    start_idx = text.lower().find('from:')
    if start_idx != -1:
        text = text[:start_idx]
    return text


def remove_blank_space(text):
    """
    Очищает текст, оставляя не более одной пустой строки подряд.
    """
    lines = text.split('\n')
    cleaned_lines = []
    empty_count = 0

    for line in lines:
        if line.strip() == '':
            empty_count += 1
            if empty_count <= 1:
                cleaned_lines.append(line)
        else:
            empty_count = 0
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def clean_html(html_content):
    """
    Очищает текст письма.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    links = extract_links(soup)

    # Удаляем все html теги, кроме текста + сообщение на которое ответили + лишний пустые строки
    cleaned_text = soup.get_text(separator='\n')
    cleaned_text = remove_replied_message(cleaned_text)
    cleaned_text = remove_blank_space(cleaned_text)

    final_text = restore_links(cleaned_text, links)

    return final_text


def connect_to_imap():
    """
    Устанавливает соединение с IMAP-сервером.
    """
    context = ssl.create_default_context()
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, ssl_context=context)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
    mail.select("inbox")
    return mail


def fetch_unseen_emails(mail):
    """
    Получает список непрочитанных писем.
    """
    status, messages = mail.search(None, 'UNSEEN')
    return messages[0].split()


def fetch_email(mail, email_id):
    """
    Получает письмо по его ID.
    """
    status, msg_data = mail.fetch(email_id, '(RFC822)')
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            return email.message_from_bytes(response_part[1])


async def process_email(msg):
    """
    Обрабатывает письмо, извлекая HTML-содержимое и вложения.
    """
    subject = decode_mime_header(msg["Subject"])
    from_ = decode_mime_header(msg.get("From"))

    logging.info(f"Обрабатывается письмо от: {from_}, тема: {subject}")

    attachments = []
    if msg.is_multipart():
        html_body, attachments = extract_multipart_content(msg)
    else:
        html_body = decode_html_payload(msg)
    html_body = clean_html(html_body)

    await send_to_telegram(subject, from_, html_body, attachments)


def extract_multipart_content(msg):
    """
    Извлекает HTML-контент и вложения из многочастного письма.
    """
    html_body = ""
    attachments = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = part.get("Content-Disposition", "")

        if content_type == "text/html" and not content_disposition:
            html_body = decode_html_part(part)
        elif "attachment" in content_disposition:
            attachments.append(decode_attachment(part))
        elif content_type.startswith("image/") and not content_disposition:
            attachments.append(decode_inline_image(part))

    return html_body, attachments


def decode_html_part(part):
    """
    Декодирует HTML-содержимое.
    """
    try:
        html_bytes = part.get_payload(decode=True)
        html_str = html_bytes.decode('utf-8', errors='replace')

        # Поиск кодировки в мета-теге
        match = re.search(
            r'<meta\s+http-equiv="Content-Type"\s+content="text/html;\s*charset=([^"]+)"',
            html_str, re.IGNORECASE)
        if match:
            meta_charset = match.group(1).strip()
        else:
            meta_charset = 'utf-8'

        return html_bytes.decode(meta_charset, errors='replace')

    except UnicodeDecodeError as e:
        logging.error(f"Ошибка декодирования HTML-контента: {e}")
        return ""


def decode_html_payload(msg):
    """
    Декодирует HTML-контент одночастного письма.
    """
    try:
        return msg.get_payload(decode=True).decode('utf-8', errors='replace')
    except UnicodeDecodeError as e:
        logging.error(f"Ошибка декодирования HTML-контента: {e}")
        return ""


def decode_attachment(part):
    """
    Извлекает и декодирует вложение.
    """
    filename = decode_mime_header(part.get_filename())
    if filename:
        attachment = io.BytesIO(part.get_payload(decode=True))
        attachment.name = filename
        return attachment
    return None


def decode_inline_image(part):
    """
    Извлекает и декодирует встроенное изображение.
    """
    image_data = io.BytesIO(part.get_payload(decode=True))
    image_data.name = decode_mime_header(part.get_filename()) or "image.jpg"
    return image_data


async def check_email():
    """
    Проверка почты.
    """
    try:
        mail = connect_to_imap()
        email_ids = fetch_unseen_emails(mail)

        if not email_ids:
            logging.info("Новых писем нет.")
        else:
            logging.info(f"Найдено {len(email_ids)} новых писем.")

        for email_id in email_ids:
            msg = fetch_email(mail, email_id)
            await process_email(msg)

        mail.close()
        mail.logout()

    except imaplib.IMAP4.error as e:
        logging.error("Ошибка при подключении к IMAP-серверу:", exc_info=True)
