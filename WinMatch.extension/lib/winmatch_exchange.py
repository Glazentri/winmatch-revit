# -*- coding: utf-8 -*-
"""WinMatch exchange v0.1.0. Run inside pyRevit's IronPython engine.

Export is read-only. Import writes reviewed instance text fields only.
No network calls, geometry edits, family creation or type parameter writes.
"""
from __future__ import print_function
import io
import json
import math
import re
from datetime import datetime
from Autodesk.Revit import DB

VERSION = '0.1.0-beta-experimental'
MAX_ROWS = 3000
BASES = ['Internal window size', 'Structural opening', 'Overall including reveals', 'Internal reveal']
TEXT_FIELDS = {
    'glazing': ['WM_Glazing', 'WM_GlazingColour', 'Glazing Colour', 'Glass Colour', 'Glazing'],
    'glazingLayers': ['WM_GlazingLayers', 'Glazing Layers'],
    'frameColour': ['WM_FrameColour', 'Frame Colour', 'Frame Color'],
    'bal': ['WM_BAL', 'BAL Rating'],
    'acoustic': ['WM_Rw', 'Rw'],
    'u': ['WM_UValue', 'U-value'],
    'shgc': ['WM_SHGC', 'SHGC'],
    'screenType': ['WM_ScreenType', 'Screen Type'],
    'thermal': ['WM_ThermalBreak'],
    'lowE': ['WM_LowE'],
    'birdGlass': ['WM_BirdGlass'],
    'revealType': ['WM_RevealType'],
    'revealMaterial': ['WM_RevealMaterial']
}
# Return writes only existing instance TEXT parameters with these explicit names.
IMPORT_FIELDS = dict((key, names[0]) for key, names in TEXT_FIELDS.items())
IMPORT_FIELDS.update({'id': 'WM_OpeningID', 'room': 'WM_Room', 'floor': 'WM_Level',
                      'elevation': 'WM_Elevation', 'config': 'WM_ConfigId',
                      'basis': 'WM_Basis', 'notes': 'WM_Notes', 'handing': 'WM_Handing'})
try:
    string_type = unicode
except NameError:
    string_type = str


def text(value):
    return '' if value is None else string_type(value)


def param(element, name):
    # Ambiguous duplicate parameter names are never guessed.
    ps = list(element.GetParameters(name))
    return ps[0] if len(ps) == 1 else None


def parameter_text(p):
    if p is None or not p.HasValue:
        return ''
    if p.StorageType == DB.StorageType.String:
        return p.AsString() or ''
    return p.AsValueString() or ''


def read_text(element, names):
    for source in [element, element.Symbol]:
        for name in names:
            value = parameter_text(param(source, name))
            if value.strip():
                return value.strip()
    return ''


def millimetres(value):
    return round(DB.UnitUtils.ConvertFromInternalUnits(value, DB.UnitTypeId.Millimeters), 3)


def is_length(p):
    try:
        return p.Definition.GetDataType() == DB.SpecTypeId.Length
    except Exception:
        return False


def dimension(element, axis, basis):
    # Explicit WM override wins; positive length parameters only. No bounding boxes.
    explicit = ['WM_' + axis]
    names = explicit + ([('Rough ' + axis)] if basis == 'Structural opening' else [axis])
    built_in = ('FAMILY_ROUGH_' if basis == 'Structural opening' else 'FAMILY_') + axis.upper() + '_PARAM'
    sources = [(source, True) for source in [element, element.Symbol]] + [(source, False) for source in [element, element.Symbol]]
    for source, explicit_only in sources:
        candidates = [param(source, name) for name in (explicit if explicit_only else names[len(explicit):])]
        bip = getattr(DB.BuiltInParameter, built_in, None)
        if bip is not None and not explicit_only:
            candidates.append(source.get_Parameter(bip))
        for p in candidates:
            if p is not None and p.HasValue and p.StorageType == DB.StorageType.Double and is_length(p):
                value = millimetres(p.AsDouble())
                if not math.isnan(value) and not math.isinf(value) and value > 0:
                    return value
    return None


def model_id(doc):
    return doc.ProjectInformation.UniqueId


def opening_elements(doc):
    result = []
    for category in [DB.BuiltInCategory.OST_Windows, DB.BuiltInCategory.OST_Doors]:
        result.extend(list(DB.FilteredElementCollector(doc).OfCategory(category).WhereElementIsNotElementType()))
    return sorted([e for e in result if isinstance(e, DB.FamilyInstance)], key=lambda e: e.UniqueId)


def room_name(element, phase):
    values = []
    for prop in ['Room', 'FromRoom', 'ToRoom']:
        try:
            room = getattr(element, prop)[phase]
            if room:
                number = parameter_text(room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER))
                name = parameter_text(room.get_Parameter(DB.BuiltInParameter.ROOM_NAME))
                value = (number + ' ' + name).strip()
                if value and value not in values:
                    values.append(value)
        except Exception:
            pass
    return ' / '.join(values)


