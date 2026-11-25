WINMATCH FOR REVIT — v0.1.0 BETA · EXPERIMENTAL
Limited testing: automated exchange checks only; not yet validated inside Revit.

INSTALL
1. Install full desktop Autodesk Revit on Windows and compatible pyRevit.
   Use pyRevit's IronPython engine, not the CPython engine.
   Target API: Revit 2022–2026. Individual releases are not verified.
   Revit LT, browser viewers, macOS and standalone Python are unsupported.
2. Extract the ZIP; copy WinMatch.extension to %APPDATA%\pyRevit\Extensions.
3. Reload pyRevit or restart Revit. Open a project, find WinMatch Beta.
4. Test a few selected openings in a copy of your model.

REVIT TO WINMATCH
Export to WinMatch > All or Selected host openings > choose phase > save JSON.
Only New, Existing and Temporary openings in the selected phase are collected.
The JSON is a WinMatch version 1 project, with p, rows, quotes and empty docs.
Each row has a stable key, Revit UniqueId and source model identity.
In WinMatch open Export > Revit exchange > Import Revit JSON. This uses project
restore and replaces the active browser project after confirmation. Back it up first.
Review the separate -review.json and the embedded p.revitSource.issues.
Review dimensions, configuration, handing, specifications and allowances.

WINMATCH TO REVIT
Use Download project JSON in Revit exchange (or normal project backup).
Do not use 3D model JSON. Keep the Revit metadata with every row.
In the original Revit model: Import from WinMatch > choose JSON.
The output report shows current / proposed text. Select openings and confirm.
Matching uses source UniqueId plus ProjectInformation.UniqueId, never Mark alone.
The importer writes a [WinMatch] block in built-in instance Comments, preserving
text outside the block, and any EXISTING writable WM_ instance TEXT fields.
Blank mapped values do not clear existing text. No parameters are created.
One transaction applies the selection; failure rolls back. Revit Undo reverses it.
The built-in Mark is not changed. WM_OpeningID is a separate schedule reference.

OPTIONAL PARAMETERS (exact names; instance text fields unless noted)
WM_OpeningID, WM_Room, WM_Level, WM_Elevation, WM_ConfigId, WM_Basis,
WM_Notes, WM_Handing, WM_Glazing, WM_GlazingLayers, WM_FrameColour, WM_BAL,
WM_Rw, WM_UValue, WM_SHGC, WM_ScreenType, WM_ThermalBreak, WM_LowE,
WM_BirdGlass, WM_RevealType, WM_RevealMaterial.
WM_Height and WM_Width must be LENGTH parameters (instance or type), read only.
WM_HeadHeight and WM_SillHeight must be instance LENGTH parameters, read only.
Create optional text project/shared parameters for Windows and Doors through
Revit's parameter management if you need separately schedulable imported data.
Without these fields the Comments summary still works if Comments is writable.
Duplicate same-name parameters are not guessed.

SIZE BASIS
WM_Basis allowed values: Internal window size, Structural opening,
Overall including reveals, Internal reveal.
WM_Height / WM_Width win when present and positive length parameters.
Structural opening uses Rough Height / Rough Width / built-in rough parameters.
Other bases use Height / Width / built-in family size parameters.
No bounding-box dimensions or localized numeric strings are inferred.
Missing WM_Basis defaults to Internal window size with a warning: this is a
nominal family size, NOT evidence of manufacturing frame size. All exported
clearances and subsill deductions are zero to preserve raw values. Check them.
Missing dimensions stay blank. The JSON retains the row for correction.
All exported rows are unconfirmed. Handing is TBC and WinMatch flipped=false.
Revit HandFlipped/FacingFlipped are metadata, not a WinMatch handing mapping.
WM_ConfigId must match lib/configurations.json and the window/door category.
Family names are never guessed into panel layouts. Unknown config stays blank.

SPECIFICATION READ ALIASES (instance then type)
WM_Glazing / WM_GlazingColour / Glazing Colour / Glass Colour / Glazing; WM_GlazingLayers / Glazing Layers;
WM_FrameColour / Frame Colour / Frame Color; WM_BAL / BAL Rating;
WM_Rw / Rw; WM_UValue / U-value; WM_SHGC / SHGC;
WM_ScreenType / Screen Type. Other fields use only the WM_ name above.
Numeric parameters use Revit's formatted text for specifications. Check units.
Only LENGTH dimensions are numerically converted from internal units to mm.
A rating or label alone does not establish compliance.

LIMITATIONS
No linked-model openings, curtain-wall panels, generic model openings,
family placement, type replacement, geometric resizing, automatic handing,
new elements, deletions, live sync or design-option filtering. Check collector
scope if the model contains alternate design options. Special shapes require
manual review; no manufacturing shape or panel geometry is exported.
Return import records sizes in Comments; it does NOT change size parameters.
Actual rooms, levels and elevations are not changed by imported text labels.
Maximum 3000 rows; return JSON limit 20 MB. Unrelated rows without Revit source
metadata and duplicated source identities are rejected, not matched heuristically.
Model copies may retain source identities: verify the target file yourself.
Worksharing, element ownership and read-only fields can prevent updates.
Source code is included for inspection. No network API key or licence server.
Help opens the online guide in your browser; exchange runs locally through files.

Independent extension by Glazentri. Not endorsed by Autodesk or pyRevit.
Autodesk and Revit are trademarks of Autodesk, Inc.
Guide and download: https://winquotes.com.au/revit-plugin.html
