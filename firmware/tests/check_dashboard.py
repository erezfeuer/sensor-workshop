#!/usr/bin/env python3
"""Exercise the production page with a simulated API; no device is contacted.

Requires Playwright and Chromium (or local Google Chrome).
"""
import json
import math
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / 'tests/artifacts'
ARTIFACTS.mkdir(exist_ok=True)

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/web/index.html'
checks = []
def passed(name):
    checks.append(name)
    print('PASS', name, flush=True)

try:
    with sync_playwright() as pw:
        chrome = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        browser = pw.chromium.launch(executable_path=str(chrome) if chrome.exists() else None)
        page = browser.new_page(viewport={'width': 1360, 'height': 1000}, locale='en-US')
        errors, network = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: network.append(request.url))
        page.add_init_script(path=str(ROOT / 'tests/mock_device.js'))
        page.goto(url)
        expect(page.locator('#co2')).to_have_text('637')
        expect(page.locator('#historySummary')).to_contain_text('120 plotted points')
        assert not any(x.startswith('http') and '127.0.0.1' not in x for x in network)
        passed('Live dashboard and history require no external requests')
        page.screenshot(path=str(ARTIFACTS / 'desktop-live.png'), full_page=True)

        page.locator('[data-tab="runtime"]').click()
        expect(page.locator('#fullRuntime')).to_have_text('4.9 days')
        estimate = page.evaluate('''() => SensorWorkshop.powerModel({capacity:3500,interval:60,cadence:2,
          wifi:10,screen:10,usable:80,wake:1.2,cpuMa:45,wifiMa:160,screenMa:25,extras:2,sleepMa:.1},1441792)''')
        assert math.isclose(estimate['ma'], 23.8053611111, abs_tol=0.00001)
        assert estimate['records'] == 22016
        page.locator('#modelCadence').select_option('30')
        expect(page.locator('#fullRuntime')).to_have_text('11.2 days')
        assert page.evaluate('DemoDevice.state.settings.sensor_interval_s') == 2
        page.locator('#modelCadence').select_option('2')
        page.locator('#modelCapacity').fill('1750')
        expect(page.locator('#fullRuntime')).to_have_text('2.5 days')
        page.locator('#modelCapacity').fill('3500')
        passed('Calculator agrees with native model; scenarios do not change device settings')
        page.screenshot(path=str(ARTIFACTS / 'desktop-runtime.png'), full_page=True)

        page.locator('[data-tab="settings"]').click()
        page.locator('#name').fill('Test plot')
        page.locator('#interval').fill('120')
        page.locator('#channels input[value="8"]').uncheck()
        page.locator('#saveSettings').click()
        expect(page.locator('#settingsFeedback')).to_have_text('Saved to device.')
        saved = page.evaluate("DemoDevice.calls.filter(c=>c.path==='/api/settings').at(-1)")
        assert saved['data']['channels'] == 23 and saved['data']['expected_revision'] == 1
        assert saved['headers']['X-Workshop-Token'] == 'preview-token'
        assert page.evaluate('DemoDevice.state.settings.revision') == 2
        passed('Settings save carries channel mask, revision and per-device token')

        page.locator('#name').fill('Stale editor')
        page.evaluate('DemoDevice.state.settings.revision++')
        page.locator('#saveSettings').click()
        expect(page.locator('#settingsFeedback')).to_contain_text('Settings changed')
        page.wait_for_timeout(2100)
        page.locator('#reloadSettings').click()
        expect(page.locator('#name')).to_have_value('Test plot')
        passed('Conflicting settings are shown; edited values survive background polling')

        page.locator('#settings details summary').click()
        page.locator('#sensorInterval').select_option('30')
        page.locator('#saveSettings').click()
        expect(page.locator('#settingsFeedback')).to_contain_text('requires recalibration')
        page.locator('#cadenceAck').check()
        page.locator('#saveSettings').click()
        expect(page.locator('#settingsFeedback')).to_have_text('Saved to device.')
        expect(page.locator('#quality')).to_contain_text('cadence changed')
        passed('Cadence change acknowledgement and calibration warning')

        page.locator('[data-tab="live"]').click()
        page.locator('#toggleLog').click()
        expect(page.locator('#toggleLog')).to_have_text('Start logging')
        page.locator('#toggleLog').click()
        expect(page.locator('#toggleLog')).to_have_text('Pause logging')
        page.locator('#syncClock').click()
        page.wait_for_function("DemoDevice.calls.some(c=>c.path==='/api/clock')")
        assert abs(page.evaluate('DemoDevice.state.utc') - page.evaluate('Math.floor(Date.now()/1000)')) <= 2
        passed('Start/pause and explicit phone clock sync')
        with page.expect_download() as info:
            page.locator('#live a[download]').click()
        download = info.value
        download.save_as(ARTIFACTS / download.suggested_filename)
        assert 'co2_ppm' in (ARTIFACTS / download.suggested_filename).read_text()
        passed('CSV download control produces a file (simulated contents)')

        page.locator('[data-tab="calibration"]').click()
        expect(page.locator('#calApply')).to_be_disabled()
        page.locator('#calStart').click()
        expect(page.locator('#calTitle')).to_have_text('Stabilising…')
        page.locator('#referencePpm').fill('420')
        page.locator('#referenceAck').check()
        expect(page.locator('#calApply')).to_be_disabled()
        page.evaluate('DemoDevice.calibrationReady = true')
        expect(page.locator('#calTitle')).to_have_text('Ready to apply', timeout=5000)
        page.locator('#referencePpm').fill('399')
        expect(page.locator('#calApply')).to_be_disabled()
        page.locator('#referencePpm').fill('420')
        page.locator('#referenceAck').uncheck()
        expect(page.locator('#calApply')).to_be_disabled()
        page.locator('#referenceAck').check()
        page.locator('#calApply').click()
        expect(page.locator('#calTitle')).to_have_text('Allow six minutes')
        assert page.evaluate('DemoDevice.state.calibration_due') is False
        passed('Calibration needs ready state, valid reference and explicit confirmation')

        page.locator('[data-tab="runtime"]').click()
        page.locator('#runtime details').last.locator('summary').click()
        page.locator('#eraseConfirm').fill('ERASE')
        expect(page.locator('#eraseData')).to_be_disabled()
        page.locator('[data-tab="live"]').click()
        page.locator('#toggleLog').click()
        expect(page.locator('#toggleLog')).to_have_text('Start logging')
        page.locator('[data-tab="runtime"]').click()
        page.locator('#eraseConfirm').fill('erase')
        expect(page.locator('#eraseData')).to_be_disabled()
        page.locator('#eraseConfirm').fill('ERASE')
        page.locator('#eraseData').click()
        expect(page.locator('#storageInfo')).to_contain_text('0 records')
        expect(page.locator('#eraseConfirm')).to_have_value('')
        passed('Erase requires paused logging and exact confirmation')

        page.locator('[data-tab="live"]').click()
        page.evaluate('''() => {DemoDevice.state.live.co2=null;DemoDevice.state.live.lux=null;
          DemoDevice.state.live.light_saturated=true;DemoDevice.state.sensor='missing';
          SensorWorkshop.render(DemoDevice.state);}''')
        expect(page.locator('#co2')).to_have_text('—')
        expect(page.locator('#lightSensor')).to_contain_text('Saturated')
        expect(page.locator('#quality')).to_contain_text('not found')
        page.evaluate('''() => {DemoDevice.points=[{sequence:1,utc:0,session:1,co2:500},
          {sequence:2,utc:100,session:1,co2:null},{sequence:3,utc:90,session:1,co2:600}];}''')
        page.locator('#refreshHistory').click()
        expect(page.locator('#chartCaption')).to_contain_text('Record order')
        passed('Missing/saturated values remain blank; clock changes use record-order plot')

        page.evaluate('DemoDevice.fail = true')
        expect(page.locator('#connectionText')).to_have_text('Disconnected', timeout=5000)
        expect(page.locator('#connectionError')).to_contain_text('press D1')
        page.evaluate('DemoDevice.fail = false')
        expect(page.locator('#connectionText')).to_have_text('Connected', timeout=5000)
        passed('Connection loss explains how to reconnect and recovers')

        page.evaluate('DemoDevice.state.utc = 0')
        # Reload resets the fixture, so a new init script applies the missing clock after it.
        page.add_init_script("document.addEventListener('DOMContentLoaded',()=>{DemoDevice.state.utc=0;}, {once:true})")
        # A separate clean page gives a deterministic unset RTC at the first request.
        clockpage = browser.new_page()
        clockpage.add_init_script((ROOT / 'tests/mock_device.js').read_text() + '\nDemoDevice.state.utc=0;')
        clockpage.goto(url)
        clockpage.wait_for_function("DemoDevice.calls.some(c=>c.path==='/api/clock')")
        passed('Opening the dashboard sets an unset RTC from browser time')
        clockpage.close()

        mobile = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='en-US')
        mobile.on('pageerror', lambda error: errors.append(str(error)))
        mobile.add_init_script(path=str(ROOT / 'tests/mock_device.js'))
        mobile.goto(url)
        expect(mobile.locator('#co2')).to_have_text('637')
        for tab in ['live', 'settings', 'runtime', 'calibration']:
            mobile.locator(f'[data-tab="{tab}"]').click()
            assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow in {tab}'
            mobile.screenshot(path=str(ARTIFACTS / f'mobile-{tab}.png'), full_page=True)
        passed('All four tabs fit a 390-pixel phone without horizontal scrolling')
        assert not errors, errors
        passed('No JavaScript exceptions across interaction and recovery scenarios')
        browser.close()
finally:
    server.shutdown()

(ARTIFACTS / 'dashboard-results.json').write_text(json.dumps({'passed': checks, 'hardware': False}, indent=2) + '\n')
print(f'{len(checks)} dashboard scenarios passed; screenshots: {ARTIFACTS}')
