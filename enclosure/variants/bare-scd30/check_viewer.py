#!/usr/bin/env python3
"""Check the personal offline model, detailed sensor and original cable line."""
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
html=(HERE/'model.html').read_text()
meta=json.loads(re.search(r'<script id="model-data" type="application/json">(.*?)</script>',html,re.S)[1])
assert len([p for p in meta['parts'] if p.get('parent')=='scd30'])==24
assert not any(p['id'].startswith(('personal_','scd30-header','scd30-washer','scd30-screw','scd30-strain')) for p in meta['parts'])
original=json.loads(re.search(r'<script id="model-data" type="application/json">(.*?)</script>',(HERE.parents[1]/'model.html').read_text(),re.S)[1])
for part in meta['parts']:
    if part['id']=='qt3' or part.get('parent')=='qt3':
        before=next(p for p in original['parts'] if p['id']==part['id'])
        assert all(part[k]==before[k] for k in ('data','count','bounds'))
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1500,'height':1000},offline=True)
    page=context.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url))
    page.goto((HERE/'model.html').as_uri());page.wait_for_selector('canvas[data-rendered="true"]')
    state=page.evaluate('sensorWorkshop.state()')
    assert state['version']=='0.6-personal-scd30-2'
    assert len(state['components'])==28
    assert sum(c['group']=='Printed enclosure' for c in state['components'])==3
    assert page.locator('#error').is_hidden() and state['glError']==0
    assert 'snap-in bare SCD30' in page.locator('header').inner_text()
    page.locator('details').evaluate_all('(nodes)=>nodes.forEach(n=>n.open=true)')
    for c in state['components']:
        checkbox=page.locator(f'input[data-part="{c["id"]}"]');checkbox.uncheck()
        assert not next(v for v in page.evaluate('sensorWorkshop.state().components') if v['id']==c['id'])['visible']
        checkbox.check()
    page.locator('#reset').click();page.locator('#inside').click();page.locator('[data-view="bottom"]').click()
    page.screenshot(path=str(HERE/'renders/viewer-inside.png'))
    for amount in ('50','100'):
        page.locator('#explode').fill(amount)
        assert page.evaluate('sensorWorkshop.state().explosion')==int(amount)/100
        state=page.evaluate('sensorWorkshop.state()')
        assert not next(c for c in state['components'] if c['id']=='qt3')['visible']
        assert next(c for c in state['components'] if c['id']=='scd30')['offset'][2]==-65*int(amount)/100
    page.screenshot(path=str(HERE/'renders/viewer-exploded.png'))
    page.locator('#motion').select_option('feather')
    state=page.evaluate('sensorWorkshop.state()')
    assert not any(c['visible'] for c in state['components'] if c['id'].startswith('scd30'))
    page.locator('#reset').click();page.locator('#cut').select_option('x');page.locator('#cut-position').fill('49')
    assert page.evaluate('sensorWorkshop.state().cutPosition')==49
    page.locator('#reset').click();page.locator('#tie-access').click();page.locator('#tie-section').click();page.locator('#pole-mount').click()
    assert page.locator('#error').is_hidden()
    page.locator('#reset').click();page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.evaluate('sensorWorkshop.state().glError')==0
    assert not errors,errors
    assert not any(url.startswith(('http:','https:')) for url in requests),requests
    report={'status':'passed','variant':state['version'],'offline':True,'selectable_components':28,
        'checks':['all visibility controls','explosion and sensor motion','25 vendor solids grouped under the sensor',
            'original cable geometry retained and hidden during explosion','obsolete clamp hardware absent',
            'sensor hidden for Feather removal','cut through snap','existing tie and pole views',
            'mobile width','no JavaScript/WebGL errors or network requests'],
        'browser':browser.version,'limitations':['Chrome only','No physical fit implied']}
    (HERE/'generated/viewer-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));browser.close()
