from .fetcher.file_fetcher import FileFetcher
from .fetcher.requests_fetcher import RequestsFetcher
from .fetcher.sqlite_fetcher import SqliteFetcher
from .generator.file_generator import FileGenerator
from .generator.requests_generator import RequestsGenerator
from .generator.sqlite_generator import SqliteGenerator
from .pipeline import ConnectorPipeline

# from .plugins.confluence_fetcher import ConfluenceFetcher
# from .plugins.confluence_generator import ConfluenceGenerator
# from .plugins.discord_fetcher import DiscordFetcher
# from .plugins.discord_generator import DiscordGenerator
from .plugins.github_fetcher import GithubFetcher
from .plugins.github_generator import GithubGenerator
from .plugins.gmail_fetcher import GmailFetcher
from .plugins.gmail_generator import GmailGenerator
from .plugins.google_calendar_fetcher import GoogleCalendarFetcher
from .plugins.google_calendar_generator import GoogleCalendarGenerator
from .plugins.google_docs_fetcher import GoogleDocsFetcher
from .plugins.google_drive_fetcher import GoogleDriveFetcher
from .plugins.google_drive_generator import GoogleDriveGenerator
from .plugins.google_sheets_fetcher import GoogleSheetsFetcher
from .plugins.google_slides_fetcher import GoogleSlidesFetcher
from .plugins.google_youtube_fetcher import GoogleYoutubeFetcher
from .plugins.google_youtube_generator import GoogleYoutubeGenerator
from .plugins.imap_email_fetcher import ImapEmailFetcher
from .plugins.imap_email_generator import ImapEmailGenerator

# from .plugins.jira_fetcher import JiraFetcher
# from .plugins.jira_generator import JiraGenerator
from .plugins.mongodb_fetcher import MongoDBFetcher
from .plugins.mongodb_generator import MongoDBGenerator
from .plugins.mssql_fetcher import MSSQLFetcher
from .plugins.mssql_generator import MSSQLGenerator
from .plugins.mysql_fetcher import MySQLFetcher
from .plugins.mysql_generator import MySQLGenerator

# from .plugins.naver_search_fetcher import NaverSearchFetcher
# from .plugins.naver_search_generator import NaverSearchGenerator
from .plugins.notion_fetcher import NotionFetcher
from .plugins.notion_generator import NotionGenerator
from .plugins.obsidian_fetcher import ObsidianFetcher
from .plugins.obsidian_generator import ObsidianGenerator
from .plugins.oracle_fetcher import OracleFetcher
from .plugins.oracle_generator import OracleGenerator
from .plugins.postgresql_fetcher import PostgresqlFetcher
from .plugins.postgresql_generator import PostgresqlGenerator
from .plugins.public_youtube_fetcher import YouTubeFetcher
from .plugins.public_youtube_generator import YouTubeGenerator
from .plugins.rss_fetcher import RssFetcher
from .plugins.rss_generator import RssGenerator

# from .plugins.s3_fetcher import S3Fetcher
# from .plugins.s3_generator import S3Generator
# from .plugins.slack_fetcher import SlackFetcher
# from .plugins.slack_generator import SlackGenerator
from .plugins.trafilatura_fetcher import TrafilaturaFetcher
from .plugins.trafilatura_generator import TrafilaturaGenerator

# from .plugins.velog_fetcher import VelogFetcher
# from .plugins.velog_generator import VelogGenerator
from .plugins.wikipedia_fetcher import WikipediaFetcher
from .plugins.wikipedia_generator import WikipediaGenerator

__all__ = [
    "ConnectorPipeline",
    # "ConfluenceFetcher",
    # "ConfluenceGenerator",
    # "DiscordFetcher",
    # "DiscordGenerator",
    "FileFetcher",
    "FileGenerator",
    "GithubFetcher",
    "GithubGenerator",
    "GmailFetcher",
    "GmailGenerator",
    "GoogleCalendarFetcher",
    "GoogleCalendarGenerator",
    "GoogleDocsFetcher",
    "GoogleDriveFetcher",
    "GoogleDriveGenerator",
    "GoogleSheetsFetcher",
    "GoogleSlidesFetcher",
    "GoogleYoutubeFetcher",
    "GoogleYoutubeGenerator",
    "ImapEmailFetcher",
    "ImapEmailGenerator",
    # "JiraFetcher",
    # "JiraGenerator",
    "MongoDBFetcher",
    "MongoDBGenerator",
    "MSSQLFetcher",
    "MSSQLGenerator",
    "MsSQLFetcher",
    "MsSQLGenerator",
    "MySQLFetcher",
    "MySQLGenerator",
    # "NaverSearchFetcher",
    # "NaverSearchGenerator",
    "NotionFetcher",
    "NotionGenerator",
    "ObsidianFetcher",
    "ObsidianGenerator",
    "OracleFetcher",
    "OracleGenerator",
    "PostgresqlFetcher",
    "PostgresqlGenerator",
    "RequestsFetcher",
    "RequestsGenerator",
    "SqliteFetcher",
    "SqliteGenerator",
    "YouTubeFetcher",
    "YouTubeGenerator",
    "RssFetcher",
    "RssGenerator",
    # "S3Fetcher",
    # "S3Generator",
    # "SlackFetcher",
    # "SlackGenerator",
    "TrafilaturaFetcher",
    "TrafilaturaGenerator",
    # "VelogFetcher",
    # "VelogGenerator",
    "WikipediaFetcher",
    "WikipediaGenerator",
]
