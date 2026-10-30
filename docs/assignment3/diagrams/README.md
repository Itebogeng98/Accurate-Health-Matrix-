# PlantUML sources

Eight editable diagrams accompany sections 3.1–3.6 and 4.2. Java, PlantUML and Graphviz were not found on PATH; no PlantUML JAR was found in the inspected project. Rendered exports and visual readability verification are **Evidence not available**. Sources use Smetana so Graphviz is not required by the rendering command.

From the repository root, after installing Java and obtaining an official PlantUML JAR locally:

```powershell
java -jar C:\tools\plantuml.jar -tsvg docs/assignment3/diagrams/*.puml
java -jar C:\tools\plantuml.jar -tpng docs/assignment3/diagrams/*.puml
```

Open each SVG, check labels, arrows and multiplicities at 100% zoom, and insert/export figures for submission. Command execution and syntax validation by PlantUML remain outstanding; source structure has been checked only. Diagram files use repository identifiers, not claims of deployment or lecturer approval.
