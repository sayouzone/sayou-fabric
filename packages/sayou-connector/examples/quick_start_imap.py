import logging

from sayou.loader import LoaderPipeline

from sayou.connector import ConnectorPipeline

try:
    from sayou.visualizer import VisualizerPipeline

    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")


def run_demo():
    print(">>> Initializing Sayou Connector Brain...")
    connector = ConnectorPipeline()
    loader = LoaderPipeline()
    loader.initialize()
    connector.initialize()

    if VISUALIZER_AVAILABLE:
        print("[Demo] Visualizer detected! Attaching pipeline...")
        viz = VisualizerPipeline()
        viz.attach_to(connector)

    # ---------------------------------------------------------
    # Scenario 1: Gmail Connector
    # ---------------------------------------------------------
    print("\n=== [1] Gmail Connector Demo ===")

    import os

    IMAP_MAIL = os.environ.get("IMAP_MAIL", "IMAP_MAIL")
    IMAP_PASSWORD = os.environ.get("IMAP_PASSWORD", "IMAP_PASSWORD")

    packets = connector.run(
        source="imap://",
        imap_server="imap.gmail.com",
        username=IMAP_MAIL,
        password=IMAP_PASSWORD,
    )

    for i, packet in enumerate(packets):

        if not packet.success:
            print(f"❌ Error: {packet.error}")
            continue

        print("-" * 40)

        if isinstance(packet.data, dict):
            meta = packet.data.get("meta", {})
            subject = meta.get("subject", "No Subject")
            sender = meta.get("sender", "Unknown")
            content = packet.data.get("content", "")

            print(f"📧 Subject: {subject}")
            print(f"👤 From:    {sender}")
            print("-" * 20)
            print(content[:500] + "..." if len(content) > 500 else content)

            import os
            import re

            def sanitize_filename(name):
                """Remove invalid characters for file names"""
                if not name:
                    return "No_Subject"
                return re.sub(r'[\\/*?:"<>|]', "", name).strip()

            subject = sanitize_filename(meta.get("subject", "Untitled"))
            filename = f"{subject}.md"
            full_destination = os.path.join("examples/", filename)

            loader.run(
                input_data=packet.data["content"],
                destination=full_destination,
            )

        elif isinstance(packet.data, bytes):
            content = packet.data.decode("utf-8")
            print(f"[{i}] File: {packet.task.meta['filename']}")
            print(f"    Content: {content[:20]}...")
        else:
            print(f"📝 Data: {str(packet.data)[:500]}")

        print("-" * 40)

    if VISUALIZER_AVAILABLE:
        viz.report("examples/visualizer_gmail_demo.html")
        print(f"[Demo] Report generated: visualizer_gmail_demo.html")


if __name__ == "__main__":
    run_demo()
