from datetime import datetime

def create_application_path(username: str, telegram_id: int) -> str:
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = username.replace(" ", "_")
    return f"/applications/{telegram_id}_{safe_name}_{now}.pdf"
