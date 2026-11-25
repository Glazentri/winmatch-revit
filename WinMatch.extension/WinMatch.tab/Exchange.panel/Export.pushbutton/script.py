# -*- coding: utf-8 -*-
"""Read host-model windows and doors into WinMatch project JSON."""
import io
import json
import os
from pyrevit import DB, revit, forms, script
import winmatch_exchange as wm

doc = revit.doc
if not doc or doc.IsFamilyDocument:
    forms.alert('Open a Revit project first.', exitscript=True)
try:
    scope = forms.CommandSwitchWindow.show(['All host-model openings', 'Selected host-model openings'], message='Export scope')
    if not scope:
        script.exit()
    phases = list(doc.Phases)
    phase_name = forms.SelectFromList.show([p.Name for p in phases], title='Choose the schedule phase', multiselect=False)
    if not phase_name:
        script.exit()
    phase = next(p for p in phases if p.Name == phase_name)
    elements = wm.opening_elements(doc)
    if scope == 'Selected host-model openings':
        selected = set(e.UniqueId for e in revit.get_selection().elements)
        elements = [e for e in elements if e.UniqueId in selected]
    # Exclude demolished, future and phase-inapplicable elements.
    allowed = [DB.ElementOnPhaseStatus.New, DB.ElementOnPhaseStatus.Existing, DB.ElementOnPhaseStatus.Temporary]
    elements = [e for e in elements if e.GetPhaseStatus(phase.Id) in allowed]
    if not elements:
        forms.alert('No windows or doors in that scope / phase.', exitscript=True)
    config_path = os.path.join(os.path.dirname(wm.__file__), 'configurations.json')
    with io.open(config_path, 'r', encoding='utf-8') as stream:
        configs = json.load(stream)
    project, issues = wm.build_project(doc, elements, phase, configs)
    if not project['rows']:
        forms.alert('No openings could be exported. Check the model families.', exitscript=True)
    output_path = forms.save_file(file_ext='json', default_name='WinMatch-Revit-project.json')
    if not output_path:
        script.exit()
    wm.write_json(output_path, project)
    report_path = os.path.splitext(output_path)[0] + '-review.json'
    report_message = '\nReview report: ' + report_path
    try:
        wm.write_json(report_path, {'pluginVersion': wm.VERSION, 'collected': len(elements), 'exported': len(project['rows']), 'issues': issues})
    except Exception:
        report_message = '\nSeparate report could not be saved. All issues are also embedded in the project JSON.'
    forms.alert('Exported {} opening rows.\n{} review items.\nProject: {}{}\n\nIn WinMatch, use Revit exchange > Import Revit JSON.\nImport replaces the active browser project after confirmation; save it first.'.format(len(project['rows']), len(issues), output_path, report_message), title='WinMatch export complete')
except Exception as error:
    forms.alert('Export could not finish: ' + wm.text(error), title='WinMatch export')
