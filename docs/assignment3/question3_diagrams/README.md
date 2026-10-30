# Question 3.1-3.4 - rendered diagram package

Prepared 30 September 2026 for Itebogeng Eugene Sebapu.

The PDF contains four actual vector diagrams plus explanations and the detailed UC02 use case. Large diagrams use A3/A2 sheets to preserve label readability; explanatory pages use A4. Zoom freely without pixelation, or print large diagram sheets at their native size. PNG files can be inserted into Word; SVG files preserve vector quality; PUML files are editable PlantUML sources.

- 3_1_architecture: users, interfaces, Django services, stores, Kaggle/CDN and the conditional ML component.
- 3_2_use_cases: implemented patient/staff/developer workflows and supporting external system.
- 3_3_classes: seven domain models, manager, inherited auth fields/operations and association multiplicities.
- 3_4_sequence: UC02 browser stroke prediction, ML/fallback, persistence and failure branches.
- Question_3_1_to_3_4.md: complete accompanying answers and source-code references.

Sources follow the inspected code; no trained-model accuracy, lecturer approval or clinical validation is claimed. Training CSVs/model artifacts remain absent. Application behaviour was not changed.

PlantUML rendered all four sources successfully. PNG/SVG exports and rendered PDF pages were visually reviewed. The local portable renderer is under tmp/diagram_tools; no external diagram service received the sources.

To render from the repository root in this workspace:

```powershell
& 'tmp/diagram_tools/jre/jdk-17.0.20.1+1-jre/bin/java.exe' '-Djava.awt.headless=true' -jar tmp/diagram_tools/plantuml.jar -tsvg 'docs/assignment3/question3_diagrams/*.puml'
& 'tmp/diagram_tools/jre/jdk-17.0.20.1+1-jre/bin/java.exe' '-Djava.awt.headless=true' -jar tmp/diagram_tools/plantuml.jar -tpng 'docs/assignment3/question3_diagrams/*.puml'
```

The older full-assignment PDF predates these rendered figures. Use this Question 3 supplement for the requested 3.1-3.4 diagrams. Activity/component/deployment diagrams for 3.5-3.6 are outside this four-subsection supplement.
