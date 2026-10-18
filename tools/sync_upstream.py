#!/usr/bin/env python3
"""Open a reviewable upstream integration PR; explicitly dispatch secret-free CI."""
import json
from pathlib import Path
import subprocess
import os

def run(*args, check=True):
    return subprocess.run(args,check=check,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
def git(*args): return run('git',*args).stdout.strip()

def main():
    repo=os.environ['GITHUB_REPOSITORY']
    config=json.loads(Path('.github/upstreams.json').read_text())
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    for name,url in [('upstream',config['upstream']),('android-reference',config['android'])]:
        run('git','remote','add',name,url,check=False)
        git('fetch','--no-tags',name,'main')
    original=git('rev-parse','upstream/main');android=git('rev-parse','android-reference/main')
    need_merge=run('git','merge-base','--is-ancestor',original,'HEAD',check=False).returncode!=0
    if not need_merge and android==config['android_reviewed']: return
    branch='sync/'+original[:10]+'-'+android[:10]
    # Keep an existing review intact; never force-push over reviewer changes.
    existing=json.loads(run('gh','pr','list','--repo',repo,'--state','all','--head',branch,'--json','number,state').stdout)
    if existing: return
    git('switch','-c',branch)
    conflict=False
    if need_merge:
        result=run('git','merge','--no-edit','upstream/main',check=False)
        if result.returncode:
            conflict=True
            conflicts=git('diff','--name-only','--diff-filter=U')
            git('merge','--abort')
        else: conflicts='None'
    else: conflicts='None'
    report=(f'# Upstream review\n\nOriginal: `{original}`\n\nAndroid reference: `{android}`\n\n'
            f'Original merge conflicts: {conflicts}\n\n'
            f'Android changes require selective review: https://github.com/sydeEvans/d2r-android/compare/{config["android_reviewed"]}...{android}\n\n'
            'Do not merge until conflicts and Android compatibility are reviewed. Update android_reviewed only after reviewing that diff.\n')
    Path('docs/UPSTREAM_REVIEW.md').write_text(report)
    git('add','docs/UPSTREAM_REVIEW.md');git('commit','-m','Record upstream integration review')
    git('push','origin',branch)
    run('gh','pr','create','--repo',repo,'--base','main','--head',branch,'--title','Review upstream updates '+original[:8],'--body-file','docs/UPSTREAM_REVIEW.md',*(['--draft'] if conflict else []))
    # PRs created with GITHUB_TOKEN do not trigger pull_request workflows.
    run('gh','workflow','run','build.yml','--repo',repo,'--ref',branch)
if __name__=='__main__':main()
