"""Private PostgREST/Supabase database adapter, server-side only."""
from __future__ import annotations
import os
import requests


def credentials(secrets=None):
    s=secrets if secrets is not None else os.environ
    url=str(s.get('SUPABASE_URL','')).strip().rstrip('/')
    key=str(s.get('SUPABASE_SERVICE_ROLE_KEY','')).strip()
    return url,key


def table_read(table, params, secrets=None):
    url,key=credentials(secrets)
    if not url or not key:return []
    if table not in ('sog_prices','sog_forecasts','sog_refresh_runs'):
        raise ValueError('Unsupported table')
    resp=requests.get(f'{url}/rest/v1/{table}',params=params,headers={
        'apikey':key,'Authorization':'Bearer '+key},timeout=20)
    resp.raise_for_status()
    data=resp.json()
    if not isinstance(data,list):raise ValueError('Unexpected database result')
    return data


def table_append(table, rows, secrets=None):
    url,key=credentials(secrets)
    if not url or not key:raise RuntimeError('Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in server environment')
    if table not in ('sog_prices','sog_forecasts','sog_refresh_runs'):
        raise ValueError('Unsupported table')
    for k in range(0,len(rows),200):
        batch=rows[k:k+200]
        resp=requests.post(f'{url}/rest/v1/{table}',json=batch,headers={
            'apikey':key,'Authorization':'Bearer '+key,
            'Content-Type':'application/json','Prefer':'return=minimal,resolution=ignore-duplicates'},timeout=30)
        resp.raise_for_status()
