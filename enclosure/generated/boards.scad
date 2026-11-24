// Generated from pinned Adafruit Eagle PCB files; units mm.
// See hardware/reference/manifest.json and ATTRIBUTION.md.
feather_size = [50.8, 22.86];
feather_holes = [[2.54, 2.54, 2.5], [2.54, 20.32, 2.5], [48.26, 1.8415, 2.2], [48.26, 20.955, 2.2]];
scd30_size = [50.8, 25.4];
scd30_holes = [[2.54, 2.54, 2.5], [2.54, 22.86, 2.5], [48.26, 2.54, 2.5], [48.26, 22.86, 2.5]];
veml7700_size = [25.4, 17.78];
veml7700_holes = [[2.54, 2.54, 2.5], [2.54, 15.24, 2.5], [22.86, 2.54, 2.5], [22.86, 15.24, 2.5]];
rtc_size = [25.4, 17.78];
rtc_holes = [[2.54, 15.24, 3.0], [22.86, 15.24, 3.0]];
tsl2591_size = [25.4, 17.78];
tsl2591_holes = [[2.54, 2.54, 2.5], [2.54, 15.24, 2.5], [22.86, 2.54, 2.5], [22.86, 15.24, 2.5]];
feather_buttons = [[7.62, 4.445], [7.62, 11.43], [7.62, 18.415]];
feather_reset = [44.45, 11.43];
// Display glass outline from the mirrored DISP1 package.
feather_glass = [11.291, 2.503, 31, 17.6];
feather_active = [12.891, 3.903, 24.9, 14.8];
veml7700_package_center = [12.7, 13.716];
tsl2591_package_center = [12.7, 8.89];
veml7700_optic = [12.7, 13.716];
tsl2591_optic = [12.7, 9.26];
light_size = light_sensor == "tsl2591" ? tsl2591_size : veml7700_size;
light_holes = light_sensor == "tsl2591" ? tsl2591_holes : veml7700_holes;
light_optic = light_sensor == "tsl2591" ? tsl2591_optic : veml7700_optic;
light_package_center = light_sensor == "tsl2591" ? tsl2591_package_center : veml7700_package_center;
light_package_size = light_sensor == "tsl2591" ? [2, 2.4, 0.65] : [6.8, 3, 2.35];
tsl2591_components = [[6.304, 4.965, 3.14, 1.5, 2.0], [6.7056, 6.8629, 2.8448, 3.8002, 2.0], [6.558, 11.442, 3.14, 1.5, 2.0], [10.4235, 5.215, 2.775, 1.0, 2.0], [15.545, 10.13, 3.2, 2.6, 2.0], [15.741, 6.493, 2.3, 2.0, 2.0], [2.406, 12.173, 2.3, 0.8, 2.0], [5.088, 11.0585, 1.0, 2.775, 2.0]];
