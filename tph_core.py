"""True Probability Hammer / verified-market gates; stdlib only.

No artificial/simulated lines are generated. No model promotion is assumed.
All comparison fields must originate in independent, timestamped sources.
"""
from __future__ import annotations
import hashlib
import hmac
import base64
import math
import re
from datetime import datetime, timezone

SUPPORTED_BOOKS = {'draftkings', 'fanduel'}
SUPPORTED_LINES = {1.5, 2.5, 3.5, 4.5}


def utc(value):
    if isinstance(value, datetime):
        dt=value
    else:
        dt=datetime.fromisoformat(str(value).replace('Z','+00:00'))
    if dt.tzinfo is None:
        raise ValueError('Timestamp must explicitly include timezone')
    return dt.astimezone(timezone.utc)


def normalize_name(name):
    return re.sub(r'[^a-z0-9]', '', str(name).casefold())


def decimal_odds(american):
    a=int(american)
    if a==0 or -100<a<100:
        raise ValueError('Invalid American odds')
    return 1+a/100 if a>0 else 1+100/abs(a)


def implied_probability(american):
    return 1/decimal_odds(american)


def normalized_market_probability(over_odds,under_odds):
    # Standard proportional de-vig, label method when displayed.
    po=implied_probability(over_odds)
    pu=implied_probability(under_odds)
    return po/(po+pu)


def expected_value(p, american):
    return p*(decimal_odds(american)-1)-(1-p)


def password_hash(password, salt=None):
    # Single-user private site: scrypt + cryptographically random salt.
    import os
    salt=salt or os.urandom(16)
    result=hashlib.scrypt(password.encode('utf-8'),salt=salt,n=16384,r=8,p=1,dklen=32)
    return 'scrypt$'+base64.urlsafe_b64encode(salt).decode()+'$'+base64.urlsafe_b64encode(result).decode()


def password_valid(password, stored):
    try:
        scheme,bsalt,bhash=stored.split('$')
        if scheme!='scrypt':return False
        salt=base64.urlsafe_b64decode(bsalt.encode())
        correct=base64.urlsafe_b64decode(bhash.encode())
        guess=hashlib.scrypt(password.encode('utf-8'),salt=salt,n=16384,r=8,p=1,dklen=len(correct))
        return hmac.compare_digest(guess,correct)
    except (ValueError,TypeError,KeyError):
        return False


def gate(forecast, quote, now=None, freshness_minutes=15):
    """Fail closed; require validated frozen pregame forecast AND timestamped paired market.
    Quote should be an API-sourced row already matched to same event/player/line/side.
    """
    now=utc(now or datetime.now(timezone.utc))
    try:
        if str(forecast.get('model_status','')).lower()!='approved':return False,'Model not prospectively approved'
        if forecast.get('data_verified') is not True:return False,'Forecast inputs not verified'
        if quote.get('source')!='the-odds-api':return False,'Odds not independently sourced'
        if str(quote.get('book','')).lower() not in SUPPORTED_BOOKS:return False,'Unsupported sportsbook'
        line=float(quote['line'])
        if line not in SUPPORTED_LINES:return False,'Unsupported or missing shot line'
        if forecast.get('event_id')!=quote.get('event_id'):return False,'Game ID mismatch'
        if normalize_name(forecast.get('player_name',''))!=normalize_name(quote.get('player_name','')):return False,'Player ID/name mismatch'
        if abs(float(forecast['line'])-line)>1e-10:return False,'Line mismatch'
        forecast_at=utc(forecast['forecast_created_utc'])
        quote_at=utc(quote['price_captured_at_utc'])
        start=utc(quote['game_start_utc'])
        forecast_start=utc(forecast['game_start_utc'])
        if abs((start-forecast_start).total_seconds())>900:return False,'Game start discrepancy'
        if not forecast_at<=quote_at<=now<start:return False,'Not locked before game start'
        if (now-quote_at).total_seconds()>freshness_minutes*60:return False,'Odds stale'
        if not quote.get('book_last_update_utc'):return False,'Provider timestamp missing'
        updated=utc(quote['book_last_update_utc'])
        if updated>quote_at:return False,'Provider timestamp invalid'
        if (now-updated).total_seconds()>freshness_minutes*60:return False,'Bookmaker last update stale'
        side=str(quote.get('side',''))
        if side not in {'Over','Under'}:return False,'Missing side'
        p=float(forecast['prob_over'])
        if not math.isfinite(p) or p<0 or p>1:return False,'Invalid calibrated probability'
        decimal_odds(quote['american_odds'])
        return True,'Eligible for price comparison (not an automatic bet)'
    except (KeyError,ValueError,TypeError,OverflowError) as exc:
        return False,'Invalid input: '+str(exc)


def compare(forecast, quote, paired_quote, now=None, freshness_minutes=15):
    ok, reason=gate(forecast,quote,now,freshness_minutes)
    if not ok:return {'eligible':False,'reason':reason}
    paired_ok, paired_reason=gate(forecast,paired_quote,now,freshness_minutes)
    if not paired_ok:return {'eligible':False,'reason':'Paired market unavailable: '+paired_reason}
    if quote['side']==paired_quote['side'] or quote['book']!=paired_quote['book']:
        return {'eligible':False,'reason':'Paired over/under quote mismatch'}
    if abs((utc(quote['price_captured_at_utc'])-utc(paired_quote['price_captured_at_utc'])).total_seconds())>60:
        return {'eligible':False,'reason':'Paired market quote timestamps do not align'}
    p_over=float(forecast['prob_over'])
    p=p_over if quote['side']=='Over' else 1-p_over
    p_mkt_over=normalized_market_probability(
        quote['american_odds'] if quote['side']=='Over' else paired_quote['american_odds'],
        paired_quote['american_odds'] if quote['side']=='Over' else quote['american_odds'])
    p_mkt=p_mkt_over if quote['side']=='Over' else 1-p_mkt_over
    return {'eligible':True,'reason':'Ready for paper evaluation','true_probability':p,
            'book_break_even':implied_probability(quote['american_odds']),
            'market_no_vig':p_mkt, 'edge_vs_no_vig_pp':100*(p-p_mkt),
            'ev_per_dollar':expected_value(p,quote['american_odds']),
            'book':quote['book'],'player':quote['player_name'],'side':quote['side'],'line':float(quote['line']),
            'odds':int(quote['american_odds'])}
