#!/usr/bin/env python3
"""Exercise the standalone HTML in an isolated Chrome session, offline."""
import json
import math
from pathlib import Path
from playwright.sync_api import sync_playwright

CAD=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True,args=['--enable-unsafe-swiftshader'])
    context=browser.new_context(viewport={'width':1500,'height':1000},offline=True)
    page=context.new_page()
    errors=[];requests=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:requests.append(r.url))
    page.goto((CAD/'model.html').as_uri())
    page.wait_for_selector('canvas[data-rendered="true"]')
    assert page.locator('#error').is_hidden()
    initial=page.evaluate('sensorWorkshop.state()')
    assert len(initial['components'])==27 and initial['glError']==0
    assert initial['version']=='0.3'
    assert len([c for c in initial['components'] if c['group']=='Printed enclosure'])==3
    assert not any(c['id'] in ['switch','buttons','pod','shade','feet','lid','base'] for c in initial['components'])
    page.screenshot(path=str(CAD/'renders/viewer-assembled.png'))
    # Check a physical component, including its attached screen, actually toggles.
    page.locator('input[data-part="feather"]').uncheck()
    assert not next(x for x in page.evaluate('sensorWorkshop.state().components') if x['id']=='feather')['visible']
    page.locator('input[data-part="feather"]').check()
    page.locator('#explode').fill('64')
    page.wait_for_function('sensorWorkshop.state().explosion === .64')
    state=page.evaluate('sensorWorkshop.state()')
    assert math.isclose(next(x for x in state['components'] if x['id']=='carrier')['offset'][2],-29.44)
    assert not next(x for x in state['components'] if x['id']=='qt1')['visible']
    page.locator('#explode-all').click()
    page.wait_for_function('sensorWorkshop.state().explosion === 1')
    page.screenshot(path=str(CAD/'renders/viewer-exploded.png'))
    page.locator('#motion').select_option('feather')
    state=page.evaluate('sensorWorkshop.state()')
    assert state['motion']=='feather'
    for ident in ['feather','feather_frame','feather-screw-0','feather-screw-3']:
        assert next(x for x in state['components'] if x['id']==ident)['offset']==[0,0,-80]
    assert not next(x for x in state['components'] if x['id']=='carrier')['visible']
    assert next(x for x in state['components'] if x['id']=='battery')['offset']==[0,0,0]
    page.screenshot(path=str(CAD/'renders/viewer-feather-install.png'))
    page.locator('#explode').fill('40')
    assert next(x for x in page.evaluate('sensorWorkshop.state().components') if x['id']=='feather_frame')['offset']==[0,0,-32]
    page.locator('#assemble').click()
    assert next(x for x in page.evaluate('sensorWorkshop.state().components') if x['id']=='feather_frame')['offset']==[0,0,0]
    page.locator('#reset').click()
    assert page.evaluate('sensorWorkshop.state().motion')=='explode'
    page.locator('#cut').select_option('x')
    page.locator('#cut-position').fill('60')
    assert page.evaluate('sensorWorkshop.state().cutPosition')==60
    page.locator('#reset').click()
    page.locator('#hide-all').click()
    assert not any(x['visible'] for x in page.evaluate('sensorWorkshop.state().components'))
    page.locator('#show-all').click()
    assert all(x['visible'] for x in page.evaluate('sensorWorkshop.state().components'))
    # Exercise every component independently, including collapsed hardware rows.
    page.locator('details').evaluate_all('(nodes)=>nodes.forEach(n=>n.open=true)')
    for component in initial['components']:
        checkbox=page.locator(f'input[data-part="{component["id"]}"]')
        checkbox.uncheck()
        assert not next(x for x in page.evaluate('sensorWorkshop.state().components') if x['id']==component['id'])['visible']
        checkbox.check()
    page.locator('#inside').click()
    assert not next(x for x in page.evaluate('sensorWorkshop.state().components') if x['id']=='shell')['visible']
    page.locator('#fit').click()
    page.screenshot(path=str(CAD/'renders/viewer-inside.png'))
    page.locator('#reset').click()
    page.locator('[data-view="bottom"]').click()
    page.screenshot(path=str(CAD/'renders/viewer-underside.png'))
    page.locator('#reset').click()
    canvas=page.locator('#model').bounding_box()
    x,y=canvas['x']+canvas['width']/2,canvas['y']+canvas['height']/2
    old=page.evaluate('sensorWorkshop.state()')
    page.mouse.move(x,y);page.mouse.down();page.mouse.move(x+90,y+40,steps=8);page.mouse.up()
    assert page.evaluate('sensorWorkshop.state().yaw')!=old['yaw']
    page.mouse.wheel(0,-150)
    page.wait_for_function(f'sensorWorkshop.state().halfHeight !== {old["halfHeight"]}')
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#reset').click()
    page.screenshot(path=str(CAD/'renders/viewer-mobile.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert page.evaluate('sensorWorkshop.state().glError')==0
    assert not errors,errors
    assert not any(u.startswith(('http:','https:')) for u in requests),requests
    report=dict(status='passed',browser=browser.version,offline=True,selectable_components=27,
                checks=['three printed components; obsolete parts absent','all 27 visibility toggles','explosion 0/64/100 percent and transforms','Feather insertion mode: paired movement, carrier hidden, other parts stationary, reset','cut controls','hide/show all','look inside','orbit and zoom','mobile layout','no external network requests','no JavaScript/WebGL errors'],
                limitations=['Chrome only; Safari and Firefox not exercised','hardware fit is not a browser test'])
    (CAD/'generated/viewer-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    browser.close()
