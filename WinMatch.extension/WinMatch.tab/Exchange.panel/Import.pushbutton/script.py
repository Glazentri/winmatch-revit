# -*- coding: utf-8 -*-
"""Preview and update matching Revit instance text fields from WinMatch."""
from pyrevit import revit, forms, script
import winmatch_exchange as wm

doc = revit.doc
if not doc or doc.IsFamilyDocument or doc.IsReadOnly:
    forms.alert('Open a writable Revit project first.', exitscript=True)


class OpeningChange(forms.TemplateListItem):
    @property
    def name(self):
        return self.item['row']['id'] + ' | ' + ', '.join(c['name'] for c in self.item['changes'])


try:
    path = forms.pick_file(file_ext='json')
    if not path:
        script.exit()
    project = wm.load_project(path)
    plans, skipped = wm.plan_import(doc, project)
    output = script.get_output()
    output.print_md('## WinMatch import preview')
    output.print_md('Existing instance text fields only. Dimensions are recorded in Comments, not applied to geometry. Built-in Mark, types, location, level and handing are unchanged.')
    if skipped:
        output.print_table(table_data=[[s] for s in skipped], columns=['Skipped / unchanged'])
    if not plans:
        forms.alert('No writable changes found. See the preview report.', exitscript=True)
    output.print_table(table_data=[[p['row']['id'], c['name'], c['old'], c['new']] for p in plans for c in p['changes']], columns=['Opening', 'Parameter', 'Current', 'Proposed'])
    selected = forms.SelectFromList.show([OpeningChange(p) for p in plans], title='Choose openings to update (see preview report)', multiselect=True, button_name='Review selected changes')
    if not selected:
        script.exit()
    chosen = [p.item if isinstance(p, OpeningChange) else p for p in selected]
    count = sum(len(p['changes']) for p in chosen)
    if not forms.alert('Apply {} text-field changes to {} matched openings?\n\nReview Current / Proposed in the output report first.\nThis writes Comments and any existing WM_ instance text fields.\nNo dimensions, geometry, types, built-in Mark or placement will change.\nUndo in Revit reverses this transaction.'.format(count, len(chosen)), yes=True, no=True, title='Apply WinMatch data?'):
        script.exit()
    wm.apply_import(doc, chosen)
    forms.alert('Updated {} existing openings in one Revit transaction.\n{} skipped / unchanged. See the preview report.\nUse Undo to reverse.'.format(len(chosen), len(skipped)), title='WinMatch import complete')
except Exception as error:
    forms.alert('Import could not finish: ' + wm.text(error), title='WinMatch import')
