from urllib.parse import urljoin

from requests import get


class TelegramError(BaseException):
    def __init__(self, code, message):
        super().__init__()
        self.code = code
        self.message = message


class Telegram:
    BASE_URL = "https://api.telegram.org"

    def __init__(self, app=None):
        self.token = None
        self.chat_id = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        self.token = app.config.get("TELEGRAM_TOKEN", None)
        self.chat_id = app.config.get("TELEGRAM_CHAT_ID", None)

    @property
    def bot_base(self):
        return urljoin(self.BASE_URL, f"/bot{self.token}/")

    def send(self, message, chat_id=None, parse_mode="text"):
        parameters = {
            "chat_id": chat_id or self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }
        url = urljoin(self.bot_base, "sendMessage")
        response = get(url, params=parameters)
        result = response.json()

        if not result["ok"]:
            raise TelegramError(code=result["error_code"], message=result["description"])
        return True


telegram = Telegram()
