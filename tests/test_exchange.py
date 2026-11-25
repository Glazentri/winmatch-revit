"""Offline tests for the original IronPython-compatible exchange logic.

The Autodesk DB API is stubbed. These tests are not host/engine validation.
"""
import copy
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]

class StorageType:
    String = "String"
    Double = "Double"
    Integer = "Integer"
class BuiltInParameter:
    ALL_MODEL_INSTANCE_COMMENTS = "Comments"
    FAMILY_WIDTH_PARAM = "Family Width"
    FAMILY_ROUGH_WIDTH_PARAM = "Family Rough Width"
class BuiltInCategory:
    OST_Doors = "Door"
    OST_Windows = "Window"
class Param:
    def __init__(self, val, storage=StorageType.String, read_only=False, length=False):
        self.val = val
        self.StorageType = storage
        self.IsReadOnly = read_only
        self.HasValue = val is not None
        self.Definition = types.SimpleNamespace(GetDataType=lambda: "Length" if length else "Other")
    def AsString(self): return self.val
    def AsValueString(self): return str(self.val)
    def AsDouble(self): return self.val
    def Set(self, val):
        if self.IsReadOnly: return False
        self.val = val
        return True

class Element:
    def __init__(self, params=None, kind="Window"):
        self.params = params or {}
        self.Category = types.SimpleNamespace(Id=kind)
        self.Symbol = types.SimpleNamespace(GetParameters=lambda name: [], get_Parameter=lambda key: None)
    def GetParameters(self, key):
        val=self.params.get(key)
        return val if isinstance(val,list) else [val] if val is not None else []
    def get_Parameter(self, key): return self.params.get(key)

class TxStatus:
    Started="Started"
    Committed="Committed"
    RolledBack="RolledBack"
class Tx:
    def __init__(self, doc, label):
        self.doc=doc
        doc.transaction=self
        self.status=None
        self.original=[]
    def Start(self):
        self.status=TxStatus.Started
        self.original=[(p,p.val) for el in self.doc.elements.values() for p in el.params.values() if isinstance(p,Param)]
        return self.status
    def GetStatus(self): return self.status
    def Commit(self):
        self.status=TxStatus.Committed
        return self.status
    def RollBack(self):
        for param,val in self.original: param.val=val
        self.status=TxStatus.RolledBack

db=types.SimpleNamespace(StorageType=StorageType, BuiltInCategory=BuiltInCategory, BuiltInParameter=BuiltInParameter, ElementId=lambda x:x,
    FamilyInstance=Element, UnitUtils=types.SimpleNamespace(ConvertFromInternalUnits=lambda value,_type: value*304.8),
    UnitTypeId=types.SimpleNamespace(Millimeters="mm"), SpecTypeId=types.SimpleNamespace(Length="Length"),
    Transaction=Tx,TransactionStatus=TxStatus)
autodesk=types.ModuleType('Autodesk')
revit=types.ModuleType('Autodesk.Revit')
revit.DB=db
autodesk.Revit=revit
sys.modules['Autodesk']=autodesk
sys.modules['Autodesk.Revit']=revit
sys.path.insert(0,str(ROOT/'WinMatch.extension'/'lib'))
wm=importlib.import_module('winmatch_exchange')

class Document:
    def __init__(self, model_id, elements):
        self.ProjectInformation=types.SimpleNamespace(UniqueId=model_id)
        self.elements=elements
    def GetElement(self, uid): return self.elements.get(uid)

def example():
    return json.loads((ROOT/'examples'/'example-project.json').read_text())

