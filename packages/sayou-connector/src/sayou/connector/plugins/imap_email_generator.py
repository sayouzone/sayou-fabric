import imaplib
from typing import Iterator

from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_generator import BaseGenerator


@register_component("generator")
class ImapEmailGenerator(BaseGenerator):
    """
    Scans Generic IMAP inbox and generates tasks for individual emails.
    Supports Gmail, Naver, Daum, Outlook, etc.
    """

    component_name = "ImapEmailGenerator"
    SUPPORTED_TYPES = ["imap", "email"]

    @classmethod
    def can_handle(cls, source: str) -> float:
        return 1.0 if source.startswith("imap://") else 0.0

    def _do_generate(self, source: str, **kwargs) -> Iterator[SayouTask]:
        """
        Connects to IMAP Server -> Search -> Yield Tasks.
        """
        # 1. Parse connection information
        parsed_host = source.replace("imap://", "").strip()
        imap_server = (
            parsed_host if parsed_host else kwargs.get("imap_server", "imap.gmail.com")
        )

        username = kwargs.get("username")
        password = kwargs.get("password")

        if not username or not password:
            raise ValueError(
                "IMAP credentials (username, password) required in kwargs."
            )

        folder = kwargs.get("folder", "INBOX")
        limit = int(kwargs.get("limit", 10))

        # 2. IMAP connection and search
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        try:
            mail = imaplib.IMAP4_SSL(imap_server)
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
                f"📧 [{imap_server}] Found {len(mail_ids)} emails. Generating tasks for last {len(target_ids)}."
            )

            # 3. Task generation (one task per email)
            for b_id in reversed(target_ids):
                uid = b_id.decode()

                # Fetcher will process this internal protocol
                task_uri = f"imap-msg://{imap_server}/{folder}/{uid}"

                yield SayouTask(
                    uri=task_uri,
                    source_type="imap",
                    params={
                        "imap_server": imap_server,
                        "username": username,
                        "password": password,
                        "uid": uid,
                        "folder": folder,
                    },
                    meta={"source": "imap", "server": imap_server, "email_id": uid},
                )

        except Exception as e:
            raise RuntimeError(f"IMAP connection failed to {imap_server}: {e}")
        finally:
            try:
                mail.close()
                mail.logout()
            except:
                pass
