import json
import os
from sayou.core.base_component import BaseComponent


class ShowcaseKGRenderer(BaseComponent):
    """
    Renders the Final Stable 3D Knowledge Graph.
    - [Architecture] Removed unstable Post-Processing shaders to fix physics crash.
    - [Visuals] Uses native 'Emissive' materials for Neon aesthetics.
    - [Topology] Distinguishes 'Imports' (Gold/Bright) vs 'Hierarchy' (Dark/Blue).
    """

    component_name = "ShowcaseKGRenderer"

    def render(self, json_path: str, output_path: str = "sayou_showcase_3d.html"):
        if not os.path.exists(json_path):
            return

        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        nodes = []
        links = []
        existing_ids = set()

        for node in raw_data.get("nodes", []):
            node_id = node.get("node_id")
            existing_ids.add(node_id)
            attrs = node.get("attributes", {})
            n_cls = node.get("node_class", "unknown").lower()

            group = "Chunk"
            color = "#4a69bd"
            val = 3

            if "file" in n_cls or "package" in n_cls:
                group = "Document"
                color = "#00d2d3"  # Cyan
                val = 20
            elif "class" in n_cls:
                group = "Header"
                color = "#ff6b81"  # Pink
                val = 12
            elif "method" in n_cls or "function" in n_cls:
                group = "Code"
                color = "#feca57"  # Gold
                val = 6
            elif "library" in n_cls:
                group = "Library"
                color = "#2ed573"  # Green
                val = 10

            label = attrs.get("label") or node.get("friendly_name") or node_id
            if group == "Document":
                label = os.path.basename(attrs.get("sayou:filePath", label))

            clean_attrs = {}
            for k, v in attrs.items():
                if isinstance(v, str) and len(v) > 200:
                    clean_attrs[k] = v[:200] + "..."
                elif not k.startswith("sayou:"):
                    clean_attrs[k] = v

            nodes.append(
                {
                    "id": node_id,
                    "label": label,
                    "group": group,
                    "color": color,
                    "val": val,
                    "attributes": clean_attrs,
                }
            )

        # [2] Edge data processing
        for edge in raw_data.get("edges", []):
            src = edge.get("source")
            tgt = edge.get("target")

            if src in existing_ids and tgt in existing_ids:
                e_type = edge.get("type", "relates")
                is_import = "import" in e_type or "calls" in e_type

                links.append(
                    {
                        "source": src,
                        "target": tgt,
                        "type": e_type,
                        "is_import": is_import,
                    }
                )

        graph_data = {"nodes": nodes, "links": links}
        self._generate_html(graph_data, output_path)
        self._log(f"✅ Final Visual Showcase generated at: {output_path}")

    def _generate_html(self, graph_data, output_path):
        json_str = json.dumps(graph_data)

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sayou Dataverse</title>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <script src="https://unpkg.com/3d-force-graph@1.73.1/dist/3d-force-graph.min.js"></script>
    <style>
        body {{ margin: 0; background-color: #020202; overflow: hidden; font-family: sans-serif; }}
        #graph {{ width: 100%; height: 100vh; }}
        #info {{
            position: absolute; top: 30px; right: 30px; width: 300px;
            background: rgba(15, 20, 30, 0.9);
            border: 1px solid #444; border-left: 4px solid #00d2d3;
            box-shadow: 0 0 20px rgba(0,0,0,0.8);
            color: #fff; padding: 20px; font-size:13px;
            backdrop-filter: blur(5px); display: none; border-radius: 4px; pointer-events: none;
        }}
        .tag {{ display: inline-block; padding: 3px 6px; border-radius: 4px; color: #000; font-weight:bold; font-size:10px; margin-bottom:10px; }}
        h2 {{ margin:0 0 10px 0; font-size:16px; color:#eee; }}
        .row {{ margin-bottom:4px; color:#aaa; border-bottom:1px solid #333; padding-bottom:2px; }}
        .key {{ color:#00d2d3; margin-right:5px; }}
    </style>
</head>
<body>
    <div id="graph"></div>
    <div id="info"></div>

    <script>
        const gData = {json_str};
        const infoDiv = document.getElementById('info');
        
        // [State]
        const highlightNodes = new Set();
        const highlightLinks = new Set();
        let hoverNode = null;
        let isFlying = false;

        // [Init] Big Bang
        gData.nodes.forEach(node => {{
            node.x = Math.random() * 2000 - 1000;
            node.y = Math.random() * 2000 - 1000;
            node.z = Math.random() * 2000 - 1000;
        }});

        // [Graph Init]
        const Graph = ForceGraph3D()(document.getElementById('graph'))
            .graphData(gData)
            .backgroundColor('#050505')
            .showNavInfo(false)
            .nodeLabel(null)
            .cooldownTicks(50);

        // [Physics]
        Graph.d3Force('charge').strength(-100);
        Graph.d3Force('link').distance(link => link.is_import ? 10 : 100);

        // [Visuals]
        Graph
            .nodeThreeObject(node => {{
                let isDimmed = false;
                let isTarget = false;
                if (hoverNode) {{
                    if (hoverNode === node || highlightNodes.has(node)) isTarget = true;
                    else isDimmed = true;
                }}
                const baseColor = node.color;
                const opacity = isDimmed ? 0.1 : 0.9;
                const emissiveInt = isTarget ? 1.5 : (isDimmed ? 0 : 0.6);

                const material = new THREE.MeshPhongMaterial({{
                    color: baseColor,
                    emissive: baseColor,
                    emissiveIntensity: emissiveInt,
                    transparent: true,
                    opacity: opacity,
                    shininess: 90
                }});

                if (node.group === "Document") {{
                    const s = node.val;
                    const geometry = new THREE.BoxGeometry(s, s, s);
                    const edges = new THREE.EdgesGeometry(geometry);
                    const lineMat = new THREE.LineBasicMaterial({{ color: baseColor, transparent:true, opacity: isDimmed ? 0.05 : 0.4 }});
                    const wireframe = new THREE.LineSegments(edges, lineMat);
                    wireframe.add(new THREE.Mesh(new THREE.BoxGeometry(s*0.4, s*0.4, s*0.4), material));
                    return wireframe;
                }}
                else if (node.group === "Header") return new THREE.Mesh(new THREE.OctahedronGeometry(node.val * 0.7), material);
                else return new THREE.Mesh(new THREE.IcosahedronGeometry(node.val * 0.6, 2), material);
            }})
            .linkWidth(link => {{
                if (highlightLinks.has(link)) return 3;
                if (hoverNode && !highlightLinks.has(link)) return 0; 
                return link.is_import ? 1.5 : 0.5;
            }})
            .linkColor(link => {{
                if (highlightLinks.has(link)) return link.is_import ? '#feca57' : '#00d2d3'; 
                return link.is_import ? 'rgba(254, 202, 87, 0.4)' : 'rgba(44, 62, 80, 0.3)';
            }})
            .linkDirectionalParticles(link => highlightLinks.has(link) ? 3 : 0)
            .linkDirectionalParticleWidth(3)
            .onNodeHover(node => {{
                if ((!node && !hoverNode) || (node && hoverNode === node)) return;
                
                highlightNodes.clear(); highlightLinks.clear();
                if (node) {{
                    highlightNodes.add(node);
                    gData.links.forEach(link => {{
                        if (link.source.id === node.id) {{ highlightNodes.add(link.target); highlightLinks.add(link); }}
                        else if (link.target.id === node.id) {{ highlightNodes.add(link.source); highlightLinks.add(link); }}
                    }});
                }}
                hoverNode = node || null;
                requestAnimationFrame(() => {{
                    Graph
                        .nodeThreeObject(Graph.nodeThreeObject())
                        .linkWidth(Graph.linkWidth())
                        .linkColor(Graph.linkColor())
                        .linkDirectionalParticles(Graph.linkDirectionalParticles());
                }});
                
                document.body.style.cursor = node ? 'crosshair' : null;
                if (node) {{
                    infoDiv.style.display = 'block';
                    let html = `<span class='tag' style='background:${{node.color}}'>${{node.group}}</span><h2>${{node.label}}</h2>`;
                    if (node.attributes) {{
                        for (const [k, v] of Object.entries(node.attributes)) {{
                            if(k!=='type') html += `<div class='row'><span class='key'>${{k.split(':').pop()}}:</span> ${{v}}</div>`;
                        }}
                    }}
                    infoDiv.innerHTML = html;
                }} else infoDiv.style.display = 'none';
            }})
            .onNodeClick(node => {{
                if (!node) return;
                isFlying = true;
                const dist = 150;
                const distRatio = 1 + dist/Math.hypot(node.x, node.y, node.z);
                Graph.cameraPosition(
                    {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                    node,
                    2000
                );
                setTimeout(() => {{ isFlying = false; }}, 2000);
            }});

        // [Env]
        const scene = Graph.scene();
        const starsGeo = new THREE.BufferGeometry();
        const pos = new Float32Array(2000 * 3);
        for(let i=0; i<2000*3; i++) pos[i] = (Math.random()-0.5) * 4000;
        starsGeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
        scene.add(new THREE.Points(starsGeo, new THREE.PointsMaterial({{size:2, color:0xffffff, opacity:0.5, transparent:true}})));
        scene.add(new THREE.AmbientLight(0x222222));
        const light = new THREE.DirectionalLight(0xffffff, 1);
        light.position.set(100, 100, 100);
        scene.add(light);

        // [Manual Orbit Engine]
        setInterval(() => {{
            if (hoverNode || isFlying) return;
            const cam = Graph.camera();
            const controls = Graph.controls();
            if (!controls) return;

            const target = controls.target;
            const relX = cam.position.x - target.x;
            const relZ = cam.position.z - target.z;
            const r = Math.sqrt(relX*relX + relZ*relZ);
            let theta = Math.atan2(relZ, relX);
            
            theta += 0.0015;

            const newX = target.x + r * Math.cos(theta);
            const newZ = target.z + r * Math.sin(theta);

            Graph.cameraPosition(
                {{ x: newX, y: cam.position.y, z: newZ }},
                target,
                0
            );
        }}, 15);

    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