class TestExchange(unittest.TestCase):
    def test_fixture_valid(self):
        p=wm.load_project(str(ROOT/'examples'/'example-project.json'))
        self.assertEqual(p['rows'][0]['height'],1200)
        self.assertEqual(len(p['rows']),2)

    def load_temp(self, p):
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'project.json'
            wm.write_json(str(file),p)
            return wm.load_project(str(file))
    def test_round_trip_utf8(self):
        p=example()
        p['rows'][0]['notes']='Glazing – café'
        self.assertEqual(self.load_temp(p)['rows'][0]['notes'],'Glazing – café')
    def test_duplicate_and_missing_id_rejected(self):
        p=example()
        p['rows'][1]['revit']['uniqueId']=p['rows'][0]['revit']['uniqueId']
        with self.assertRaisesRegex(ValueError,'Duplicate or missing'):
            self.load_temp(p)
        p=example()
        p['rows'][0]['key']=''
        with self.assertRaisesRegex(ValueError,'Duplicate or missing'):
            self.load_temp(p)
    def test_rejects_unrelated_data_and_nested_text(self):
        p=example()
        p['rows'][0].pop('revit')
        with self.assertRaisesRegex(ValueError,'source metadata'):self.load_temp(p)
        p=example()
        p['rows'][0]['notes']={'not':'text'}
        with self.assertRaisesRegex(ValueError,'nested'):self.load_temp(p)
    def test_comments_replace_and_escape_delimiters(self):
        row=example()['rows'][0]
        row['notes']='Preserve literal [WinMatch] text'
        block=wm.summary_block(row)
        self.assertIn('(WinMatch) text',block)
        current='Before\n[WinMatch]\nOld\n[/WinMatch]\nAfter'
        new=wm.replace_block(current,block)
        self.assertTrue(new.startswith('Before\n'))
        self.assertTrue(new.endswith('\nAfter'))
        self.assertNotIn('Old',new)
        self.assertEqual(wm.replace_block(new,block),new)
    def test_explicit_dimension_overrides_and_positive_length_only(self):
        e=Element({'WM_Width':Param(3,StorageType.Double,length=True),'Width':Param(6,StorageType.Double,length=True)})
        self.assertAlmostEqual(wm.dimension(e,'Width','Internal window size'),914.4)
        e.params['WM_Width']=Param(-3,StorageType.Double,length=True)
        self.assertAlmostEqual(wm.dimension(e,'Width','Internal window size'),1828.8)
        e.params['Width']=Param(6,StorageType.Double,length=False)
        self.assertIsNone(wm.dimension(e,'Width','Internal window size'))
        e.params['Rough Width']=Param(7,StorageType.Double,length=True)
        self.assertAlmostEqual(wm.dimension(e,'Width','Structural opening'),2133.6)
    def test_import_matches_model_and_category_only_text(self):
        p=example()
        first=p['rows'][0]
        first['notes']='Reviewed'
        first['frameColour']='White'
        first['room']=''
        params={'Comments':Param('Existing note'),'WM_Notes':Param('Old'), 'WM_Room':Param('Existing room'), 'WM_FrameColour':Param('old',read_only=True),'WM_Height':Param(2,StorageType.Double,length=True)}
        e=Element(params)
        doc=Document(p['p']['revitSource']['modelId'],{first['revit']['uniqueId']:e})
        plans,skipped=wm.plan_import(doc,p)
        self.assertEqual(len(plans),1)
        self.assertEqual(len(skipped),1)
        self.assertEqual({c['name'] for c in plans[0]['changes']},{'Comments','WM_Notes'})
        wm.apply_import(doc,plans)
        self.assertIn('Existing note',params['Comments'].val)
        self.assertEqual(params['WM_Notes'].val,'Reviewed')
        self.assertEqual(params['WM_Room'].val,'Existing room')
        self.assertEqual(params['WM_FrameColour'].val,'old')
        self.assertEqual(params['WM_Height'].val,2)
        self.assertEqual(doc.transaction.GetStatus(),TxStatus.Committed)
        with self.assertRaisesRegex(ValueError,'Source model'):
            wm.plan_import(Document('another',{}),p)
        e.Category.Id='Door'
        plans,skipped=wm.plan_import(doc,p)
        self.assertEqual(plans,[])
        self.assertTrue(any('category mismatch' in s for s in skipped))
    def test_failed_transaction_rolls_back_mock_changes(self):
        e=Element({'WM_Notes':Param('Old'),'Comments':Param('Original',read_only=True)})
        doc=Document('test',{'element':e})
        plans=[{'changes':[{'name':'WM_Notes','parameter':e.params['WM_Notes'],'new':'New'},{'name':'Comments','parameter':e.params['Comments'],'new':'Does not write'}]}]
        with self.assertRaises(ValueError):wm.apply_import(doc,plans)
        self.assertEqual(e.params['WM_Notes'].val,'Old')
        self.assertEqual(doc.transaction.GetStatus(),TxStatus.RolledBack)
    def test_config_lookup(self):
        configs=json.loads((ROOT/'WinMatch.extension'/'lib'/'configurations.json').read_text())
        self.assertGreater(len(configs),30)
        self.assertTrue(all(v.get('group') and v.get('code') for v in configs.values()))

if __name__=='__main__':
    unittest.main()
