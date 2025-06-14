
from bot.mail_manager import (
    decode_mime_header, extract_links, restore_links, remove_replied_message,
    remove_blank_space, clean_html, connect_to_imap, fetch_unseen_emails, fetch_email,
    extract_multipart_content, decode_html_part, decode_html_payload, decode_attachment,
    decode_inline_image
)
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO

def test_decode_mime_header_utf8():
    encoded = '=?utf-8?q?Test_Subject?='
    result = decode_mime_header(encoded)
    assert isinstance(result, str)
    assert "Test" in result

def test_extract_links():
    html = '<a href="http://example.com">Example</a>'
    soup = BeautifulSoup(html, 'html.parser')
    assert extract_links(soup) == {'Example': 'http://example.com'}

def test_restore_links():
    text = 'Click Example'
    links = {'Example': 'http://example.com'}
    result = restore_links(text, links)
    assert '<a href=' in result

def test_remove_replied_message():
    text = "Hi\nFrom: old@example.com\nThis is old"
    result = remove_replied_message(text)
    assert "From:" not in result

def test_remove_blank_space():
    result = remove_blank_space("  Hello   World  ")
    assert isinstance(result, str)

def test_clean_html():
    html = "<div>Hello<br>World</div>"
    result = clean_html(html)
    assert "Hello" in result and "World" in result

@patch("bot.mail_manager.imaplib.IMAP4_SSL")
def test_connect_to_imap(mock_imap):
    instance = mock_imap.return_value
    instance.login.return_value = "OK"
    conn = connect_to_imap()
    instance.login.assert_called_once()

def test_fetch_unseen_emails():
    mock_mail = MagicMock()
    mock_mail.search.return_value = ("OK", [b"1 2 3"])
    result = fetch_unseen_emails(mock_mail)
    assert isinstance(result, list)

def test_fetch_email():
    mail = MagicMock()
    mail.fetch.return_value = ("OK", [(None, b"email data")])
    with patch("bot.mail_manager.email.message_from_bytes", return_value=MIMEText("test")):
        result = fetch_email(mail, b"1")
        assert result is not None

def test_extract_multipart_content():
    msg = MIMEMultipart()
    msg.attach(MIMEText("Hello", "plain"))
    html_part = MIMEText("<b>Hi</b>", "html")
    msg.attach(html_part)
    text, links = extract_multipart_content(msg)
    assert isinstance(text, str)
    assert isinstance(links, (dict, list))

def test_decode_html_part():
    part = MIMEText("<html>Hi</html>", "html", "utf-8")
    result = decode_html_part(part)
    assert isinstance(result, str)

def test_decode_html_payload():
    part = MIMEText("<html>Hi</html>", "html", "utf-8")
    result = decode_html_payload(part)
    assert isinstance(result, str)

def test_decode_attachment():
    part = MIMEBase("application", "octet-stream")
    part.set_payload(b"test")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename="test.txt")
    result = decode_attachment(part)
    assert isinstance(result, BytesIO)

def test_decode_inline_image():
    part = MIMEBase("image", "png")
    part.set_payload(b"imagedata")
    encoders.encode_base64(part)
    part.add_header("Content-ID", "<image1>")
    result = decode_inline_image(part)
    assert isinstance(result, BytesIO)
