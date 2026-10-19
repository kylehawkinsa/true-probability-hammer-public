"""Import *research-only* pregame forecast CSVs produced by an authorized model run.

This does NOT promote the V3 challenger. It intentionally forces all imported
forecasts to research/unverified until the validation protocol approves a model.
"""
import argparse
from datetime import datetime,timezone
import pandas as pd
from tph_core import utc, SUPPORTED_LINES
from storage import table_append

COLS=['event_id','game_start_utc','player_name','line','prob_over','forecast_created_utc','model_version']

def parse_export(path):
    data=pd.read_csv(path)
    missing=set(COLS)-set(data.columns)
    if missing:raise ValueError('Missing required columns: '+', '.join(sorted(missing)))
    output=[]
    for _,r in data.iterrows():
        p=float(r.prob_over);line=float(r.line)
        created=utc(r.forecast_created_utc);start=utc(r.game_start_utc)
        if not 0<=p<=1 or line not in SUPPORTED_LINES or created>=start:
            raise ValueError('Probability, line, or forecast timestamp invalid')
        if (pd.isna(r.event_id) or pd.isna(r.player_name)
            or not str(r.event_id).strip() or not str(r.player_name).strip()):
            raise ValueError('Missing identity')
        output.append({'event_id':str(r.event_id),'game_start_utc':start.isoformat(),
                      'player_name':str(r.player_name),'line':line,
                      'projected_sog':float(r.projected_sog) if 'projected_sog' in data.columns and pd.notna(r.projected_sog) else None,
                      'prob_over':p,'forecast_created_utc':created.isoformat(),
                      'model_version':str(r.model_version),
                      'model_status':'research','data_verified':False})
    return output

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('csv_path');args=parser.parse_args()
    rows=parse_export(args.csv_path)
    if rows:table_append('sog_forecasts',rows)
    print('Imported',len(rows),'RESEARCH-ONLY forecasts; zero approved wagers')
