from sayou.core.ontology import SayouClass

HIDDEN_ATTR_PREFIXES = ["sayou:", "meta:", "schema:"]

# =========================================================
# 1. 3D Showcase Styles (Original Design Restored)
# =========================================================
SHOWCASE_STYLE_MAP = {
    "default": {"group": "Chunk", "color": "#4a69bd", "val": 3},
    # [Original Design Colors]
    SayouClass.FILE: {"group": "Document", "color": "#00d2d3", "val": 20},  # Cyan
    SayouClass.CLASS: {"group": "Header", "color": "#ff6b81", "val": 12},  # Pink
    SayouClass.METHOD: {"group": "Code", "color": "#feca57", "val": 6},  # Gold
    SayouClass.FUNCTION: {"group": "Code", "color": "#feca57", "val": 6},  # Gold
    SayouClass.LIBRARY: {"group": "Library", "color": "#2ed573", "val": 10},  # Green
    # [New] YouTube Domain (Compatible Theme)
    SayouClass.VIDEO: {"group": "Video", "color": "#e84118", "val": 40},  # Deep Red
    SayouClass.VIDEO_SEGMENT: {
        "group": "Segment",
        "color": "#dcdde1",
        "val": 4,
    },  # Gray
}

# 동적 크기 계산 규칙
DYNAMIC_SIZING_RULES = {
    SayouClass.VIDEO_SEGMENT: {
        "attr_start": "sayou:startTime",
        "attr_end": "sayou:endTime",
        "base_val": 4,
        "scale_factor": 0.5,
    }
}

# =========================================================
# 2. 2D Analyst Styles (Original Design + Interactions Restored)
# =========================================================
ANALYST_TYPE_MAPPING = {
    SayouClass.FILE: "file",
    SayouClass.CLASS: "class",
    SayouClass.METHOD: "method",
    SayouClass.FUNCTION: "function",
    SayouClass.LIBRARY: "library",
    SayouClass.CODE_BLOCK: "code_block",
    SayouClass.VIDEO: "video",
    SayouClass.VIDEO_SEGMENT: "segment",
}

ANALYST_STYLE_SHEET = [
    # [Global]
    {
        "selector": "node",
        "style": {
            "label": "data(label)",
            "color": "#ecf0f1",
            "font-size": "10px",
            "text-valign": "center",
            "text-halign": "center",
            "text-wrap": "wrap",
            "text-max-width": "100px",
            "background-color": "#95a5a6",
            "border-width": 1,
            "border-color": "#7f8c8d",
        },
    },
    # [Original Node Shapes/Colors]
    {
        "selector": "node[type='file']",
        "style": {
            "shape": "rectangle",
            "background-color": "#2c3e50",
            "width": 60,
            "height": 60,
            "font-size": "12px",
            "font-weight": "bold",
            "border-width": 2,
            "border-color": "#00d2d3",
        },
    },
    {
        "selector": "node[type='class']",
        "style": {
            "shape": "diamond",
            "background-color": "#8e44ad",
            "width": 40,
            "height": 40,
        },
    },
    {
        "selector": "node[type='method'], node[type='function']",
        "style": {
            "shape": "ellipse",
            "background-color": "#e67e22",
            "width": 25,
            "height": 25,
        },
    },
    {
        "selector": "node[type='code_block']",
        "style": {
            "shape": "round-rectangle",
            "background-color": "#7f8c8d",
            "width": 15,
            "height": 15,
            "label": "",
        },
    },
    {
        "selector": "node[type='library']",
        "style": {
            "shape": "hexagon",
            "background-color": "#16a085",
            "width": 50,
            "height": 50,
        },
    },
    # [New YouTube Nodes]
    {
        "selector": "node[type='video']",
        "style": {
            "shape": "rectangle",
            "background-color": "#c0392b",
            "width": 80,
            "height": 80,
            "border-width": 4,
            "border-color": "#e74c3c",
        },
    },
    {
        "selector": "node[type='segment']",
        "style": {
            "shape": "round-rectangle",
            "background-color": "#bdc3c7",
            "width": 40,
            "height": 20,
            "color": "#2c3e50",
            "font-size": "8px",
        },
    },
    # [Original Edges]
    {
        "selector": "edge",
        "style": {
            "width": 1,
            "curve-style": "bezier",
            "opacity": 0.6,
            "arrow-scale": 1,
        },
    },
    {
        "selector": "edge[edgeType='sayou:contains']",
        "style": {
            "line-color": "#7f8c8d",
            "target-arrow-shape": "circle",
            "line-style": "dashed",
            "width": 1.5,
            "opacity": 0.7,
        },
    },
    {
        "selector": "edge[edgeType='sayou:imports']",
        "style": {
            "line-color": "#00d2d3",
            "target-arrow-shape": "triangle",
            "line-style": "dashed",
            "width": 2,
            "opacity": 0.9,
        },
    },
    {
        "selector": "edge[edgeType='sayou:inherits']",
        "style": {
            "line-color": "#ff6b6b",
            "target-arrow-shape": "triangle",
            "width": 3,
        },
    },
    {
        "selector": "edge[edgeType='sayou:next']",
        "style": {
            "line-color": "#f39c12",
            "target-arrow-shape": "triangle",
            "width": 2,
        },
    },
    # =========================================================
    # [CRITICAL FIX] Restored Interaction Styles
    # =========================================================
    {
        "selector": ".highlighted",
        "style": {
            "background-color": "#f1c40f",
            "line-color": "#f1c40f",
            "target-arrow-color": "#f1c40f",
            "opacity": 1,
            "z-index": 999,
        },
    },
    {
        "selector": ".faded",
        "style": {"opacity": 0.05, "label": ""},
    },
    {
        "selector": ".found",
        "style": {
            "border-width": 4,
            "border-color": "#e056fd",
            "background-color": "#e056fd",
        },
    },
    {
        "selector": "node.no-label",
        "style": {
            "text-opacity": 0,
            "text-background-opacity": 0,
            "text-border-opacity": 0,
        },
    },
    {
        "selector": "edge.hidden-edge",
        "style": {"display": "none"},
    },
]
