import datetime
import os
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError:
    build = None


@register_component("fetcher")
class GoogleCalendarFetcher(BaseFetcher):
    """
    Fetches events using Google API with User OAuth Token.
    Works for Workspace (Corporate) & Personal accounts.
    """

    component_name = "GoogleCalendarFetcher"
    SUPPORTED_TYPES = ["google_calendar"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gcal://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        if not build:
            raise ImportError("Google API libraries required.")

        token_path = task.params.get("token_path")
        if not token_path or not os.path.exists(token_path):
            raise ValueError("Token path invalid.")

        creds = Credentials.from_authorized_user_file(token_path)

        service = build("calendar", "v3", credentials=creds)

        now = datetime.datetime.utcnow()
        time_min = (now - datetime.timedelta(days=30)).isoformat() + "Z"
        time_max = (now + datetime.timedelta(days=30)).isoformat() + "Z"

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])

        parsed_events = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))

            parsed_events.append(
                {
                    "id": event.get("id"),
                    "summary": event.get("summary", "No Title"),
                    "description": event.get("description", ""),
                    "start": start,
                    "end": end,
                    "location": event.get("location", ""),
                    "htmlLink": event.get("htmlLink", ""),
                    "attendees": [
                        {"email": a.get("email"), "status": a.get("responseStatus")}
                        for a in event.get("attendees", [])
                    ],
                }
            )

        return {
            "content": parsed_events,
            "meta": {
                "source": "google_calendar",
                "account": "authenticated_user",
                "count": len(parsed_events),
            },
        }
