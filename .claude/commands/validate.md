---
description: "Run Druck standards validation on this project"
tools: [bash]
model: ["claude-3-5-sonnet-20240620", "glm-4.6", "*"]
---

Run Druck standards validation on this project.

Execute:
```bash
python -m pytest tests/ -v
```

This checks:
- Directory structure compliance
- Excel files (one-sheet rule)
- PDF reports existence
- LaTeX sources
- Documentation completeness
- Progress log recency
