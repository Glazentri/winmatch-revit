# Optional Revit parameter mapping

Create these through Revit’s shared or project parameter management only if needed for scheduling. The extension does not add or bind parameters.

| Quantity / text | Parameter | Behaviour |
| --- | --- | --- |
| Opening identifier | WM_OpeningID | Instance text, read/write |
| Room | WM_Room | Instance text, read/write |
| Storey / level label | WM_Level | Instance text, read/write |
| Elevation label | WM_Elevation | Instance text, read/write |
| Configuration ID | WM_ConfigId | Instance text, read/write; must match configuration lookup |
| Measurement basis | WM_Basis | Instance text, read/write |
| Notes / handing | WM_Notes, WM_Handing | Instance text, read/write |
| Glazing and glazing layers | WM_Glazing, WM_GlazingLayers | Instance text, read/write |
| Colour | WM_FrameColour | Instance text, read/write |
| BAL / acoustic | WM_BAL, WM_Rw | Instance text, read/write |
| Thermal | WM_UValue, WM_SHGC, WM_ThermalBreak, WM_LowE | Instance text, read/write |
| Screen / bird glass | WM_ScreenType, WM_BirdGlass | Instance text, read/write |
| Reveal | WM_RevealType, WM_RevealMaterial | Instance text, read/write |
| Height and width | WM_Height, WM_Width | Length, instance or type, read only |
| Head and sill | WM_HeadHeight, WM_SillHeight | Length, instance, read only |

Basis strings: Internal window size, Structural opening, Overall including reveals, Internal reveal. If unspecified, nominal family size is exported with a review warning. Structural opening uses rough dimensions where available. See the original extension README for fallback aliases.

Do not infer frame fabrication size from nominal family dimensions. Zero clearances and subsill deductions preserve the raw exported measurement; they are not manufacturer defaults. Only known configuration IDs from the included JSON are accepted. Return writes the chosen values solely to compatible instance text fields and Comments, not actual room, level, position or geometry.
