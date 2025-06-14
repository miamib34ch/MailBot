
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, ANY
from bot import telegram_sender

@pytest.mark.asyncio
@patch("bot.telegram_sender.Bot", autospec=True)
async def test_send_simple_message(mock_bot_class):
    mock_bot = mock_bot_class.return_value
    mock_bot.send_message = AsyncMock()

    await telegram_sender.send_to_telegram("Subject", "from@example.com", "Hello body")

    mock_bot.send_message.assert_awaited_once_with(
        chat_id=telegram_sender.TELEGRAM_CHANNEL,
        text=ANY,
        parse_mode="HTML"
    )

@pytest.mark.asyncio
@patch("bot.telegram_sender.Bot", autospec=True)
async def test_send_long_message_in_parts(mock_bot_class):
    mock_bot = mock_bot_class.return_value
    mock_bot.send_message = AsyncMock()

    long_body = "A" * 5000
    await telegram_sender.send_to_telegram("Subject", "from@example.com", long_body)

    assert mock_bot.send_message.await_count >= 2

@pytest.mark.asyncio
@patch("bot.telegram_sender.Bot", autospec=True)
async def test_send_with_image_attachment(mock_bot_class):
    mock_bot = mock_bot_class.return_value
    mock_bot.send_message = AsyncMock()
    mock_bot.send_photo = AsyncMock()

    img = MagicMock()
    img.name = "photo.jpg"
    img.seek = MagicMock()

    await telegram_sender.send_to_telegram("Subject", "from@example.com", "Body", attachments=[img])

    mock_bot.send_photo.assert_awaited_once_with(
        chat_id=telegram_sender.TELEGRAM_CHANNEL,
        photo=img
    )

@pytest.mark.asyncio
@patch("bot.telegram_sender.Bot", autospec=True)
async def test_send_with_document_attachment(mock_bot_class):
    mock_bot = mock_bot_class.return_value
    mock_bot.send_message = AsyncMock()
    mock_bot.send_document = AsyncMock()

    file = MagicMock()
    file.name = "file.pdf"
    file.seek = MagicMock()

    await telegram_sender.send_to_telegram("Subject", "from@example.com", "Body", attachments=[file])

    mock_bot.send_document.assert_awaited_once_with(
        chat_id=telegram_sender.TELEGRAM_CHANNEL,
        document=file
    )
