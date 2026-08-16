import os
import sys

import requests

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

token = os.environ.get('DATABRICKS_TOKEN')
instance = os.environ.get('DATABRICKS_HOST', 'https://dbc-3f46f628-dd14.cloud.databricks.com')

print('=' * 70)
print('🚀 LIVE DATABRICKS LAKEHOUSE WORKFLOW AUDIT VIA DOPPLER')
print('=' * 70)
print('Databricks Host:', instance)

headers = {'Authorization': f'Bearer {token}'}

# 1. SCIM / User
me_res = requests.get(f'{instance}/api/2.0/preview/scim/v2/Me', headers=headers, timeout=15)
if me_res.status_code == 200:
    print('\n[1. AUTHENTICATED USER]:', me_res.json().get('userName'))
else:
    print('SCIM Error:', me_res.status_code, me_res.text)

# 2. Deployed Jobs
jobs_res = requests.get(f'{instance}/api/2.1/jobs/list', headers=headers, timeout=15)
if jobs_res.status_code == 200:
    jobs = jobs_res.json().get('jobs', [])
    print(f'\n[2. DEPLOYED WORKFLOW JOBS ({len(jobs)} Total)]:')
    for j in jobs:
        jid = j.get('job_id')
        name = j.get('settings', {}).get('name')
        print(f'  - Job ID: {jid} | Name: {name}')
else:
    print('Jobs Error:', jobs_res.status_code, jobs_res.text)

# 3. Recent Runs & Pipeline States
runs_res = requests.get(f'{instance}/api/2.1/jobs/runs/list?limit=10', headers=headers, timeout=15)
if runs_res.status_code == 200:
    runs = runs_res.json().get('runs', [])
    print(f'\n[3. RECENT PIPELINE EXECUTION RUNS ({len(runs)} Total)]:')
    for r in runs:
        rid = r.get('run_id')
        rname = r.get('run_name')
        state = r.get('state', {})
        res_state = state.get('result_state')
        life_state = state.get('life_cycle_state')
        print(f'  - Run ID: {rid} | Job: {rname} | Result: {res_state} | LifeCycle: {life_state}')
else:
    print('Runs Error:', runs_res.status_code, runs_res.text)
