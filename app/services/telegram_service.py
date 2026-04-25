from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import requests


class TelegramService:
    def __init__(self, bot_token: str | None, chat_id: str | None, logger: Any) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logger

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def _build_url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}/{method}"

    def send_message(self, text: str) -> bool:
        if not self.is_configured:
            self.logger.warning("Telegram nao configurado; mensagem nao enviada.")
            return False
        try:
            response = requests.post(
                self._build_url("sendMessage"),
                data={"chat_id": self.chat_id, "text": text},
                timeout=30,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            self.logger.error("Falha ao enviar mensagem para o Telegram: %s", exc)
            return False

    def send_photo(self, photo_path: str, caption: str | None = None) -> bool:
        if not self.is_configured:
            self.logger.warning("Telegram nao configurado; foto nao enviada.")
            return False

        file_path = Path(photo_path)
        if not file_path.exists():
            self.logger.error("Arquivo de foto inexistente: %s", file_path)
            return False

        try:
            with file_path.open("rb") as image_file:
                response = requests.post(
                    self._build_url("sendPhoto"),
                    data={"chat_id": self.chat_id, "caption": caption or ""},
                    files={"photo": image_file},
                    timeout=60,
                )
            response.raise_for_status()
            return True
        except requests.RequestException as exc:
            self.logger.error("Falha ao enviar foto %s para o Telegram: %s", file_path, exc)
            return False

    def send_multiple_photos(self, photo_paths: Iterable[str]) -> list[str]:
        sent_files: list[str] = []
        for photo_path in photo_paths:
            if self.send_photo(photo_path):
                sent_files.append(photo_path)
        return sent_files

