import os
import requests

from config import (
    REQUEST_TIMEOUT,
    SLACK_WEBHOOK_ENV,
)


def send_to_slack(message):

    webhook_url = os.getenv(
        SLACK_WEBHOOK_ENV
    )

    if not webhook_url:

        print(
            "SLACK_WEBHOOK_URL がありません"
        )

        return False

    response = requests.post(
        webhook_url,
        json={
            "text": message
        },
        timeout=REQUEST_TIMEOUT,
    )

    print(
        "Slack status:",
        response.status_code,
    )

    if 200 <= response.status_code < 300:

        return True

    print(
        "Slack送信に失敗しました。"
        f"status={response.status_code}"
    )

    return False
