#!/usr/bin/env python3
"""Local write-only diagnostic receiver; expose through an HTTPS tunnel."""
import argparse,collections,hmac,http.server,json,os,threading,time,uuid
from pathlib import Path
MAX_BYTES=262144
class Receiver(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args): pass  # Do not leak the secret URL or report content.
    def reply(self,status,data=b''):
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        self.reply(200,b'{"ok":true}') if self.path=='/health' else self.reply(404)
    def do_POST(self):
        if not hmac.compare_digest(self.path,self.server.upload_path):return self.reply(404)
        try:size=int(self.headers.get('Content-Length','0'))
        except ValueError:return self.reply(400)
        if not 0<size<=MAX_BYTES or self.headers.get('Transfer-Encoding'):return self.reply(413)
        self.connection.settimeout(15)
        try:raw=self.rfile.read(size);text=raw.decode('utf-8')
        except (OSError,UnicodeError):return self.reply(400)
        if len(raw)!=size or not text.startswith('D2R startup diagnostics\n'):return self.reply(400)
        with self.server.guard:
            now=time.monotonic()
            while self.server.recent and now-self.server.recent[0]>60:self.server.recent.popleft()
            if len(self.server.recent)>=12:return self.reply(429)
            self.server.recent.append(now)
            report=self.server.directory/(time.strftime('%Y%m%d-%H%M%S',time.gmtime())+'-'+uuid.uuid4().hex[:8]+'.txt')
            fd=os.open(report,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as out:out.write(raw)
            for old in sorted(self.server.directory.glob('*.txt'))[:-100]:old.unlink()
        self.reply(202,json.dumps({'received':report.name}).encode())
def serve(directory,token,port):
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    server=http.server.ThreadingHTTPServer(('127.0.0.1',port),Receiver)
    server.directory=directory;server.upload_path='/v1/'+token+'/reports';server.guard=threading.Lock();server.recent=collections.deque()
    return server
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args();config=json.loads(a.config.read_text())
    serve(Path(config['directory']),config['token'],config.get('port',8974)).serve_forever()
