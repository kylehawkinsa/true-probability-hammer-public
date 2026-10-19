import sys,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tph_core import password_hash,password_valid,decimal_odds,implied_probability,expected_value,gate,compare,normalize_name
from odds_worker import parse_events

class AuthAndMath(unittest.TestCase):
 def test_password_hash(self):
  h=password_hash('this is a complex passphrase')
  self.assertTrue(password_valid('this is a complex passphrase',h))
  self.assertFalse(password_valid('wrong',h))
 def test_odds_math(self):
  self.assertAlmostEqual(implied_probability(-150),.6)
  self.assertAlmostEqual(implied_probability(120),1/2.2)
  self.assertAlmostEqual(expected_value(.60,120),.32)
 def test_name_normalization(self):
  self.assertEqual(normalize_name("J.T. Miller"),normalize_name("JT Miller"))
 def fixture(self):
  t=datetime(2026,10,18,19,0,tzinfo=timezone.utc)
  z=lambda dt:dt.isoformat()
  f={'event_id':'tested-game','game_start_utc':z(t+timedelta(hours=1)),
     'player_name':'Example Test Player','line':2.5,'prob_over':.6,
     'forecast_created_utc':z(t-timedelta(hours=1)),
     'model_version':'test-fixture','model_status':'approved','data_verified':True}
  q={'event_id':'tested-game','game_start_utc':f['game_start_utc'],
     'player_name':f['player_name'],'line':2.5,'side':'Over','book':'draftkings','american_odds':120,
     'source':'the-odds-api','price_captured_at_utc':z(t-timedelta(minutes=2)),
     'book_last_update_utc':z(t-timedelta(minutes=3))}
  return t,f,q
 def test_research_only_model_blocked(self):
  t,f,q=self.fixture();f['model_status']='research'
  self.assertFalse(gate(f,q,now=t)[0])
 def test_missing_model_verified_blocked(self):
  t,f,q=self.fixture();f['data_verified']=False
  self.assertFalse(gate(f,q,now=t)[0])
 def test_stale_quote_blocked(self):
  t,f,q=self.fixture();q['book_last_update_utc']=(t-timedelta(minutes=40)).isoformat()
  self.assertFalse(gate(f,q,now=t)[0])
 def test_poststart_quote_blocked(self):
  t,f,q=self.fixture();q['game_start_utc']=(t-timedelta(minutes=1)).isoformat()
  self.assertFalse(gate(f,q,now=t)[0])
 def test_mismatched_player_blocked(self):
  t,f,q=self.fixture();q['player_name']='Different Guy'
  self.assertFalse(gate(f,q,now=t)[0])
 def test_no_source_blocked(self):
  t,f,q=self.fixture();q['source']='manual'
  self.assertFalse(gate(f,q,now=t)[0])
 def test_valid_paired_market(self):
  t,f,q=self.fixture()
  other=q.copy();other['side']='Under';other['american_odds']=-140
  r=compare(f,q,other,now=t)
  self.assertTrue(r['eligible']);self.assertAlmostEqual(r['ev_per_dollar'],.32)
 def test_missing_paired_market(self):
  t,f,q=self.fixture()
  r=compare(f,q,q,now=t)
  self.assertFalse(r['eligible'])
 def test_parser_real_market_schema(self):
  t,f,q=self.fixture()
  event={'id':'tested-game','commence_time':f['game_start_utc'],
    'bookmakers':[{'key':'draftkings','last_update':q['book_last_update_utc'],
      'markets':[{'key':'player_shots_on_goal','outcomes':[
       {'name':'Over','description':'Example Test Player','point':2.5,'price':120},
       {'name':'Under','description':'Example Test Player','point':2.5,'price':-140}]}]}]}
  rows=parse_events([event],t)
  self.assertEqual(len(rows),2)
  self.assertTrue(all(x['source']=='the-odds-api' for x in rows))
 def test_parser_ignores_unsupported_book_and_market(self):
  t,f,q=self.fixture()
  e={'id':'tested-game','commence_time':f['game_start_utc'],'bookmakers':[{'key':'pinnacle','markets':[{'key':'player_shots_on_goal','outcomes':[]}]}]}
  self.assertEqual(parse_events([e],t),[])
if __name__=='__main__':unittest.main()
