from pathlib import Path

from app.main import gather_sendable_screenshots
from app.models import QuoteResult
from app.services.screenshot_service import ScreenshotService


def test_choose_existing_screenshot_prefers_success_file(app_config, test_logger) -> None:
    screenshot_service = ScreenshotService(app_config, test_logger)
    success_file = app_config.screenshots_dir / "success.png"
    fallback_file = app_config.errors_dir / "error.png"
    success_file.write_bytes(b"ok")
    fallback_file.write_bytes(b"ok")

    selected = screenshot_service.choose_existing_screenshot(success_file, fallback_file)

    assert selected == str(success_file)


def test_gather_sendable_screenshots_falls_back_to_error_image(app_config) -> None:
    error_file = app_config.errors_dir / "movida_error.png"
    error_file.write_bytes(b"ok")
    result = QuoteResult(provider="Movida", success=False, error_artifacts=[str(error_file)])

    screenshots = gather_sendable_screenshots(result)

    assert screenshots == [str(error_file)]
