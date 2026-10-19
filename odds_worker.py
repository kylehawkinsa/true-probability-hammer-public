"""Real Odds API NHL player SOG fetcher. API key + subscription/market coverage required.

No probabilistic forecasts are computed here. Only observed DK/FD offered quotes
are saved. Run with secrets on GitHub Actions, not from the web browser.
"""
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
from datetime import datetime,timezone
import requests
from storage import table_append
from tph_core import SUPPORTED_BOOKS, SUPPORTED_LINES, utc

BASE='https://api.the-odds-api.com/v4/sports/icehockey_nhl'

def get_json(session,url,params):
    response=session.get(url,params=params,timeout=25)
    response.raise_for_status()
    return response.json()


def parse_events(events, collected_at):
    """Pure transform to normalized price rows. Fail rather than invent timestamps."""
    output=[]
    for event in events:
        event_id=event.get('id')
        start=event.get('commence_time')
        if not event_id or not start:continue
        try:utc(start)
        except (TypeError,ValueError):continue
        for book in event.get('bookmakers',[]):
            bookname=book.get('key','').lower()
            if bookname not in SUPPORTED_BOOKS:continue
            for market in book.get('markets',[]):
                if market.get('key')!='player_shots_on_goal':continue
                timestamp=market.get('last_update') or book.get('last_update')
                if not timestamp:continue
                try:utc(timestamp)
                except (TypeError,ValueError):continue
                for outcome in market.get('outcomes',[]):
                    side=outcome.get('name')
                    player=outcome.get('description','')
                    if side not in ('Over','Under') or not player:continue
                    try:
                        line=float(outcome['point']);price=int(outcome['price'])
                        if line not in SUPPORTED_LINES or abs(price)<100 or price==0:continue
                    except (KeyError,TypeError,ValueError):continue
                    output.append({'event_id':event_id,'game_start_utc':utc(start).isoformat(),
                         'player_name':player,'line':line,'side':side,'book':bookname,
                         'american_odds':price,'price_captured_at_utc':utc(collected_at).isoformat(),
                         'book_last_update_utc':utc(timestamp).isoformat(),
                         'source':'the-odds-api'})
    return output


def fetch_quotations(api_key):
    if not api_key:raise ValueError('THE_ODDS_API_KEY is not configured')
    now=datetime.now(timezone.utc)
    with requests.Session() as session:
        events=get_json(session,BASE+'/events',{'apiKey':api_key})
        records=[]
        for e in events:
            if not e.get('id'):continue
            # Request exact DK+FD books and the NHL shots-on-goal event market.
            try:
                result=get_json(session,BASE+'/events/'+e['id']+'/odds',{
                    'apiKey':api_key,'bookmakers':'draftkings,fanduel',
                    'markets':'player_shots_on_goal','oddsFormat':'american'})
                records.extend(parse_events([result],datetime.now(timezone.utc)))
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code in (429,401,403):
                    raise  # stop to avoid burning quota or ignoring bad credentials
                raise
            time.sleep(0.08)
    return records,len(events),now


def main():
    arg=argparse.ArgumentParser();arg.add_argument('--local-only',action='store_true');opts=arg.parse_args()
    records,n,run_at=fetch_quotations(os.getenv('THE_ODDS_API_KEY',''))
    if opts.local_only:
        folder=Path('private_data');folder.mkdir(exist_ok=True)
        (folder/'quotes_latest.json').write_text(json.dumps(records,indent=2))
        print(f'Local-only: {len(records)} provider quote rows across {n} scheduled events; never commit private_data/')
    else:
        if records:table_append('sog_prices',records)
        table_append('sog_refresh_runs',[{'kind':'odds','success':True,'message':f'{n} events fetched; prices append-only','quotes':len(records)}])
        print(f'Persisted {len(records)} verified-source quote rows from {n} events at {run_at.isoformat()}')
if __name__=='__main__':main()
