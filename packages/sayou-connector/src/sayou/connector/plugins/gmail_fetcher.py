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

            html_doc = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>{parsed_content['subject']}</title>
                    <meta name="sender" content="{parsed_content['sender']}">
                    <meta name="date" content="{parsed_content['date']}">
                    <meta name="uid" content="{uid}">
                    <meta name="source" content="gmail">
                </head>
                <body>
                    {parsed_content['body']}
                </body>
                </html>
            """

            return html_doc.strip()

        finally:
            mail.logout()

    def _parse_email(self, msg) -> Dict[str, Any]:
        subject = self._decode_header(msg["Subject"])
        sender = self._decode_header(msg["From"])
        date = msg["Date"]

        body_content = ""
        html_found = False

        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True)

                if not payload:
                    continue

                try:
                    text = payload.decode(
                        part.get_content_charset() or "utf-8", errors="ignore"
                    )
                except:
                    text = payload.decode("utf-8", errors="ignore")

                if ctype == "text/html":
                    body_content = text
                    html_found = True

                elif ctype == "text/plain":
                    if not html_found:
                        body_content = text

        else:
            body_content = msg.get_payload(decode=True).decode(errors="ignore")

        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body_content,
        }

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