def export_row(doc, element, phase, configs):
    issues = []
    kind = 'Door' if element.Category.Id == DB.ElementId(DB.BuiltInCategory.OST_Doors) else 'Window'
    mark = read_text(element, ['WM_OpeningID']) or parameter_text(element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK))
    if not mark:
        mark = ('D' if kind == 'Door' else 'W') + '-' + element.UniqueId[-8:]
        issues.append('Missing Mark; generated identifier requires review.')
    supplied_basis = read_text(element, ['WM_Basis'])
    basis = supplied_basis if supplied_basis in BASES else 'Internal window size'
    if not supplied_basis:
        issues.append('Nominal family dimensions exported unchanged; verify frame / rough-opening datum.')
    elif supplied_basis not in BASES:
        issues.append('Unknown WM_Basis; nominal family dimensions exported unchanged.')
    h, w = dimension(element, 'Height', basis), dimension(element, 'Width', basis)
    if h is None or w is None:
        issues.append('Missing positive length parameter for height / width; dimensions left blank.')
    cfg = read_text(element, ['WM_ConfigId'])
    config = configs.get(cfg)
    if not config or ('Door' in config['group']) != (kind == 'Door'):
        cfg = ''
        issues.append('Choose WinMatch configuration; family name and flip flags do not establish panel layout / handing.')
    room = read_text(element, ['WM_Room']) or room_name(element, phase)
    if not room:
        issues.append('Room unresolved in selected phase.')
    level = doc.GetElement(element.LevelId)
    floor = read_text(element, ['WM_Level']) or (level.Name if level else '')
    if not floor:
        issues.append('Level unresolved.')
    family_name = element.Symbol.Family.Name
    type_name = parameter_text(element.Symbol.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM))
    row = {'key': 'revit-' + element.UniqueId, 'id': mark, 'kind': kind, 'room': room,
           'floor': floor, 'elevation': read_text(element, ['WM_Elevation']), 'config': cfg,
           'qty': 1, 'height': h if h is not None else '', 'width': w if w is not None else '',
           'basis': basis, 'clearH': 0, 'clearW': 0, 'subsill': 0,
           'subsillMode': 'Not required', 'revealType': 'TBC', 'bottomReveal': 'No' if kind == 'Door' else 'TBC',
           'confirmed': False, 'flipped': False, 'handing': 'TBC', 'glazing': 'TBC', 'glazingLayers': 'TBC',
           'revit': {'uniqueId': element.UniqueId, 'family': family_name, 'type': type_name,
                     'modelId': model_id(doc), 'phase': phase.Name,
                     'handFlipped': bool(element.HandFlipped), 'facingFlipped': bool(element.FacingFlipped),
                     'dimensionSource': 'Revit length parameters; no bounding-box inference'}}
    for key, names in TEXT_FIELDS.items():
        value = read_text(element, names)
        if value:
            row[key] = value
    for key, name in [('head', 'WM_HeadHeight'), ('sill', 'WM_SillHeight')]:
        p = param(element, name)
        if p is not None and p.HasValue and p.StorageType == DB.StorageType.Double and is_length(p):
            row[key] = millimetres(p.AsDouble())
    note = read_text(element, ['WM_Notes'])
    source_note = 'Revit: ' + family_name + ' / ' + type_name
    row['notes'] = note if source_note in note.splitlines() else (note + '\n' if note else '') + source_note
    row['revit']['issues'] = issues
    return row, issues


def build_project(doc, elements, phase, configs):
    if len(elements) > MAX_ROWS:
        raise ValueError('WinMatch supports up to 3000 opening rows. Select a smaller set.')
    rows, issues, seen = [], [], {}
    for element in elements:
        try:
            row, warnings = export_row(doc, element, phase, configs)
            rows.append(row)
            seen.setdefault(row['id'].strip().lower(), []).append(row)
            issues.extend([{'id': row['id'], 'uniqueId': element.UniqueId, 'message': w} for w in warnings])
        except Exception as error:
            issues.append({'id': '', 'uniqueId': element.UniqueId, 'message': 'Not exported: ' + text(error)})
    for group in seen.values():
        if len(group) > 1:
            for row in group:
                row['revit']['issues'].append('Duplicate identifier; unique Revit source identity retained.')
                issues.append({'id': row['id'], 'uniqueId': row['revit']['uniqueId'], 'message': 'Duplicate identifier.'})
    return {'version': 1, 'p': {'project': doc.Title, 'revision': '', 'measurementBasis': 'Internal window size',
            'clearH': 0, 'clearW': 0, 'notes': 'Imported from Revit. Review dimensions, configuration, handing and specifications.',
            'revitSource': {'modelId': model_id(doc), 'title': doc.Title, 'pluginVersion': VERSION,
                            'exportedAt': datetime.utcnow().isoformat() + 'Z', 'phase': phase.Name,
                            'scope': 'Host-model openings in selected phase; no links', 'collected': len(elements),
                            'exported': len(rows), 'issues': issues}},
            'rows': rows, 'quotes': {}, 'docs': [], 'procurement': [], 'preorder': {}}, issues


