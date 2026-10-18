#!/usr/bin/env python3
import importlib.util,tempfile,threading,http.client
from pathlib import Path
spec=importlib.util.spec_from_file_location('receiver',Path(__file__).resolve().parents[1]/'diagnostics/receiver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as t:
 s=m.serve(Path(t),'test-token',0);threading.Thread(target=s.serve_forever,daemon=True).start()
 def request(method,path,body=b''):
  c=http.client.HTTPConnection('127.0.0.1',s.server_port,timeout=5);c.request(method,path,body);r=c.getresponse();code=r.status;r.read();c.close();return code
 try:
  assert request('GET','/health')==200
  assert request('POST','/v1/wrong/reports',b'D2R startup diagnostics\n')==404
  assert request('POST',s.upload_path,b'x'*(m.MAX_BYTES+1))==413
  assert request('POST',s.upload_path,b'other content')==400
  assert request('POST',s.upload_path,b'D2R startup diagnostics\nfixture')==202
  files=list(Path(t).glob('*.txt'));assert len(files)==1 and files[0].read_text().endswith('fixture')
  assert request('GET','/'+files[0].name)==404
  assert request('GET',s.upload_path)==404
  assert files[0].stat().st_mode&0o777==0o600
  print('Receiver: real HTTP upload, token enforcement, body limit, private storage and no public reads passed')
 finally:s.shutdown();s.server_close()
