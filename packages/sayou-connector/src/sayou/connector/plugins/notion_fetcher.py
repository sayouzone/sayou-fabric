import re
from typing import Any, Dict, List

import requests
from sayou.core.registry import register_component
from sayou.core.schemas import SayouTask

from ..interfaces.base_fetcher import BaseFetcher


@register_component("fetcher")
class NotionFetcher(BaseFetcher):
    """
    Fetches Notion content.
    Supports:
    1. Pages (Text, Media, Simple Tables)
    2. Inline Databases (Databases embedded inside pages)
    3. Full Databases (URL with ?v=...)
    """

    component_name = "NotionFetcher"
    SUPPORTED_TYPES = ["notion"]

    UUID_PATTERN = re.compile(
        r"[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}",
        re.IGNORECASE,
    )

    @classmethod
    def can_handle(cls, uri: str) -> float:
        if uri.startswith("notion://"):
            return 1.0
        if "notion.so" in uri or "notion.site" in uri:
            return 1.0
        return 0.0

    def _do_fetch(self, task: SayouTask) -> Dict[str, Any]:
        token = task.params.get("notion_token")
        if not token:
            raise ValueError("[NotionFetcher] 'notion_token' is required.")

        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }

        resource_id = self._extract_id(task.uri)
        if not resource_id:
            raise ValueError(f"Invalid Notion ID in URI: {task.uri}")

        try:
            return self._fetch_as_page(resource_id)
        except RuntimeError:
            self._log(
                f"ID {resource_id} is not a Page. Trying Database...", level="debug"
            )
            return self._fetch_as_database_root(resource_id)

    # --- Mode A: Page (Recursive) ---
    def _fetch_as_page(self, page_id: str) -> Dict[str, Any]:
        url = f"https://api.notion.com/v1/pages/{page_id}"
        resp = requests.get(url, headers=self.headers)

        if resp.status_code != 200:
            raise RuntimeError(f"Status {resp.status_code}")

        page_meta = resp.json()
        title = self._extract_title_prop(page_meta)

        md_content = f"# {title}\n\n"
        root_blocks = self._get_children_recursive(page_id)
        for block in root_blocks:
            md_content += self._block_to_markdown(block) + "\n"

        return {
            "content": md_content,
            "meta": {
                "source": "notion",
                "type": "page",
                "page_id": page_id,
                "title": title,
                "url": page_meta.get("url", ""),
                "filename": f"{self._sanitize_filename(title)}.md",
            },
        }

    # --- Mode B: Database (Root) ---
    def _fetch_as_database_root(self, db_id: str) -> Dict[str, Any]:
        url = f"https://api.notion.com/v1/databases/{db_id}"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            raise RuntimeError(f"Access Failed: {db_id}")

        db_meta = resp.json()
        title = (
            "".join([t.get("plain_text", "") for t in db_meta.get("title", [])])
            or "Untitled DB"
        )

        md_table = self._query_and_render_database(db_id)

        full_md = f"# [DB] {title}\n\n{md_table}"

        return {
            "content": full_md,
            "meta": {
                "source": "notion",
                "type": "database",
                "page_id": db_id,
                "title": title,
                "filename": f"DB_{self._sanitize_filename(title)}.md",
            },
        }

    # --- Core Logic: Block to Markdown ---
    def _block_to_markdown(self, block: Dict, indent: int = 0) -> str:
        b_type = block.get("type")
        prefix = "  " * indent

        # [Inline Database]
        if b_type == "child_database":
            db_id = block["id"]
            db_title = block.get("child_database", {}).get("title", "Inline Database")
            table_md = self._query_and_render_database(db_id)

            return f"\n{prefix}### 📂 {db_title}\n{table_md}\n"

        # [Simple Table]
        if b_type == "table":
            rows = block.get("children_data", [])
            if not rows:
                return ""
            md_lines = []
            has_header = block.get("table", {}).get("has_column_header", False)
            for idx, row in enumerate(rows):
                if row.get("type") == "table_row":
                    cells = row.get("table_row", {}).get("cells", [])
                    row_txt = "|" + "".join(
                        [
                            f" {''.join([t.get('plain_text', '') for t in c])} |"
                            for c in cells
                        ]
                    )
                    md_lines.append(f"{prefix}{row_txt}")
                    if has_header and idx == 0:
                        md_lines.append(
                            f"{prefix}|" + "|".join([" --- " for _ in cells]) + "|"
                        )
            return "\n".join(md_lines) + "\n"

        # Standard Blocks
        content = block.get(b_type, {})
        text = ""
        if "rich_text" in content:
            text = "".join(
                [t.get("plain_text", "") for t in content.get("rich_text", [])]
            )

        md = ""
        if b_type == "paragraph":
            md = f"{prefix}{text}\n"
        elif b_type.startswith("heading_"):
            md = f"\n{prefix}{'#' * int(b_type[-1])} {text}\n"
        elif b_type == "bulleted_list_item":
            md = f"{prefix}- {text}"
        elif b_type == "numbered_list_item":
            md = f"{prefix}1. {text}"
        elif b_type == "code":
            lang = content.get("language", "text")
            md = f"{prefix}```{lang}\n{prefix}{text}\n{prefix}```"
        elif b_type == "image":
            src = content.get("file", {}).get("url") or content.get("external", {}).get(
                "url"
            )
            md = f"{prefix}![img]({src})"

        # Recursive Children (except tables/dbs which handle their own data)
        if block.get("children_data") and b_type not in ["table", "child_database"]:
            next_indent = (
                indent + 1
                if b_type in ["toggle", "bulleted_list_item", "numbered_list_item"]
                else indent
            )
            for child in block["children_data"]:
                child_md = self._block_to_markdown(child, next_indent)
                if child_md:
                    md += "\n" + child_md

        return md

    # --- Helper: Universal Database Renderer ---
    def _query_and_render_database(self, db_id: str) -> str:
        """
        [핵심] 어떤 DB ID가 들어오든 내용을 조회(Query)해서 Markdown Table 문자열로 반환합니다.
        Root DB Fetch와 Inline DB Fetch 양쪽에서 사용합니다.
        """
        items = []
        query_url = f"https://api.notion.com/v1/databases/{db_id}/query"
        has_more = True
        next_cursor = None

        # 1. Fetch All Items
        while has_more:
            payload = {
                "page_size": 100,
                # "sorts": [{"timestamp": "created_time", "direction": "ascending"}],
            }
            if next_cursor:
                payload["start_cursor"] = next_cursor
            r = requests.post(query_url, headers=self.headers, json=payload)
            if r.status_code != 200:
                self._log(f"DB Query Failed {db_id}: {r.text}", level="warning")
                return "> ⚠️ Failed to load database content."

            d = r.json()
            items.extend(d.get("results", []))
            has_more = d.get("has_more")
            next_cursor = d.get("next_cursor")

        if not items:
            return "> (Empty Database)"

        # 2. Extract Headers (from first item)
        first_props = items[0].get("properties", {})
        headers = list(first_props.keys())

        # 3. Build Markdown Table
        # Header
        md = "| " + " | ".join(headers) + " |\n"
        md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # Rows
        for item in items:
            row_cells = []
            props = item.get("properties", {})
            for col in headers:
                val = props.get(col, {})
                txt = self._extract_prop_value(val)
                safe_txt = txt.replace("\n", " ").replace("|", "/")
                row_cells.append(safe_txt)
            md += "| " + " | ".join(row_cells) + " |\n"

        return md

    # --- Utils ---
    def _extract_id(self, source: str) -> str:
        if "?" in source:
            source = source.split("?")[0]
        match = self.UUID_PATTERN.search(source)
        return match.group(0) if match else None

    def _get_children_recursive(self, block_id: str) -> List[Dict]:
        results = []
        url = f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100"
        while url:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code != 200:
                break
            data = resp.json()
            for block in data.get("results", []):
                if block.get("has_children"):
                    block["children_data"] = self._get_children_recursive(block["id"])
                results.append(block)
            url = (
                f"https://api.notion.com/v1/blocks/{block_id}/children?page_size=100&start_cursor={data['next_cursor']}"
                if data.get("has_more")
                else None
            )
        return results

    def _extract_title_prop(self, meta: Dict) -> str:
        for v in meta.get("properties", {}).values():
            if v.get("type") == "title":
                return "".join([t.get("plain_text") for t in v.get("title", [])])
        return "Untitled"

    def _extract_prop_value(self, val: Dict) -> str:
        t = val.get("type")
        if t == "title":
            return "".join([x.get("plain_text") for x in val.get("title", [])])
        if t == "rich_text":
            return "".join([x.get("plain_text") for x in val.get("rich_text", [])])
        if t == "select":
            return val.get("select", {}).get("name") or ""
        if t == "status":
            return val.get("status", {}).get("name") or ""
        if t == "url":
            return val.get("url") or ""
        if t == "date":
            return val.get("date", {}).get("start") or ""
        if t == "checkbox":
            return "Yes" if val.get("checkbox") else "No"
        if t == "email":
            return val.get("email") or ""
        if t == "number":
            return str(val.get("number") or "")
        return ""

    def _sanitize_filename(self, name: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
