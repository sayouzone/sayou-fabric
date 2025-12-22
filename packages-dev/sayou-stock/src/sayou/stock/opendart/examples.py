import os
import sys

module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)

from opendart import OpenDartCrawler


def main():
    crawler = OpenDartCrawler()
    data = crawler.fetch(code="005930")

if __name__ == "__main__":
    main()