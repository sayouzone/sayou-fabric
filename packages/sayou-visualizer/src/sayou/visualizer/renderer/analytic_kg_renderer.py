import json
import os

from sayou.core.base_component import BaseComponent


class AnalyticKGRenderer(BaseComponent):
    """
    Renders an interactive 2D Knowledge Graph optimized for deep analysis and topology exploration.

    Agnostic to data domains (Code, Subtitles, Text), it visualizes structural relationships
    using a 'Hub & Spoke' layout. Features interactive filtering, search capabilities,
    and detailed node inspection (Visual IDE/Viewer) to derive insights from complex connections.
    """

    component_name = "AnalyticKGRenderer"

    STYLE_SHEET = [
        # [Global Nodes]
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
        # [File Node]
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
        # [Class Node]
        {
            "selector": "node[type='class']",
            "style": {
                "shape": "diamond",
                "background-color": "#8e44ad",
                "width": 40,
                "height": 40,
            },
        },
        # [Method/Function]
        {
            "selector": "node[type='method'], node[type='function']",
            "style": {
                "shape": "ellipse",
                "background-color": "#e67e22",
                "width": 25,
                "height": 25,
            },
        },
        # [Code Chunk]
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
        # [Package/Library]
        {
            "selector": "node[type='library'], node[type='package']",
            "style": {
                "shape": "hexagon",
                "background-color": "#16a085",
                "width": 50,
                "height": 50,
            },
        },
        # [Edges]
        {
            "selector": "edge",
            "style": {
                "width": 1,
                "curve-style": "bezier",
                "opacity": 0.6,
                "arrow-scale": 1,
            },
        },
        # 1. Structure Line (contains) -> Gray Dashed Line (Skeleton)
        {
            "selector": "edge[edgeType='sayou:contains']",
            "style": {
                "line-color": "#7f8c8d",
                "target-arrow-color": "#7f8c8d",
                "target-arrow-shape": "circle",
                "width": 1.5,
                "line-style": "dashed",
                "opacity": 0.7,
            },
        },
        # 2. Logic Line (imports) -> Cyan Dashed Line (Flow)
        {
            "selector": "edge[edgeType='sayou:imports']",
            "style": {
                "line-color": "#00d2d3",
                "target-arrow-color": "#00d2d3",
                "target-arrow-shape": "triangle",
                "line-style": "dashed",
                "width": 2,
                "opacity": 0.9,
            },
        },
        # 3. Inheritance Line (inherits) -> Red Solid Line
        {
            "selector": "edge[edgeType='sayou:inherits']",
            "style": {
                "line-color": "#ff6b6b",
                "target-arrow-color": "#ff6b6b",
                "target-arrow-shape": "triangle",
                "width": 3,
            },
        },
        # [Interaction]
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

    def render(self, json_path: str, output_path: str = "sayou_analyst_view.html"):
        if not os.path.exists(json_path):
            return

        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        elements = []

        # 1. Nodes (No Parents logic)
        for node in raw_data.get("nodes", []):
            node_id = node.get("node_id")
            attrs = node.get("attributes", {})
            n_cls = node.get("node_class", "unknown").lower()

            # Type Check
            cy_type = "unknown"
            if "file" in n_cls:
                cy_type = "file"
            elif "class" in n_cls:
                cy_type = "class"
            elif "method" in n_cls:
                cy_type = "method"
            elif "function" in n_cls:
                cy_type = "function"
            elif "library" in n_cls:
                cy_type = "library"
            elif "code" in n_cls:
                cy_type = "code_block"

            # Labeling
            label = attrs.get("label") or node.get("friendly_name") or node_id
            if cy_type == "file":
                label = os.path.basename(attrs.get("sayou:filePath", label))
            elif cy_type == "class":
                label = attrs.get("meta:class_name", label)
            elif cy_type in ["method", "function"]:
                label = attrs.get("function_name", label)

            # Code Text
            code_text = attrs.get("schema:text", "")
            cy_data = {
                "id": node_id,
                "label": label,
                "type": cy_type,
                "code": code_text,
                "meta": attrs,
            }
            elements.append({"group": "nodes", "data": cy_data})

        # 2. Edges
        for edge in raw_data.get("edges", []):
            elements.append(
                {
                    "group": "edges",
                    "data": {
                        "source": edge.get("source"),
                        "target": edge.get("target"),
                        "edgeType": edge.get("type", "relates"),
                        "label": edge.get("type", "").split(":")[-1],
                    },
                }
            )

        self._generate_html(elements, output_path)
        self._log(f"✅ Pure Graph View saved to: {output_path}")

    def _generate_html(self, elements: list, output_path: str):
        style_json = json.dumps(self.STYLE_SHEET)
        elements_json = json.dumps(elements)

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sayou Code Universe</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
    <script src="https://unpkg.com/layout-base/layout-base.js"></script>
    <script src="https://unpkg.com/cose-base/cose-base.js"></script>
    <script src="https://unpkg.com/cytoscape-fcose/cytoscape-fcose.js"></script>
    
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; background: #1e272e; color: #dcdde1; overflow: hidden; display: flex; }}
        #cy {{ flex-grow: 1; height: 100vh; }}
        
        /* Sidebar & Controls */
        #controls {{
            position: absolute; top: 20px; left: 20px; z-index: 100;
            background: rgba(47, 54, 64, 0.95); padding: 15px; border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3); border: 1px solid #4b6584; width: 280px;
        }}
        #tooltip {{
            position: absolute;
            display: none;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 11px;
            pointer-events: none;
            z-index: 1000;
            border: 1px solid #00d2d3;
        }}
        .search-group {{ display: flex; gap: 5px; margin-bottom: 10px; }}
        input[type="text"] {{ flex-grow: 1; background: #222; border: 1px solid #57606f; color: white; padding: 6px; border-radius: 4px; }}
        button {{ background: #4b6584; border: none; color: white; padding: 6px 12px; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background: #00d2d3; color: #000; }}

        #sidebar {{
            width: 450px; height: 100vh; background: #2f3640; border-left: 1px solid #4b6584;
            display: flex; flex-direction: column; transform: translateX(450px); transition: 0.3s;
            position: absolute; right: 0; top: 0; z-index: 200; box-shadow: -5px 0 15px rgba(0,0,0,0.5);
        }}
        #sidebar.open {{ transform: translateX(0); }}
        .header {{ padding: 20px; border-bottom: 1px solid #4b6584; background: #252a34; }}
        .node-title {{ font-size: 18px; color: #fff; font-weight: bold; margin: 0; }}
        .content {{ flex-grow: 1; overflow-y: auto; padding: 0; background: #282c34; }}
        pre {{ margin: 0; }}
    </style>
</head>
<body>
    <div id="controls">
        <div style="font-weight:bold; color:#00d2d3; margin-bottom:10px;">Sayou Graph</div>
        <div class="search-group">
            <input type="text" id="search-input" placeholder="Search..." onkeyup="if(event.key === 'Enter') searchNode()">
            <button onclick="searchNode()">🔍</button>
        </div>
        <div style="margin-bottom: 10px; display: flex; gap: 5px;">
            <button id="btn-label" class="active" onclick="toggleLabels()" style="flex:1;">Labels ON</button>
            <button id="btn-line" class="active" onclick="toggleLines()" style="flex:1;">Lines ON</button>
        </div>
        <div style="font-size:11px; color:#aaa; border-top:1px solid #57606f; padding-top:10px;">
            <button onclick="runLayout()">Re-Layout</button>
            <button onclick="resetView()">Reset Cam</button>
        </div>
    </div>

    <div id="cy"></div>
    <div id="tooltip"></div>

    <div id="sidebar">
        <div class="header">
            <h2 class="node-title" id="sb-title">Details</h2>
            <div id="sb-desc" style="font-size:12px; color:#aaa; margin-top:5px;"></div>
        </div>
        <div class="content">
            <pre><code id="sb-code" class="language-python"></code></pre>
        </div>
    </div>

    <script>
        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {elements_json},
            style: {style_json},
            layout: {{ 
                name: 'fcose',
                quality: 'proof',
                nodeSeparation: 75,
                idealEdgeLength: edge => edge.data('edgeType') === 'sayou:contains' ? 50 : 200,
                animate: false 
            }}
        }});

        function runLayout() {{
            cy.layout({{ name: 'fcose', animate: true, animationDuration: 800 }}).run();
        }}

        // [Search]
        function searchNode() {{
            var query = document.getElementById('search-input').value.toLowerCase();
            if(!query) return;
            cy.elements().removeClass('found');
            var found = cy.nodes().filter(ele => ele.data('label').toLowerCase().includes(query));
            if(found.length > 0) {{
                found.addClass('found');
                // cy.animate({{ fit: {{ eles: found, padding: 50 }}, duration: 500 }});
                // cy.center(found);
            }}
        }}

        function resetView() {{
            cy.elements().removeClass('highlighted faded found');
            document.getElementById('sidebar').classList.remove('open');
            cy.animate({{ fit: {{ padding: 50 }} }});
        }}

        // 1. Label Toggle (ON/OFF)
        var labelsVisible = true;
        function toggleLabels() {{
            labelsVisible = !labelsVisible;
            var btn = document.getElementById('btn-label');
            
            if (labelsVisible) {{
                cy.nodes().removeClass('no-label');
                btn.innerText = "Labels ON";
                btn.style.background = "#4b6584";
                btn.style.color = "white";
            }} else {{
                cy.nodes().addClass('no-label');
                btn.innerText = "Labels OFF";
                btn.style.background = "#2f3542";
                btn.style.color = "#747d8c";
            }}
        }}

        // 2. Line Toggle (ON/OFF)
        var linesVisible = true;
        function toggleLines() {{
            linesVisible = !linesVisible;
            var btn = document.getElementById('btn-line');
            // var edges = cy.edges('[edgeType="sayou:contains"]');
            var edges = cy.edges();
            
            if (linesVisible) {{
                edges.removeClass('hidden-edge');
                btn.innerText = "Lines ON";
                btn.style.background = "#4b6584";
                btn.style.color = "white";
            }} else {{
                edges.addClass('hidden-edge');
                btn.innerText = "Lines OFF";
                btn.style.background = "#2f3542";
                btn.style.color = "#747d8c";
            }}
        }}

        // [Click Interaction]
        cy.on('tap', 'node', function(evt){{
            var node = evt.target;
            
            // Highlight neighbors
            cy.elements().removeClass('highlighted faded');
            var neighbors = node.neighborhood().add(node);
            cy.elements().addClass('faded');
            neighbors.removeClass('faded').addClass('highlighted');

            // Sidebar
            document.getElementById('sidebar').classList.add('open');
            document.getElementById('sb-title').innerText = node.data('label');
            document.getElementById('sb-desc').innerText = (node.data('type') || 'Unknown').toUpperCase() + ' | ' + node.id();
            
            var codeArea = document.getElementById('sb-code');
            codeArea.innerText = node.data('code') || JSON.stringify(node.data('meta'), null, 2);
            hljs.highlightElement(codeArea);
        }});

        cy.on('tap', function(evt){{
            if(evt.target === cy) resetView();
        }});

        var tooltip = document.getElementById('tooltip');

        cy.on('mouseover', 'node', function(evt){{
            var node = evt.target;
            var label = node.data('label') || node.data('id');
            
            tooltip.style.display = 'block';
            tooltip.innerText = label;
            tooltip.style.left = evt.renderedPosition.x + 'px';
            // var pos = node.renderedPosition();
            // tooltip.style.left = (pos.x + 10) + 'px';
            // tooltip.style.top = (pos.y + 10) + 'px';
        }});

        cy.on('mousemove', function(evt){{
            tooltip.style.left = (evt.renderedPosition.x + 15) + 'px';
            tooltip.style.top = (evt.renderedPosition.y + 15) + 'px';
        }});

        cy.on('mouseout', 'node', function(){{
            tooltip.style.display = 'none';
        }});
    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
