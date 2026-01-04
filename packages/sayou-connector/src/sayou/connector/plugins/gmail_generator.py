import imaplib
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class GmailGenerator(BaseGenerator):
    """
    Scans Gmail inbox and generates tasks for individual emails.
    """

    component_name = "GmailGenerator"
    SUPPORTED_TYPES = ["gmail"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("gmail://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        Connects to Gmail -> Search -> Yield Tasks.
        """
        # 1. Parse connection information (gmail://username:password@host...)
        username = kwargs.get("username")
        password = kwargs.get("password")

        if not username or not password:
            raise ValueError("Gmail credentials required in kwargs.")

        folder = kwargs.get("folder", "INBOX")
        limit = int(kwargs.get("limit", 10))

        # 2. IMAP connection and search
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        try:
            mail.login(username, password)
            mail.select(folder)

            # Search criteria (e.g., '(UNSEEN)' or 'ALL')
            criteria = kwargs.get("search_criteria", "ALL")
            status, messages = mail.search(None, criteria)

            if status != "OK":
                return

            mail_ids = messages[0].split()
            target_ids = mail_ids[-limit:]

            self._log(
                f"📧 Found {len(mail_ids)} emails. Generating tasks for last {len(target_ids)}."
            )

            # 3. Task generation (one task per email)
            for b_id in reversed(target_ids):
                uid = b_id.decode()

                # Fetcher will process this internal protocol
                task_uri = f"gmail-msg://{folder}/{uid}"

                yield SayouTask(
                    uri=task_uri,
                    source_type="gmail",
                    params={
                        "username": username,
                        "password": password,
                        "uid": uid,
                        "folder": folder,
                    },
                )

        except Exception as e:
            raise RuntimeError(f"Gmail connection failed: {e}")
        finally:
            try:
                mail.logout()
            except:
                pass
