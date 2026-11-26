// Browser test fixture and offline preview only. Never bundled into firmware.
(() => {
  const now = Math.floor(Date.now() / 1000);
  const device = {
    version: '0.1.0-preview', name: 'Greenhouse prototype', token: 'preview-token',
    utc: now, uptime_s: 8400, session: 1305, logging: true, warming: false,
    calibration_due: false, rtc: 'ready', clock_source: 'RTC', sensor: 'SCD30',
    light_sensor: 'TSL2591', sensor_errors: 0, reset_reason: 1,
    live: {co2: 637, temperature: 24.6, humidity: 58.2, lux: 1240, volts: 3.94,
      percent: 78, light_saturated: false, co2_age_bound_s: 2},
    settings: {name: 'Greenhouse prototype', interval_s: 60, sensor_interval_s: 2,
      screen_seconds: 45, wifi_minutes: 10, channels: 31, asc: false,
      temperature_offset_centi: 0, altitude_m: 0, battery_mah: 3500, revision: 1},
    storage: {mounted: true, healthy: true, full: false, records: 140, sequence: 140,
      free_bytes: 1417216, total_bytes: 1441792, record_bytes: 64,
      reserve_bytes: 32768, recovered_bytes: 0, error: ''},
    wifi: {ssid: 'Sensor-DEMO', seconds_left: 598, clients: 1},
    calibration: {active: false, seconds_left: 0, ready: false},
    estimate: {average_ma: 23.805361, measured: false}
  };
  const points = Array.from({length: 120}, (_, i) => ({
    sequence: i + 1, session: 1305, utc: now - (119 - i) * 60, uptime_s: i * 60,
    flags: 1, co2: i === 60 ? null : Math.round(620 + 55 * Math.sin(i / 17) + 13 * Math.cos(i / 4)),
    temperature: 23.5 + Math.sin(i / 38), humidity: 58 + 4 * Math.cos(i / 20),
    lux: Math.round(1100 + 250 * Math.sin(i / 35)), percent: 80 - i / 60
  }));
  const demo = window.DemoDevice = {state: device, points, calls: [], fail: false,
    calibrationStarted: 0, calibrationReady: false};
  const result = (data, status = 200) => Promise.resolve(new Response(JSON.stringify(data), {
    status, headers: {'Content-Type': 'application/json'}
  }));
  window.fetch = (url, options = {}) => {
    const path = new URL(url, location.href).pathname;
    if (demo.fail) return Promise.reject(new Error('Simulated lost connection'));
    const data = options.body ? JSON.parse(options.body) : null;
    demo.calls.push({path, data, headers: options.headers});
    if (data && options.headers['X-Workshop-Token'] !== device.token)
      return result({message: 'Missing device token'}, 403);
    if (path === '/api/status') {
      if (device.calibration.active) {
        const remaining = Math.max(0, 360 - Math.floor((Date.now() - demo.calibrationStarted) / 1000));
        device.calibration.seconds_left = demo.calibrationReady ? 0 : remaining;
        device.calibration.ready = demo.calibrationReady || remaining === 0;
      }
      return result(device);
    }
    if (path === '/api/history') return result({points: demo.points, total_records: device.storage.records, stride: 1});
    if (path === '/api/clock') {device.utc = data.utc; device.rtc = 'ready'; device.clock_source = 'RTC';}
    else if (path === '/api/logging') device.logging = data.enabled;
    else if (path === '/api/settings') {
      if (data.expected_revision !== device.settings.revision)
        return result({message: 'Settings changed since this form was opened. Reload settings and try again.'}, 409);
      if (data.interval_s < data.sensor_interval_s)
        return result({message: 'Log interval must be at least the CO2 sensor cadence.'}, 400);
      if (data.sensor_interval_s !== device.settings.sensor_interval_s && !data.cadence_acknowledged)
        return result({message: 'Changing sensor cadence requires recalibration and temperature-offset review.'}, 400);
      if (data.asc && !device.settings.asc && !data.asc_acknowledged)
        return result({message: 'Confirm fresh air every day before enabling ASC.'}, 400);
      device.calibration_due ||= data.sensor_interval_s !== device.settings.sensor_interval_s;
      for (const key of Object.keys(device.settings)) if (key in data) device.settings[key] = data[key];
      device.settings.revision++; device.name = data.name;
    }
    else if (path === '/api/wifi/extend') device.wifi.seconds_left = device.settings.wifi_minutes * 60;
    else if (path === '/api/calibration/start') {
      demo.calibrationStarted = Date.now(); demo.calibrationReady = false;
      device.calibration = {active: true, seconds_left: 360, ready: false};
    }
    else if (path === '/api/calibration/cancel') device.calibration = {active: false, seconds_left: 0, ready: false};
    else if (path === '/api/calibration/apply') {
      if (!device.calibration.ready || !data.confirmed || data.reference_ppm < 400 || data.reference_ppm > 2000)
        return result({message: 'Wait for stabilisation and confirm the reference.'}, 409);
      device.calibration = {active: false, seconds_left: 0, ready: false}; device.calibration_due = false;
    }
    else if (path === '/api/storage/erase') {
      if (device.logging || device.calibration.active || data.confirmation !== 'ERASE')
        return result({message: 'Pause logging and type ERASE first.'}, 409);
      demo.points = []; device.storage.records = 0; device.storage.free_bytes = 1433600;
    }
    else return result({message: 'Unknown preview endpoint'}, 404);
    return result({ok: true, message: 'Preview updated — no hardware changed.'});
  };
  document.addEventListener('click', event => {
    const link = event.target.closest('a[download]');
    if (!link || !link.getAttribute('href').startsWith('/api/download')) return;
    event.preventDefault();
    const csv = 'sequence,timestamp_utc,co2_ppm,temperature_c,humidity_pct,illuminance_lux\r\n' +
      demo.points.map(p => [p.sequence, new Date(p.utc * 1000).toISOString(), p.co2,
        p.temperature, p.humidity, p.lux].join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], {type: 'text/csv'}));
    const a = document.createElement('a'); a.href = url; a.download = 'SIMULATED-preview.csv'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
