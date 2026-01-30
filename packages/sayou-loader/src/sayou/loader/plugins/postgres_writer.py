import json
from typing import Any, Dict, List

from sayou.core.registry import register_component

from ..interfaces.base_writer import BaseWriter

try:
    import psycopg2
except ImportError:
    psycopg2 = None


@register_component("writer")
class PostgresWriter(BaseWriter):
    """
    PostgreSQL Writer (Loader).

    Features:
    - Dynamic UPSERT support (INSERT ... ON CONFLICT DO UPDATE)
    - Automatic JSON serialization for list/dict types
    - Supports both connection URI strings and kwargs dictionaries
    """

    component_name = "PostgresWriter"

    @classmethod
    def can_handle(
        cls, input_data: Any, destination: str, strategy: str = "auto"
    ) -> float:
        if strategy in ["postgres", "postgresql", "psycopg2"]:
            return 1.0
        if destination and (
            destination.startswith("postgres://")
            or destination.startswith("postgresql://")
        ):
            return 1.0
        return 0.0

    def _do_write(self, input_data: Any, destination: str, **kwargs) -> bool:
        if not psycopg2:
            raise ImportError("Please install 'psycopg2' or 'psycopg2-binary'.")

        table_name = kwargs.get("table_name")
        pk_columns = kwargs.get("pk_columns", ["id"])
        conn_args = kwargs.get("connection_args", {})

        if not table_name:
            raise ValueError("[PostgresWriter] 'table_name' is required in kwargs.")

        rows = self._normalize_input_data(input_data)
        if not rows:
            self._log("No data rows extracted. Skipping.", level="warning")
            return True

        dsn = destination if "://" in destination else ""

        conn = None
        try:
            if dsn:
                conn = psycopg2.connect(dsn)
            else:
                conn = psycopg2.connect(**conn_args)

            cursor = conn.cursor()

            first_row = rows[0]
            columns = list(first_row.keys())

            cols_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(columns))

            pk_str = ", ".join(pk_columns)
            update_set = ", ".join(
                [f"{col} = EXCLUDED.{col}" for col in columns if col not in pk_columns]
            )

            query = f"""
                INSERT INTO {table_name} ({cols_str})
                VALUES ({placeholders})
                ON CONFLICT ({pk_str})
                DO UPDATE SET {update_set};
            """

            values_to_insert = []
            for row in rows:
                row_vals = []
                for col in columns:
                    val = row.get(col)
                    if isinstance(val, (dict, list)):
                        row_vals.append(json.dumps(val))
                    else:
                        row_vals.append(val)
                values_to_insert.append(tuple(row_vals))

            self._log(
                f"Upserting {len(values_to_insert)} rows into table '{table_name}'..."
            )
            cursor.executemany(query, values_to_insert)
            conn.commit()

            return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def _normalize_input_data(self, input_data: Any) -> List[Dict]:
        """
        Converts to various forms of standard List[Dict] format.
        """
        if hasattr(input_data, "nodes"):
            nodes = input_data.nodes
        elif isinstance(input_data, list):
            nodes = input_data
        else:
            nodes = [input_data]

        normalized = []
        for node in nodes:
            if hasattr(node, "attributes"):
                data = node.attributes
            elif hasattr(node, "metadata"):
                data = node.metadata
            elif isinstance(node, dict):
                data = node
            else:
                continue

            normalized.append(data)

        return normalized
