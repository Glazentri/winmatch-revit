# WinMatch for Revit — pyRevit Extension

**Open-source window and door schedule exchange between Autodesk Revit and WinMatch.**

[WinMatch by Glazentri](https://winquotes.com.au) · v0.1.0 beta · MIT · Windows

The original November 2026 Revit tool exports selected or all host-model window and door instances to the WinMatch project format. Review the schedule in WinMatch, then return reviewed data into existing instance text properties in Revit.

> **Experimental beta:** The target API range is Revit 2022–2026, using a compatible version of pyRevit with IronPython. The code is included and offline logic has been tested; no Revit host version has yet been independently verified. Test in a copy of a model.

## Installation

1. Install desktop Autodesk Revit for Windows and a compatible [pyRevit release](https://github.com/pyrevitlabs/pyRevit/releases). Use pyRevit's IronPython engine.
2. Download this repository or its release ZIP. Extract the complete `WinMatch.extension` folder.
3. In pyRevit settings, register the **parent directory containing** `WinMatch.extension` under custom extension directories (or copy it to an already registered extension directory). See [pyRevit's official extension installation steps](https://docs.pyrevitlabs.io/get-started/install-extensions/).
4. Reload pyRevit or restart Revit. Open a project and find the **WinMatch Beta** tab.
5. Start with a small number of selected windows or doors. See [the full installation and round-trip guide](docs/workflow.md).

No account token, API key, installer executable or network service is required for the add-in's file exchange. Opening the online Help link is optional.

## Features

| Feature | Behaviour |
| --- | --- |
| Export all or selected openings | Host-model Window and Door family instances, in a chosen phase |
| Dimensions | Explicit length parameters in millimetres; raw source basis retained |
| Identifiers | UniqueId and model identity, plus user-facing opening ID |
| Schedule fields | Room, level, elevation, type and configuration when mapped |
| Specifications | Existing text parameters for glazing, frame colour, BAL, Rw, U-value, SHGC, screens and other attributes |
| Quality review | Warnings and separate review JSON; no guessed panel geometry |
| Return | Preview and select text changes, confirm one reversible Revit transaction |
| Matching | Model identity and element UniqueId; never Mark alone |
| Revit geometry | No edits, placement, deletion or type changes |

The exporter uses WinMatch **v1 project JSON** (with `version`, `p`, `rows`, `quotes`, `docs`), not the newer BIM Studio schema or 3D export JSON. The return importer updates only built-in instance Comments and existing writable WM_ instance **text** parameters. Dimensions in comments are reference notes, not resize commands.

## Repository

- `WinMatch.extension/` — full installable pyRevit directory with ribbon bundles, icons, commands, engine and configuration lookup.
- [Field mapping](docs/fields.md) — optional instance text and length parameters.
- [Workflow and limitations](docs/workflow.md) — the original installation and exchange instructions, plus test checklist.
- `examples/` — fictional exchange and review JSON for understanding the format.
- `tests/` — Python logic tests with stubbed Revit API objects; no Revit dependency for the tests.

## Tests

Run from the repository root with Python 3:

```sh
python -m unittest discover -s tests -v
```

These tests verify file parsing, comments, dimensions, identity checks, field type filtering and mocked transaction behaviour. They are **not** proof of compatibility inside Autodesk Revit or IronPython. A host smoke-test checklist is in [the workflow guide](docs/workflow.md). See [verification status](docs/verification.md).

## Licence and credits

Original WinMatch code by Adrian Woolley / Glazentri is released under the [MIT licence](LICENSE). Autodesk Revit and pyRevit must be installed separately; neither is bundled. Autodesk/Revit are trademarks of Autodesk, Inc. This is independent and not endorsed by Autodesk or the pyRevit project.

The original hosted download and guide are at [winquotes.com.au/revit-plugin.html](https://winquotes.com.au/revit-plugin.html). This release keeps the legacy project format and command source; it does not replace or merge the newer WinMatch BIM Studio add-ins.
