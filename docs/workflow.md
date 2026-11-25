# Installation, exchange and host QA

## Install on Windows

Follow the official [pyRevit custom extension installation guide](https://docs.pyrevitlabs.io/get-started/install-extensions/) and add the folder containing `WinMatch.extension` to the custom extension directory list. Reload. Revit LT, browser viewers, standalone Python and macOS are not supported.

The extension was designed for the Revit 2022–2026 API and the IronPython engine. Host compatibility remains unverified.

## Export from Revit

1. Open a copy of the project and choose a phase.
2. Select **Export to WinMatch** in the WinMatch Beta tab.
3. Choose all host-model openings or a selection. The collector includes Window and Door family instances in New, Existing or Temporary phase status.
4. Save the JSON and review report.
5. Back up the current WinMatch project. Import the Revit project JSON into WinMatch and confirm replacement if prompted.
6. Review dimension basis, allowances, subsill and reveal requirements, handing, configuration and specifications before confirming any schedule.

## Return from WinMatch

Export standard WinMatch project JSON after reviewing the schedule. Keep every row's Revit source metadata. In the original model, select **Import from WinMatch**, load the JSON, review the old and proposed text, select openings and approve. One transaction applies all selected changes; use Revit Undo to revert.

Only comments and existing writable instance text fields are updated. Comments preserve text outside the WinMatch block. Blank mapped fields do not erase text. Built-in Mark does not change. The add-in does not create parameters, update length parameters, or resize elements.

## Manual host validation checklist

- Confirm the ribbon loads in the intended Revit/pyRevit/IronPython versions.
- Export one window and one door in a test file. Check dimensions, phase, IDs and review warnings.
- Compare exported units against known instance and type length parameters.
- Confirm missing configuration stays blank; flip flags do not become assumed handing.
- Return data against the same project. Check the current/proposed preview, existing Comments and writable WM_ text parameters.
- Confirm a different model is rejected; duplicate/missing identities are rejected.
- Verify built-in Mark, geometry and type remain unchanged; use Undo and confirm comments revert.
- Repeat with read-only fields, grouped families and a workshared model where relevant.

## Limits

Read the complete original notes in [WinMatch.extension/README.txt](../WinMatch.extension/README.txt). Linked windows/doors, curtain-wall panels, generic openings, design-option filtering, geometric editing, family placement, type replacement and live sync are not implemented. Maximum 3,000 rows; return JSON limit 20 MB. Model copies can retain source identity; choose the correct model yourself. Optional shared/project properties must exist before import. Review compliance and procurement dimensions separately.
