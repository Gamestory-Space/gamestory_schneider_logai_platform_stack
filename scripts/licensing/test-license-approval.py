#!/usr/bin/env python3
import hashlib,importlib.util,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('approval',Path(__file__).with_name('verify-license-approval.py'));gate=importlib.util.module_from_spec(s);s.loader.exec_module(gate)
class ApprovalTests(unittest.TestCase):
    def model(self):return {'owner':'Gamestory Ltd','status':'approved','sha256':hashlib.sha256(b'fixture').hexdigest(),'approvedBy':'fixture reviewer','approvedAt':'2026-10-04T12:00:00+00:00'}
    def test_explicit_approval_of_exact_text_passes(self):self.assertEqual(gate.validate(b'fixture',self.model())['status'],'approved')
    def test_pending_draft_cannot_be_published(self):
        model=self.model();model['status']='pending-review'
        with self.assertRaises(ValueError):gate.validate(b'fixture',model)
    def test_changed_text_cannot_reuse_approval(self):
        with self.assertRaises(ValueError):gate.validate(b'changed',self.model())
    def test_missing_identity_or_timezone_fails(self):
        for key,value in [('approvedBy',None),('approvedAt','2026-10-04T12:00:00')]:
            model=self.model();model[key]=value
            with self.assertRaises(ValueError):gate.validate(b'fixture',model)
if __name__=='__main__':unittest.main()
