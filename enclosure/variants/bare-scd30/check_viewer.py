#!/usr/bin/env python3
"""Check the personal offline model, especially changed header and lead controls."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1500,'height':1000},offline=True)
    page=context.new_page();errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url))
    page.goto((HERE/'model.html').as_uri());page.wait_for_selector('canvas[data-rendered="true"]')
    state=page.evaluate('sensorWorkshop.state()')
    assert state['version']=='0.6-personal-scd30-1'
    assert len(state['components'])==34
    assert sum(c['group']=='Printed enclosure' for c in state['components'])==3
    assert page.locator('#error').is_hidden() and state['glError']==0
    assert {c['id'] for c in state['components']} >= {'scd30-header','scd30-washer-0','scd30-washer-1','scd30-strain-tie','personal_wire_0'}
    assert 'soldered SCD30' in page.locator('header').inner_text()
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
        assert not next(c for c in state['components'] if c['id']=='personal_wire_0')['visible']
        assert next(c for c in state['components'] if c['id']=='scd30-header')['offset'][2]==-56*int(amount)/100
    page.screenshot(path=str(HERE/'renders/viewer-exploded.png'))
    page.locator('#motion').select_option('feather')
    state=page.evaluate('sensorWorkshop.state()')
    assert not any(c['visible'] for c in state['components'] if c['id'].startswith('scd30'))
    page.locator('#reset').click();page.locator('#cut').select_option('x');page.locator('#cut-position').fill('33')
    assert page.evaluate('sensorWorkshop.state().cutPosition')==33
    page.locator('#reset').click();page.locator('#tie-access').click();page.locator('#tie-section').click();page.locator('#pole-mount').click()
    assert page.locator('#error').is_hidden()
    page.locator('#reset').click();page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.evaluate('sensorWorkshop.state().glError')==0
    assert not errors,errors
    assert not any(url.startswith(('http:','https:')) for url in requests),requests
    report={'status':'passed','variant':state['version'],'offline':True,'selectable_components':34,
        'checks':['all visibility controls','explosion and header motion','pigtail hidden during explosion',
            'all personal sensor attachments hidden for Feather removal','cut at header screw',
            'existing tie and pole views','mobile width','no JavaScript/WebGL errors or network requests'],
        'browser':browser.version,'limitations':['Chrome only','No physical fit implied']}
    (HERE/'generated/viewer-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));browser.close()
