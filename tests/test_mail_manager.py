
from bot.mail_manager import decode_mime_header, extract_links, restore_links, remove_replied_message
from bs4 import BeautifulSoup

def test_decode_mime_header_utf8():
    encoded = '=?utf-8?q?Test_Subject?='
    result = decode_mime_header(encoded)
    assert isinstance(result, str)

def test_extract_links():
    html = '<a href="http://example.com">Example</a>'
    soup = BeautifulSoup(html, 'html.parser')
    assert extract_links(soup) == {'Example': 'http://example.com'}

def test_restore_links():
    text = 'Click Example'
    links = {'Example': 'http://example.com'}
    result = restore_links(text, links)
    assert '<a href="' in result

def test_remove_replied_message():
    text = "Hi\nFrom: old@example.com\nThis is old"
    assert "From:" not in remove_replied_message(text)
