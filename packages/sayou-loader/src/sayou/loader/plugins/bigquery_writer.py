import json
import os
from typing import Any, Tuple

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter

try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None


@register_component("writer")
class BigQueryWriter(BaseWriter):
    """
    Writes Sayou Graph Data to Google BigQuery.

    Destination Format:
        bq://project_id.dataset_id.table_id

    Authentication:
        Requires GOOGLE_APPLICATION_CREDENTIALS env var or 'bq_credentials_path' in kwargs.
    """

    component_name = "BigQueryWriter"
    SUPPORTED_TYPES = ["bigquery", "bq", "gcp"]

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in cls.SUPPORTED_TYPES:
            return 1.0

        if destination and (
            destination.startswith("bq://") or destination.startswith("bigquery://")
        ):
            return 1.0

        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        """
        Executes the BigQuery loading process.
        Returns True if successful, False otherwise.
        """
        if not bigquery:
            self._log("Package 'google-cloud-bigquery' is required.", level="error")
            return False

        # 1. Setup Credentials
        creds_path = kwargs.get("bq_credentials_path") or os.getenv(
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
        if creds_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

        # 2. Parse Destination (bq://project.dataset.table)
        try:
            project_id, dataset_id, table_id = self._parse_destination(
                destination, **kwargs
            )
        except ValueError as e:
            self._log(f"Invalid BigQuery destination: {e}", level="error")
            return False

        # 3. Initialize Client
        try:
            client = bigquery.Client(project=project_id)
            table_ref = f"{project_id}.{dataset_id}.{table_id}"
        except Exception as e:
            self._log(f"Failed to initialize BigQuery client: {e}", level="error")
            return False

        # 4. Prepare Data (Graph Nodes -> Flat Rows)
        rows_to_insert = self._transform_data(input_data)
        if not rows_to_insert:
            self._log("No data to insert.", level="warning")
            return True

        # 5. Ensure Table & Upload
        try:
            self._ensure_table(client, table_ref)
            errors = client.insert_rows_json(table_ref, rows_to_insert)

            if errors:
                self._log(f"❌ BigQuery Insert Errors: {errors}", level="error")
                return False

            self._log(
                f"✅ Successfully inserted {len(rows_to_insert)} rows into {table_ref}"
            )
            return True

        except Exception as e:
            self._log(f"BigQuery Write Error: {e}", level="error")
            return False

    def _parse_destination(self, destination: str, **kwargs) -> Tuple[str, str, str]:
        """
        Extracts project, dataset, table from URI or kwargs.
        """
        if destination and "://" in destination:
            clean_path = destination.split("://")[1]
            parts = clean_path.split(".")
            if len(parts) == 3:
                return parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                return kwargs.get("bq_project_id"), parts[0], parts[1]

        project = kwargs.get("bq_project_id")
        dataset = kwargs.get("bq_dataset_id")
        table = kwargs.get("bq_table_id") or destination

        if project and dataset and table:
            return project, dataset, table

        raise ValueError(
            "Destination must be 'bq://project.dataset.table' or parameters must be provided."
        )

    def _transform_data(self, input_data: Any) -> list:
        """
        Transforms Sayou Graph JSON into BigQuery Rows.
        """
        if isinstance(input_data, dict):
            nodes = input_data.get("nodes", [])
        elif isinstance(input_data, list):
            nodes = input_data
        else:
            return []

        rows = []
        for node in nodes:
            meta = node.get("metadata", {})
            attrs = node.get("attributes", {})

            row = {
                "node_id": node.get("node_id"),
                "label": node.get("label", "Unknown"),
                "text": attrs.get("text") or attrs.get("schema:text", "")[:20000],
                "source": meta.get("source") or "unknown",
                "page_id": meta.get("page_id"),
                "metadata_json": json.dumps(meta),
            }
            rows.append(row)
        return rows

    def _ensure_table(self, client, table_ref):
        """
        Creates table if it doesn't exist.
        """
        schema = [
            bigquery.SchemaField("node_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("label", "STRING"),
            bigquery.SchemaField("text", "STRING"),
            bigquery.SchemaField("source", "STRING"),
            bigquery.SchemaField("page_id", "STRING"),
            bigquery.SchemaField("metadata_json", "STRING"),
        ]
        try:
            client.get_table(table_ref)
        except Exception:
            table = bigquery.Table(table_ref, schema=schema)
            client.create_table(table)
            self._log(f"Created new BigQuery table: {table_ref}")
