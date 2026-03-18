# =============================================================================
# Sayou Fabric — Media Domain Ontology
#
# Node types, edge types, and property keys for media knowledge graphs.
# Consumed by: sayou-connector (YouTube fetcher), sayou-wrapper (video adapters)
# =============================================================================


class SayouClassMedia:
    """Node type labels for the media domain."""

    VIDEO = "sayou:Video"
    VIDEO_SEGMENT = "sayou:VideoSegment"


class SayouPredicateMedia:
    """Edge type labels for the media domain."""

    # Reserved for future media-specific relationships.
    pass


class SayouAttributeMedia:
    """Property key constants for the media domain."""

    START_TIME = "sayou:startTime"
    END_TIME = "sayou:endTime"
    DURATION = "sayou:duration"
