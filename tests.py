import importlib.util,pathlib,unittest,subprocess,sys,json,threading
from http.server import BaseHTTPRequestHandler,HTTPServer
root=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('engine',root/'main.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
def perft(p,d):
 return sum(perft(t,d-1) for m,t in e.legal(p)) if d else 1
def score(fen,d=2,history=()):
 e.nodes=0;e.budget=200000;e.T={};e.H={};e.K={};e.trail=list(history)
 return e.search(e.parse(fen),d,-32000,32000,1)
class Tests(unittest.TestCase):
 def test_perft(self):
  for fen,counts in [(e.START,[20,400,8902,197281]),('r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1',[48,2039,97862]),('8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1',[14,191,2812,43238])]:
   for d,n in enumerate(counts,1):self.assertEqual(perft(e.parse(fen),d),n)
 def test_special(self):
  def legal(f):return {e.uci(m) for m,t in e.legal(e.parse(f))}
  self.assertTrue({'e1c1','e1g1'}<=legal('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1'))
  self.assertNotIn('g5f6',legal('k7/8/8/r4pPK/8/8/8/8 w - f6 0 1'))
  self.assertIn('e5d6',legal('4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1'))
  self.assertEqual({u for u in legal('7k/P7/8/8/8/8/8/7K w - - 0 1') if u[:2]=='a7'},{'a7a8'+q for q in 'qnrb'})
  p=e.play(e.parse('4k3/8/8/8/8/8/8/4K2R w K - 0 1'),(4,5,0))
  self.assertEqual(e.key(p),e.key(e.parse('4k3/8/8/8/8/8/8/5K1R b - - 1 1')))
 def test_terminals(self):
  self.assertEqual(score('7k/6Q1/5K2/8/8/8/8/8 b - - 100 1'),-29999)
  self.assertEqual(score('7k/5K2/6Q1/8/8/8/8/8 b - - 0 1'),0)
  self.assertEqual(score('7k/8/8/8/8/8/8/K7 w - - 0 1'),0)
  self.assertEqual(score(e.START,history=[e.key(e.parse(e.START))]*2),0)
 def test_exchange(self):
  p=e.parse('3r3k/8/8/3p4/8/8/8/3Q3K w - - 0 1')
  self.assertEqual(e.exchange(p,(e.square('d1'),e.square('d5'),0)),-850)
 def test_sacrifice(self):
  fen='5r1k/6pp/4Q2N/8/8/8/8/6K1 w - - 0 1';p=e.parse(fen)
  g=dict(fen=fen,legal_moves=[e.uci(m) for m,t in e.legal(p)])
  self.assertEqual(e.choose(g),'e6g8')
  self.assertEqual(e.choose(g),'e6g8')
 def test_protocol(self):
  fen='7k/5K2/6Q1/8/8/8/8/8 w - - 0 1';p=e.parse(fen);legal=[e.uci(m) for m,t in e.legal(p)];calls=[]
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_POST(self):
    body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));calls.append((self.path,body))
    if len(calls)==1:r=dict(status='your_move',game=1,fen=fen,legal_moves=legal)
    elif self.path=='/move':r=dict(status='over',game=1,outcome='win',reason='checkmate')
    else:r=dict(status='done')
    self.send_response(200);self.end_headers();self.wfile.write(json.dumps(r).encode())
  import os
  with HTTPServer(('127.0.0.1',0),Handler) as server:
   thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   try:
    env=dict(os.environ,MAKEFUN_ENV_URL='http://127.0.0.1:'+str(server.server_port))
    result=subprocess.run([sys.executable,'-P','-s',str(root/'main.py')],env=env,capture_output=True,timeout=10)
    self.assertEqual(result.returncode,0,result.stderr)
    self.assertIn(calls[1][1]['move'],legal)
    self.assertEqual([x[0] for x in calls],['/game','/move','/game'])
   finally:server.shutdown();thread.join()
if __name__=='__main__':unittest.main()
