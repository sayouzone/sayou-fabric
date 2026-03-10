import json
import os

from sayou.core.base_component import BaseComponent

from ..core.styles import ANALYST_STYLE_SHEET, ANALYST_TYPE_MAPPING


class AnalyticKGRenderer(BaseComponent):
    """
    Renders an interactive 2D Knowledge Graph optimized for deep analysis and topology exploration.

    Agnostic to data domains (Code, Subtitles, Text), it visualizes structural relationships
    using a 'Hub & Spoke' layout. Features interactive filtering, search capabilities,
    and detailed node inspection (Visual IDE/Viewer) to derive insights from complex connections.
    """

    component_name = "AnalyticKGRenderer"

    STYLE_SHEET = ANALYST_STYLE_SHEET

    def render(self, json_path: str, output_path: str = "sayou_analyst_view.html"):
        if not os.path.exists(json_path):
            return

        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        elements = self._build_elements(raw_data)
        self._generate_html(elements, output_path)
        self._log(f"✅ Pure Graph View saved to: {output_path}")

    def render_diff_kg(
        self,
        kg: dict,
        diff_result: dict,
        output_path: str = "sayou_diff_view.html",
        focus_node_id: str | None = None,
        subgraph_depth: int = 3,
    ) -> str:
        """
        KG와 diff 결과를 받아 변경 상태가 오버레이된 인터랙티브 그래프를 생성합니다.

        색상 규칙:
            🔴 modified  — 기존 동작이 변경됨 (가장 위험)
            🟢 added     — 새로 생긴 노드
            ⚫ removed   — 사라진 노드 (원본 KG에서만 존재)
            🟠 impacted  — modified 노드의 CALLS 역방향 영향권
            기본색       — 변경 없음

        focus_node_id가 주어지면 해당 노드 중심으로 subgraph_depth 깊이의
        서브그래프만 추출합니다. None이면 전체 KG를 렌더링합니다.
        """
        # diff 노드 분류
        modified_ids = {
            item.get("orig_node_id") for item in diff_result.get("modified", [])
        }
        added_ids = {item.get("node_id") for item in diff_result.get("added", [])}
        removed_ids = {item.get("node_id") for item in diff_result.get("removed", [])}

        # 영향권 노드 (modified의 역방향 CALLS)
        impacted_ids: set[str] = set()
        for mod_item in diff_result.get("modified", []):
            nid = mod_item.get("orig_node_id")
            if nid:
                for edge in kg.get("edges", []):
                    if edge.get("target") == nid and edge.get("type") in {
                        "sayou:calls",
                        "sayou:maybeCalls",
                    }:
                        impacted_ids.add(edge.get("source", ""))

        # 서브그래프 추출
        if focus_node_id:
            sub_kg = self._extract_subgraph(kg, focus_node_id, subgraph_depth)
        else:
            sub_kg = kg

        elements = self._build_elements(
            sub_kg,
            modified_ids=modified_ids,
            added_ids=added_ids,
            removed_ids=removed_ids,
            impacted_ids=impacted_ids,
        )
        self._generate_html(elements, output_path)
        self._log(f"✅ Diff KG View saved to: {output_path}")
        return output_path

    @staticmethod
    def _extract_subgraph(kg: dict, center_id: str, depth: int) -> dict:
        """
        center_id 노드를 중심으로 양방향 depth 깊이의 서브그래프를 추출합니다.
        """
        from collections import deque

        adj: dict[str, set] = {}
        for edge in kg.get("edges", []):
            s, t = edge.get("source", ""), edge.get("target", "")
            if s and t:
                adj.setdefault(s, set()).add(t)
                adj.setdefault(t, set()).add(s)  # 양방향

        visited: set[str] = set()
        queue = deque([(center_id, 0)])
        while queue:
            nid, d = queue.popleft()
            if nid in visited or d > depth:
                continue
            visited.add(nid)
            for neighbor in adj.get(nid, []):
                if neighbor not in visited:
                    queue.append((neighbor, d + 1))

        nodes = [n for n in kg.get("nodes", []) if n.get("node_id") in visited]
        edges = [
            e
            for e in kg.get("edges", [])
            if e.get("source") in visited and e.get("target") in visited
        ]
        return {"nodes": nodes, "edges": edges}

    def _build_elements(
        self,
        raw_data: dict,
        modified_ids: set | None = None,
        added_ids: set | None = None,
        removed_ids: set | None = None,
        impacted_ids: set | None = None,
    ) -> list:
        modified_ids = modified_ids or set()
        added_ids = added_ids or set()
        removed_ids = removed_ids or set()
        impacted_ids = impacted_ids or set()

        elements = []

        for node in raw_data.get("nodes", []):
            node_id = node.get("node_id")
            attrs = node.get("attributes", {})
            n_cls = node.get("node_class", "unknown")
            cy_type = ANALYST_TYPE_MAPPING.get(n_cls, "unknown")
            label = node.get("friendly_name") or attrs.get("label") or node_id

            diff_status = (
                "modified"
                if node_id in modified_ids
                else (
                    "added"
                    if node_id in added_ids
                    else (
                        "removed"
                        if node_id in removed_ids
                        else "impacted" if node_id in impacted_ids else "normal"
                    )
                )
            )

            cy_data = {
                "id": node_id,
                "label": label,
                "type": cy_type,
                "diff_status": diff_status,
                "code": attrs.get("schema:text", ""),
                "meta": attrs,
            }
            elements.append({"group": "nodes", "data": cy_data})

        for edge in raw_data.get("edges", []):
            e_type = edge.get("type", "relates")
            e_data = {
                "source": edge.get("source"),
                "target": edge.get("target"),
                "edgeType": e_type,
                "label": e_type.split(":")[-1],
                "async_mismatch": edge.get("async_mismatch", False),
                "abstract_parent": edge.get("abstract_parent", False),
            }
            elements.append({"group": "edges", "data": e_data})

        return elements

    def _generate_html(self, elements: list, output_path: str):
        elements_json = (
            json.dumps(elements, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )

        style_json = (
            json.dumps(self.STYLE_SHEET, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace("\u2028", "\\u2028")
        )

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sayou Code Universe</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
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
        var diffStyles = [
            {{ selector: "node[diff_status='modified']",
               style: {{ "background-color": "#d63031", "border-color": "#ff7675", "border-width": 4, "width": 40, "height": 40 }} }},
            {{ selector: "node[diff_status='added']",
               style: {{ "background-color": "#00b894", "border-color": "#55efc4", "border-width": 4 }} }},
            {{ selector: "node[diff_status='removed']",
               style: {{ "background-color": "#2d3436", "border-color": "#636e72", "border-width": 3, "opacity": 0.5 }} }},
            {{ selector: "node[diff_status='impacted']",
               style: {{ "background-color": "#e17055", "border-color": "#fdcb6e", "border-width": 3 }} }},
        ];
        try {{
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: {elements_json},
                style: {style_json}.concat(diffStyles),
                layout: {{
                    name: 'cose',
                    animate: false,
                    nodeRepulsion: 8000,
                    idealEdgeLength: 120,
                    edgeElasticity: 100,
                    gravity: 0.8,
                    numIter: 1000,
                    fit: true,
                    padding: 40,
                }}
            }});
        }} catch(e) {{
            document.getElementById('cy').innerHTML =
                '<div style="color:#ff7675;padding:20px;font-family:monospace">KG 렌더링 오류: ' + e.message + '</div>';
        }}

        function runLayout() {{
            cy.layout({{ name: 'cose', animate: true, animationDuration: 600 }}).run();
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
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
        except Exception as e:
            self._log(f"💥 Failed to write HTML: {e}", level="error")
