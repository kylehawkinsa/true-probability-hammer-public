"""TRUE PROBABILITY HAMMER / private mobile-first site.

Dedicated scrypt password plus hosting-level PRIVATE viewer restriction are mandatory.
Private Supabase PostgREST credentials remain on server; app never exports credentials.
A research-only model or stale market NEVER displays an actionable selection.
"""
from __future__ import annotations
import json
import os
from datetime import datetime,timezone,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from html import escape
import pandas as pd
import streamlit as st
from tph_core import password_valid,compare,gate,utc,normalize_name
from storage import table_read,credentials

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='True Probability Hammer • NHL SOG',page_icon='🏒',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"],p,div,span{font-family:'DM Sans',sans-serif}
.stApp{background:#071018;color:#ECF8FF}
.block-container{max-width:1080px;padding:1.05rem 1.1rem 4rem}
.tph-eyebrow{font-size:0.7rem;letter-spacing:.19em;color:#6FD9BB;font-weight:800}
.tph-title{font-size:2rem;letter-spacing:-.06em;font-weight:800;line-height:1.06;margin:.4rem 0 .5rem}
.tph-muted{color:#9BAFBD;font-size:.86rem}
.tph-shell{border:1px solid #203443;border-radius:17px;background:#101C2B;padding:16px;margin:8px 0 16px}
.tph-chip{display:inline-block;padding:5px 10px;border-radius:99px;font-size:.72rem;background:#18372E;color:#7AF0C9;font-weight:700;border:1px solid #315b4f}
.tph-chip-warn{background:#352A1C;color:#F5C68C;border-color:#56452C}
.tph-kpi{font-size:1.85rem;font-weight:800;letter-spacing:-.05em;margin-top:6px}
.tph-kpi-label{color:#91AAB8;font-size:.76rem}
section[data-testid="stSidebar"]{background:#101C2B}
div[data-testid="stMetric"]{background:#132233;border-radius:14px;padding:12px;border:1px solid #23384A}
button[data-testid="stBaseButton-primary"]{background:#45F2C6;color:#051C19;border:0;font-weight:800}
.tph-best{background:#0d3d2e;color:#7af0c9;font-weight:700;border-radius:8px;padding:2px 8px}
.tph-better{background:#3d320d;color:#f5c68c;font-weight:700;border-radius:8px;padding:2px 8px}
.tph-good{background:#3d240d;color:#f5a068;font-weight:700;border-radius:8px;padding:2px 8px}
@media(max-width:650px){
 .block-container{padding:1rem .72rem 4rem}
 .tph-title{font-size:1.65rem}
 div[data-testid="stMetric"]{padding:7px}
 div[data-testid="stMetricValue"]{font-size:1.27rem}
 button[data-baseweb="tab"]{font-size:.78rem;padding:5px 8px}
}
</style>''', unsafe_allow_html=True)

def secret(name,default=''):
    try:return str(st.secrets.get(name,os.environ.get(name,default)))
    except Exception:return str(os.environ.get(name,default))

# --- Auth is a second gate. FIRST gate is host's explicit private-viewer list.
secret_hash=secret('TPH_PASSWORD_HASH')
if not secret_hash.startswith('scrypt$'):
    st.error('Private access is NOT CONFIGURED. Add TPH_PASSWORD_HASH in deployment secrets; do not disable the password gate.')
    st.code('python setup_password.py')
    st.stop()
if not st.session_state.get('tph_authenticated'):
    st.markdown('<p class="tph-eyebrow">TRUE PROBABILITY HAMMER / PRIVATE PORTAL</p>',unsafe_allow_html=True)
    st.markdown('<div class="tph-title">Your NHL research.<br/>Your eyes only.</div>',unsafe_allow_html=True)
    st.caption('Second security gate. Host must ALSO restrict access to your approved email address.')
    if st.session_state.get('tries',0)>=5:
        st.error('Too many attempts in this session. Close this browser tab and use host-level access controls.')
        st.stop()
    with st.form('login'):
        password=st.text_input('Passphrase',type='password',autocomplete='off')
        submitted=st.form_submit_button('Unlock research desk',type='primary',use_container_width=True)
    if submitted:
        if password_valid(password,secret_hash):
            st.session_state['tph_authenticated']=True
            st.rerun()
        else:
            st.session_state['tries']=st.session_state.get('tries',0)+1
            st.error('Invalid passphrase.')
    st.stop()

now=datetime.now(timezone.utc)
with st.sidebar:
    st.markdown('## 🏒 True Probability Hammer')
    st.caption('Research desk / strictly paper only')
    st.write('Private member portal')
    if st.button('Lock and sign out',use_container_width=True):
        st.session_state.pop('tph_authenticated',None)
        st.rerun()
    st.divider()
    st.caption('MODEL POLICY')
    st.write('Research is not an approved betting model.')
    st.write('No verified price = no edge.')
    st.write('Every prediction must be timestamped before puck drop.')

st.markdown('<div class="tph-eyebrow">THE HAMMER / NHL SHOTS ON GOAL</div>',unsafe_allow_html=True)
st.markdown('<div class="tph-title">Kyle Hawkins Sharp SOG Model</div>',unsafe_allow_html=True)
st.markdown('<div class="tph-muted">NHL shots on goal · DraftKings + FanDuel</div>',unsafe_allow_html=True)
st.write('')
st.markdown('<span class="tph-chip tph-chip-warn">● PAPER / RESEARCH MODE</span>',unsafe_allow_html=True)

@st.cache_data(ttl=90,show_spinner=False)
def get_data(supabase_url,supabase_key):
    if not (supabase_url and supabase_key):return [],[],[]
    # Backend-sourced only; never use browser/client secrets.
    env={'SUPABASE_URL':supabase_url,'SUPABASE_SERVICE_ROLE_KEY':supabase_key}
    quotes=table_read('sog_prices',{'select':'*','order':'price_captured_at_utc.desc','limit':'2000'},env)
    forecasts=table_read('sog_forecasts',{'select':'*','order':'forecast_created_utc.desc','limit':'1500'},env)
    runs=table_read('sog_refresh_runs',{'select':'*','order':'run_at_utc.desc','limit':'10'},env)
    return quotes,forecasts,runs

url=secret('SUPABASE_URL');key=secret('SUPABASE_SERVICE_ROLE_KEY')
try:quotes,forecasts,runs=get_data(url,key)
except Exception:
    quotes=[];forecasts=[];runs=[]
    st.error('Private data source unavailable. Live board disabled. Check database connection privately.')

archived_path=ROOT/'research'/'pittsburgh_calibration_holdout.csv'
@st.cache_data(show_spinner=False)
def archive():return pd.read_csv(archived_path,parse_dates=['date'])

# Format lightweight health status. Connection alone is not proof of fresh data.
most_recent=None
for row in quotes:
    try:
        stamp=utc(row['price_captured_at_utc'])
        if most_recent is None or stamp>most_recent:most_recent=stamp
    except (KeyError,ValueError,TypeError):pass
recent_age=round((now-most_recent).total_seconds()/60) if most_recent else None
status=('RECENT' if recent_age is not None and 0<=recent_age<=15 else 'STALE / UNCONNECTED')

# Captured sportsbook observations: display-only, never injected into approved forecasts.
CAPTURED_MARKET_ROWS=json.loads(r'''[["2026-10-19 7:00 PM | COL @ PHI","Nathan MacKinnon","COL",3.5,null,null,-146,112],["2026-10-19 7:00 PM | COL @ PHI","Cale Makar","COL",2.5,null,null,-114,-114],["2026-10-19 7:00 PM | ANA @ NYR","Alex Killorn","ANA",1.5,null,null,-160,122],["2026-10-19 7:00 PM | ANA @ NYR","Cutter Gauthier","ANA",3.5,null,null,100,-130],["2026-10-19 7:00 PM | ANA @ NYR","Beckett Sennecke","ANA",2.5,null,null,114,-148],["2026-10-19 7:00 PM | ANA @ NYR","Will Cuylle","NYR",1.5,null,null,-168,128],["2026-10-19 7:00 PM | ANA @ NYR","Gabe Perreault","NYR",1.5,null,null,-138,104],["2026-10-19 7:00 PM | ANA @ NYR","Pavel Dorofeyev","NYR",2.5,null,null,null,null],["2026-10-19 7:00 PM | ANA @ NYR","Alexis Lafrenière","NYR",1.5,null,null,null,null],["2026-10-19 7:30 PM | SJ @ TOR","Jack Roslovic","TOR",1.5,null,null,-188,142],["2026-10-19 7:30 PM | SJ @ TOR","Kirill Marchenko","TOR",2.5,null,null,null,null],["2026-10-19 7:30 PM | SJ @ TOR","Mason Marchment","SJ",1.5,null,null,-146,112],["2026-10-19 7:30 PM | SJ @ TOR","William Nylander","TOR",2.5,null,null,-130,100],["2026-10-19 7:30 PM | SJ @ TOR","Darren Raddysh","TOR",2.5,null,null,100,-130],["2026-10-19 7:30 PM | SJ @ TOR","Will Smith","SJ",2.5,null,null,-106,-122],["2026-10-19 7:30 PM | SJ @ TOR","Tyler Toffoli","SJ",1.5,null,null,null,null],["2026-10-19 9:00 PM | PIT @ UTA","Mikhail Sergachev","UTA",1.5,null,null,-160,122],["2026-10-19 9:00 PM | PIT @ UTA","Anders Lee","UTA",1.5,null,null,-164,125],["2026-10-19 9:00 PM | PIT @ UTA","Bryan Rust","PIT",1.5,null,null,-176,134],["2026-10-19 9:00 PM | PIT @ UTA","Clayton Keller","UTA",2.5,null,null,108,-140],["2026-10-19 9:00 PM | PIT @ UTA","Nick Schmaltz","UTA",2.5,null,null,-102,-128],["2026-10-19 9:00 PM | PIT @ UTA","Tommy Novak","PIT",1.5,null,null,100,null],["2026-10-19 9:00 PM | PIT @ UTA","Barrett Hayton","UTA",1.5,null,null,-118,-110],["2026-10-19 9:00 PM | PIT @ UTA","Erik Karlsson","PIT",1.5,null,null,-154,118],["2026-10-19 9:00 PM | PIT @ UTA","Dylan Guenther","UTA",2.5,null,null,-130,100],["2026-10-19 9:00 PM | PIT @ UTA","Rickard Rakell","PIT",2.5,null,null,114,-148]]''')

def snapshot_market_frame(records):
    def implied(price):
        if price is None or abs(price)<100:
            return None
        return 100/(price+100) if price>0 else abs(price)/(abs(price)+100)
    output=[]
    for r in records:
        date_time,matchup=r[0].split(' | ',1)
        start=datetime.strptime(date_time,'%Y-%m-%d %I:%M %p').replace(tzinfo=ZoneInfo('America/New_York'))
        output.append({
            'Player':r[1], 'Team':r[2], 'SOG line':r[3],
            'FD Under':r[7], 'Under implied':implied(r[7]),
            'FD Over':r[6], 'Over implied':implied(r[6]),
            'Matchup':matchup, 'Start ET':start.strftime('%m/%d %I:%M %p'),
            'Status':'Game started' if start<=now else ('Under not captured' if r[7] is None else 'Captured price'),
        })
    return pd.DataFrame(output)

# --- Build verified eligible edges (shared by Board and Tomorrows Picks) ---
latest={}
for q in quotes:
    try:
        if utc(q['game_start_utc'])<=now:continue
        k=(str(q['event_id']),normalize_name(q['player_name']),float(q['line']),str(q['book']),str(q['side']))
        if k not in latest or utc(q['price_captured_at_utc'])>utc(latest[k]['price_captured_at_utc']):latest[k]=q
    except (KeyError,ValueError,TypeError):continue
eligible=[];rejects={}
for fc in forecasts:
    try:
        if utc(fc['game_start_utc'])<=now:continue
        for book in ['draftkings','fanduel']:
            keybase=(str(fc['event_id']),normalize_name(fc['player_name']),float(fc['line']),book)
            over=latest.get(keybase+('Over',));under=latest.get(keybase+('Under',))
            if not over or not under:
                rejects['Both sides of price unavailable']=rejects.get('Both sides of price unavailable',0)+1
                continue
            for q,opp in [(over,under),(under,over)]:
                test=compare(fc,q,opp,now)
                if test.get('eligible'):
                    test['game_start_utc']=fc.get('game_start_utc')
                    eligible.append(test)
                else:
                    reason=test.get('reason','Unverified')
                    rejects[reason]=rejects.get(reason,0)+1
    except (KeyError,ValueError,TypeError):continue

# Main navigation keeps research and setup off the daily screen.
home,board,validation,tracking,settings=st.tabs(['Top 10','Odds','Research','Ledger','Settings'])
with home:
    st.subheader('Top 10 plays')
    game_date=st.date_input('Game date (Eastern)',value=now.astimezone(ZoneInfo('America/New_York')).date())
    picks=[r for r in eligible if utc(r['game_start_utc']).astimezone(ZoneInfo('America/New_York')).date()==game_date]
    picks.sort(key=lambda r:(r['true_probability'],r['edge_vs_no_vig_pp']),reverse=True)
    seen=set();top=[]
    for r in picks:
        key=(normalize_name(r['player']),r['game_start_utc'])
        if key not in seen:
            seen.add(key);top.append(r)
        if len(top)==10:break
    if not top:
        st.markdown('<div class="tph-shell"><h3>Picks awaiting verified forecasts</h3><p class="tph-muted">Current game histories, lineup inputs and model approval are still required before plays can be ranked.</p><p>26 captured player lines are available in the <b>Odds</b> tab.</p></div>',unsafe_allow_html=True)
    else:
        st.caption('Ranked by model probability, then edge. One selection per player/game. These rankings do not require positive EV.')
        for i in range(0,len(top),2):
            columns=st.columns(2)
            for col,(rank,r) in zip(columns,enumerate(top[i:i+2],start=i+1)):
                with col:
                    with st.container(border=True):
                        st.markdown(f"### {rank}. {escape(r['player'])}")
                        st.write(f"{r['side']} {r['line']:g} SOG · {r['book'].title()} {r['odds']:+d}")
                        a,b=st.columns(2)
                        a.metric('Model probability',f"{r['true_probability']:.1%}")
                        b.metric('Implied probability',f"{r['book_break_even']:.1%}")
                        st.caption(f"Edge {r['edge_vs_no_vig_pp']:+.1f} pp · EV {r['ev_per_dollar']:+.1%}")
    if rejects:
        with st.expander('Forecast checks'):st.json(rejects)

with board:
    st.divider()
    st.subheader('Captured SOG lines · October 19, 2026')
    st.caption('FanDuel prices observed on Props.Cash, Oct 18 approximately 9:50–9:57 PM ET. Manual snapshot, not an automatic feed. Sportsbook update timestamps were not supplied.')
    market_frame=snapshot_market_frame(CAPTURED_MARKET_ROWS)
    a,b,c=st.columns(3)
    a.metric('Player lines',len(market_frame))
    b.metric('Under prices',int(market_frame['FD Under'].notna().sum()))
    c.metric('Over prices',int(market_frame['FD Over'].notna().sum()))
    st.info('Model scoring pending: verified current-season game-history features and pregame lineup inputs are missing. Implied probabilities below come from prices; model true probability and EV are unavailable.')
    market_choice=st.selectbox('Captured matchup',['All games']+sorted(market_frame['Matchup'].unique().tolist()),key='captured_matchup')
    market_view=market_frame if market_choice=='All games' else market_frame[market_frame['Matchup']==market_choice]
    st.dataframe(
        market_view.style.format({
            'SOG line':'{:.1f}', 'FD Under':'{:+.0f}', 'FD Over':'{:+.0f}',
            'Under implied':'{:.1%}', 'Over implied':'{:.1%}',
        },na_rep='Unavailable'),
        hide_index=True,use_container_width=True,height=440,
    )
    st.caption('DraftKings quotes were not captured. Missing prices remain unavailable. These observations do not count as prospective model picks or change model approval.')
    st.download_button('Download captured lines',market_frame.to_csv(index=False),
                       'sog_market_snapshot_2026-10-19.csv','text/csv')

with validation, st.expander('Historical player lab'):
    st.subheader('Historical player lab')
    st.caption('This is actual saved Pittsburgh 2023–24 V2 forecast data; not a current slate or actual sportsbook prices.')
    db=archive()
    p=st.selectbox('Player',sorted(db.player.dropna().unique()))
    ln=st.selectbox('Shot line',[1.5,2.5,3.5,4.5],index=1)
    segment=db[(db.player==p)&(db.line==ln)].sort_values('date')
    if not segment.empty:
        avg=segment.calibrated_over.mean();observed=segment.event.mean()
        a,b,c=st.columns(3)
        a.metric('Mean predicted Over',f'{avg:.1%}')
        b.metric('Historical actual Over',f'{observed:.1%}')
        c.metric('Games',len(segment))
        st.line_chart(segment.set_index('date')[['prob_over','calibrated_over']],height=250)
        st.dataframe(segment[['date','opponent','projected_sog','calibrated_over','actual_sog']].tail(12),hide_index=True,use_container_width=True)
        st.caption('Probabilities are historical research forecasts, not sportsbook wagering odds.')

with validation:
    st.subheader('Model laboratory')
    report_path=ROOT/'research'/'full_validation_summary.json'
    if report_path.exists():
        study=json.loads(report_path.read_text())
        scores=study['scores']
        a,b=st.columns(2)
        a.metric('V2 holdout log loss',f"{scores['v2_original']['log_loss']:.6f}")
        b.metric('V3 holdout log loss',f"{scores['v3_calibrated']['log_loss']:.6f}")
        a,b=st.columns(2)
        a.metric('V2 Brier score',f"{scores['v2_original']['brier']:.6f}")
        b.metric('V3 Brier score',f"{scores['v3_calibrated']['brier']:.6f}")
        st.caption(f"{study['test_rows']:,} player-games / {study['test_games']:,} NHL games / {study['binary_line_rows']:,} player-game-line outcomes.")
        paired=study['paired_v3_minus_baseline']['v2_original']
        st.write('**Paired V3 minus V2 log-loss difference:** '+f"{paired['log_loss_delta']:.8f}")
        st.write('**95% interval by NHL game:** '+str([round(x,8) for x in paired['by_game']['ci95']]))
        st.write('**95% interval by calendar week:** '+str([round(x,8) for x in paired['by_calendar_week']['ci95']]))
        st.info('Retrospective improvement is small. It supports a future paper trial; it does not establish profitable sportsbook picks.')
        st.warning('2024-25 and 2025-26 were excluded from training and tuning in this run, but had previously been examined in V2 research. They are retrospective holdouts, not pristine unseen data.')
        st.markdown('**V3 promotion checklist**')
        items=[
            ('Train challenger with strictly prior-game features',True),
            ('Hold out 2024–25 retrospective seasons without tuning on test scores',True),
            ('Require paired improvement and uncertainty interval',study['retrospective_gate_passed']),
            ('Run future prospective paper test with timestamped sportsbook lines',False),
            ('Manually approve only after documented review',False)]
        for label,complete in items:st.checkbox(label,value=bool(complete),disabled=True)
        st.caption('Trained and evaluated on 2026-10-18. V2 remains champion. V3 is research-only; no automatic promotion.')
        st.markdown('**Prospective trial status**')
        st.write('Frozen paired models and an append-only paper ledger are prepared. Current verified game-history features, pregame participation checks, an entitled DK/FD odds feed, and independent timestamp storage must be connected before the future trial can run.')
        st.write('Below 55% is a review trigger after at least 100 graded paper selections and 30 calendar days. Review ROI, calibration and genuine closing prices alongside hit rate. Register one challenger and use a fresh future window.')
        with st.expander('Evaluation evidence'):
            st.json(study)
    else:
        st.info('Full validation evidence has not been uploaded. Research-only status remains in effect.')

with tracking:
    st.subheader('Paper ledger')
    st.caption('Bet snapshots must be frozen BEFORE the start. No retroactive wager sizing or reconstructed odds.')
    columns=['locked_at_utc','game_start_utc','event_id','player_name','line','side','book','american_odds','price_captured_at_utc','model_version','true_probability','edge_vs_no_vig_pp','estimated_ev','stake_units','actual_sog','grade','closing_odds','closing_quote_at_utc','notes']
    st.download_button('Download paper ledger template',data=pd.DataFrame(columns=columns).to_csv(index=False),file_name='tph_paper_ledger_template.csv',mime='text/csv',use_container_width=True)
    st.info('The dashboard does not place real wagers. Immutable storage, automatic grading, and CLV require the next backend milestone.')

with settings:
    c1,c2,c3=st.columns(3)
    c1.metric('Automated price feed',status)
    c2.metric('Live quote rows',f'{len(quotes):,}')
    c3.metric('Approved forecasts',sum(1 for x in forecasts if x.get('model_status')=='approved' and x.get('data_verified') is True))
    st.caption('Feeds are server-side snapshots, not a streaming sportsbook connection. Price freshness checked against provider timestamps.')

    st.subheader('Operations & access')
    st.write('**Security:** hosting must be set PRIVATE to allowlisted email accounts; second gate requires your dedicated scrypt-protected password.')
    st.write('**Database:** '+('Configured' if url and key else 'Not connected. Configure Supabase server-side credentials.'))
    st.write('**Odds refresh:** '+(str(runs[0].get('run_at_utc')) if runs else 'No verified refresh runs recorded.'))
    st.write('**Forecast engine:** research-only until the trained model has been evaluated and explicitly approved.')
    st.markdown('**External sources planned:** The Odds API DK/FD NHL SOG markets, NHL schedule/boxscores, MoneyPuck game histories, and manually vetted injury/deployment feeds.')
    if st.button('Check refresh state',use_container_width=True):
        get_data.clear();st.rerun()
    st.write('')
    if st.button('Lock screen',use_container_width=True):
        st.session_state.pop('tph_authenticated',None);st.rerun()

st.divider()
st.caption('TRUE PROBABILITY HAMMER • Research utility only • All times and probabilities require source provenance • No guaranteed profits')

