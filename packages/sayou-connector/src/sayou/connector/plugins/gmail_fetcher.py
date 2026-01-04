import email
import imaplib
from email.header import decode_header
from typing import Any, Dict

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher

try:
    import html2text
except ImportError:
    html2text = None


@register_component("fetcher")
class GmailFetcher(BaseFetcher):
    """
    Fetches a specific email body and converts it to Markdown.
    """

    component_name = "GmailFetcher"
    SUPPORTED_TYPES = ["gmail"]

    @classmethod
    def can_handle(cls, uri: str) -> float:
        return 1.0 if uri.startswith("gmail-msg://") else 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        """
        Reconnects -> Fetches UID -> Parses -> Returns Dict.
        """
        params = task.params
        uid = params["uid"]
        folder = params.get("folder", "INBOX")

        mail = imaplib.IMAP4_SSL("imap.gmail.com")

        try:
            mail.login(params["username"], params["password"])
            mail.select(folder)

            status, msg_data = mail.fetch(uid, "(RFC822)")

            if status != "OK" or not msg_data:
                raise ValueError(f"Email UID {uid} not found or fetch failed.")

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            parsed_content = self._parse_email(msg)

            return {
                "content": parsed_content["markdown"],
                "meta": {
                    "source": "gmail",
                    "subject": parsed_content["subject"],
                    "sender": parsed_content["sender"],
                    "date": parsed_content["date"],
                    "uid": uid,
                },
            }

        finally:
            mail.logout()

    def _parse_email(self, msg) -> Dict[str, Any]:
        """Helper: Parses email object to Markdown text."""
        subject = self._decode_header(msg["Subject"])
        sender = self._decode_header(msg["From"])
        date = msg["Date"]

        body_text = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()

                if "attachment" in str(part.get("Content-Disposition")):
                    continue

                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                text = payload.decode(errors="ignore")

                if content_type == "text/html":
                    if html2text:
                        h = html2text.HTML2Text()
                        h.ignore_links = False
                        body_text += h.handle(text)
                    else:
                        body_text += text
                elif content_type == "text/plain":
                    if not body_text:
                        body_text += text
        else:
            payload = msg.get_payload(decode=True).decode(errors="ignore")
            if msg.get_content_type() == "text/html" and html2text:
                body_text = html2text.html2text(payload)
            else:
                body_text = payload

        md = f"# {subject}\n\n"
        md += f"- **From:** {sender}\n"
        md += f"- **Date:** {date}\n\n"
        md += "---\n\n"
        md += body_text

        return {"subject": subject, "sender": sender, "date": date, "markdown": md}

    def _decode_header(self, header_text):
        """Decodes MIME headers (e.g., =?utf-8?b?...)"""
        if not header_text:
            return "(No Subject)"
        decoded_list = decode_header(header_text)
        text = ""
        for bytes_str, encoding in decoded_list:
            if isinstance(bytes_str, bytes):
                text += bytes_str.decode(encoding or "utf-8", errors="ignore")
            else:
                text += str(bytes_str)
        return text
