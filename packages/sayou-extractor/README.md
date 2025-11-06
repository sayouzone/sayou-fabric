# Sayou Refinery (sayou_refinery)



**A pluggable framework for refining raw Data Atoms into a coherent Knowledge Graph (KG) for advanced LLM applications.**

---

## 💡 Why Sayou Refinery?

`sayou_refinery` solves the core problem of organizing messy, disconnected data into a structured KG. This KG acts as a "map" for RAG pipelines, allowing LLMs to retrieve accurate, context-aware data, minimizing hallucinations and costs.

- **Pluggable Architecture:** Bring your own data store (Neo4j, JSON) or refinement logic.
- **Ontology-Driven:** Ensures all data conforms to your central schema.
- **Focused Responsibility:** Does one job well: **Refine & Link**. No connectors, no embedding logic.

## 🚀 Quick Start (v.0.0.1)

### 1. Installation

```bash
pip install sayou-refinery
```

### 2. Usage (Example)
sayou_refinery is a library. You import it into your own project. See the full code in examples/subway_refinery/run.py.

``` Python
# your_project/run.py
from sayou.refinery.pipeline import Pipeline
from sayou.refinery.schema.manager import OntologyManager
from sayou.refinery.schema.validator import SchemaValidator
from sayou.refinery.graph.builder import KnowledgeGraphBuilder
from sayou.refinery.linker.default_linker import DefaultLinker
from sayou.refinery.store.json_store import JsonStore

# 1. Import your custom domain logic
from your_project.my_refiner import MyDomainRefiner

# 2. Prepare components (Explicit Injection)
schema_manager = OntologyManager()
validator = SchemaValidator()
refiner = MyDomainRefiner() # Your logic
builder = KnowledgeGraphBuilder()
linker = DefaultLinker()
store = JsonStore()

# 3. Create and configure the pipeline
pipeline = Pipeline(
    schema_manager=schema_manager,
    validator=validator,
    refiner=refiner,
    builder=builder,
    linker=linker,
    store=store
)

pipeline.initialize(
    ontology_path="path/to/your_schema.json",
    filepath="output/my_kg.json" # Config for JsonStore
)

# 4. Load your data atoms
my_atoms = [...] # Load your DataAtom objects

# 5. Run
pipeline.run(my_atoms)
```

## 🏗️ Core Concepts
- Data Atom: The standard input unit. (Schema/structure explanation)

- Refiner (BaseRefiner): Cleans, aggregates, or transforms atoms. (e.g., averaging subway data)

- Linker (BaseLinker): Establishes relationships between nodes.

- Store (BaseStore): The output driver (JSON, Neo4j, etc.).

## 🤝 Contributing
We welcome contributions! Please read our CONTRIBUTING.md (추후 추가) file for details on how to submit pull requests.

## 📜 License
This project is licensed under the MIT License.