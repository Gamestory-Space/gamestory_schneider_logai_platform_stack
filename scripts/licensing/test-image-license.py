#!/usr/bin/env python3
import importlib.util,io,json,tarfile,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('license_gate',Path(__file__).with_name('verify-image-license.py'))
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
EXPECTED={'LICENSE':b'Test fixture only: approved distribution terms.','NOTICE':b'Third-party software retains its own licences.'}

class LicenseTests(unittest.TestCase):
    def check(self,later=None,labels=None,initial=None):
        with tempfile.TemporaryDirectory() as tmp:
            archive=Path(tmp)/'image.tar'
            with tarfile.open(archive,'w') as tar:
                def add(name,data):
                    info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
                add('manifest.json',json.dumps([{'Config':'config.json','Layers':['one.tar','two.tar']}]).encode())
                add('config.json',json.dumps({'config':{'Labels':gate.LABELS if labels is None else labels}}).encode())
                for name,files in [('one.tar',initial if initial is not None else {gate.FILES[k]:v for k,v in EXPECTED.items()}),('two.tar',later or {})]:
                    buf=io.BytesIO()
                    with tarfile.open(fileobj=buf,mode='w') as layer:
                        for path,data in files.items():
                            info=tarfile.TarInfo(path);info.size=len(data);layer.addfile(info,io.BytesIO(data))
                    add(name,buf.getvalue())
            return gate.inspect_archive(archive,EXPECTED)
    def test_correct_metadata_and_exact_approved_files(self):self.assertEqual(self.check()['status'],'passed')
    def test_missing_label(self):
        with self.assertRaises(ValueError):self.check(labels={})
    def test_missing_license(self):
        with self.assertRaises(ValueError):self.check(initial={gate.FILES['NOTICE']:EXPECTED['NOTICE']})
    def test_modified_license(self):
        with self.assertRaises(ValueError):self.check({gate.FILES['LICENSE']:b'changed'})
    def test_deleted_license_in_later_layer(self):
        with self.assertRaises(ValueError):self.check({gate.PREFIX+'.wh.GAMESTORY-LICENSE.txt':b''})
    def test_deleted_parent_directory(self):
        with self.assertRaises(ValueError):self.check({'.wh.licenses':b''})
    def test_opaque_directory_removes_old_licence(self):
        with self.assertRaises(ValueError):self.check({gate.PREFIX+'.wh..wh..opq':b''})

if __name__=='__main__':unittest.main()
