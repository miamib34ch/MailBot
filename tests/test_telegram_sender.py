
import pytest
from unittest.mock import AsyncMock, patch
from bot import telegram_sender

@pytest.mark.asyncio
@patch('bot.telegram_sender.Bot', autospec=True)
async def test_send_to_telegram(mock_bot_class):
    mock_bot = mock_bot_class.return_value
    mock_bot.send_message = AsyncMock()
    await telegram_sender.send_to_telegram("Subject", "from@example.com", "Body")
    mock_bot.send_message.assert_awaited_once()