def write_json(path, data):
    with io.open(path, 'w', encoding='utf-8') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2))


def load_project(path):
    import os
    if os.path.getsize(path) > 20 * 1024 * 1024:
        raise ValueError('JSON exceeds 20 MB. Export a copy without attachments.')
    with io.open(path, 'r', encoding='utf-8-sig') as stream:
        project = json.load(stream)
    if not isinstance(project, dict) or project.get('version') != 1 or not isinstance(project.get('p'), dict):
        raise ValueError('Choose WinMatch PROJECT JSON, not 3D model JSON.')
    rows = project.get('rows')
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError('Invalid opening list or more than 3000 rows.')
    keys, sources = set(), set()
    for row in rows:
        if not isinstance(row, dict) or row.get('kind') not in ['Window', 'Door'] or not isinstance(row.get('revit'), dict):
            raise ValueError('Every row must retain its Revit source metadata. Remove unrelated new rows from a copy first.')
        key, source = row.get('key', ''), row['revit'].get('uniqueId', '')
        if not key or key in keys or not source or source in sources:
            raise ValueError('Duplicate or missing source identity. Duplicated schedule rows cannot update one Revit element.')
        keys.add(key)
        sources.add(source)
        if any(isinstance(row.get(field), (list, dict)) for field in IMPORT_FIELDS):
            raise ValueError('Invalid nested value in opening fields.')
    return project


def summary_block(row):
    fields = [('ID', row.get('id')), ('Room', row.get('room')), ('Level', row.get('floor')),
              ('Elevation', row.get('elevation')), ('Configuration ID', row.get('config')),
              ('Input H x W mm', '{} x {}'.format(row.get('height', ''), row.get('width', ''))),
              ('Basis', row.get('basis'))]
    fields.extend([(key, row.get(key)) for key in TEXT_FIELDS])
    fields.append(('Notes', row.get('notes')))
    clean = lambda v: text(v).replace('[WinMatch]', '(WinMatch)').replace('[/WinMatch]', '(/WinMatch)')
    return '[WinMatch]\n' + '\n'.join(label + ': ' + clean(value) for label, value in fields if value not in [None, '']) + '\n[/WinMatch]'


def replace_block(old, block):
    pattern = r'\[WinMatch\][\s\S]*?\[/WinMatch\]'
    return re.sub(pattern, lambda match: block, old, count=1) if re.search(pattern, old) else (old.rstrip() + '\n\n' + block).strip()


def plan_import(doc, project):
    source = project['p'].get('revitSource', {})
    if source.get('modelId') != model_id(doc):
        raise ValueError('Source model does not match the open model. No Mark-based fallback is used.')
    plans, skipped = [], []
    for row in project['rows']:
        uid = row['revit']['uniqueId']
        element = doc.GetElement(uid)
        if not element or not isinstance(element, DB.FamilyInstance) or row['revit'].get('modelId') != model_id(doc):
            skipped.append(row.get('id', uid) + ': source opening unavailable / wrong model.')
            continue
        expected = DB.BuiltInCategory.OST_Doors if row['kind'] == 'Door' else DB.BuiltInCategory.OST_Windows
        if element.Category.Id != DB.ElementId(expected):
            skipped.append(row.get('id', uid) + ': category mismatch.')
            continue
        changes = []
        # Comments is a built-in instance field. Preserve all text outside our block.
        candidates = [('Comments', element.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS), None)]
        candidates.extend([(name, param(element, name), row.get(field)) for field, name in IMPORT_FIELDS.items()])
        for name, p, value in candidates:
            if p is None or p.IsReadOnly or p.StorageType != DB.StorageType.String:
                continue
            old = p.AsString() or ''
            new = replace_block(old, summary_block(row)) if name == 'Comments' else text(value)
            # Blanks do not erase existing mapped values.
            if new and new != old:
                changes.append({'name': name, 'parameter': p, 'old': old, 'new': new})
        if changes:
            plans.append({'row': row, 'element': element, 'changes': changes})
        else:
            skipped.append(row.get('id', uid) + ': no changed writable instance text fields.')
    return plans, skipped


def apply_import(doc, plans):
    """Atomic transaction: any error rolls back the whole reviewed selection."""
    tx = DB.Transaction(doc, 'Import WinMatch schedule data')
    try:
        if tx.Start() != DB.TransactionStatus.Started:
            raise ValueError('Could not start a Revit transaction.')
        for plan in plans:
            for change in plan['changes']:
                if not change['parameter'].Set(change['new']):
                    raise ValueError('Could not write ' + change['name'])
        status = tx.Commit()
        if status != DB.TransactionStatus.Committed:
            raise ValueError('Revit did not commit the transaction: ' + text(status))
    except Exception:
        if tx.GetStatus() == DB.TransactionStatus.Started:
            tx.RollBack()
        raise
