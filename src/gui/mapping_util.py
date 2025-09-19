import math
import os
import time

import folium
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_ip_location(ip=None):
	# Use ipinfo.io for geolocation
	url = f"https://ipinfo.io/{ip or ''}/json"
	resp = requests.get(url)
	data = resp.json()
	loc = data.get("loc", None)
	if loc:
		lat, lon = map(float, loc.split(","))
		return lat, lon, data
	return None, None, data

# TODO update to utilize geo position not just IP
def plot_ip_on_map(ip=None, map_file="ip_map.html", radius_nmi=27):
	lat, lon, info = get_ip_location(ip)
	if lat is None or lon is None:
		print("Could not determine location for IP:", ip)
		return
	# start with a reasonable default zoom; we'll auto-fit to the circle below
	m = folium.Map(location=[lat, lon], zoom_start=10)
	# Convert nautical miles to meters (1 nmi = 1852 meters)
	radius_m = radius_nmi * 1852
	folium.Circle(
		location=[lat, lon],
		radius=radius_m,
		color='blue',
		fill=True,
		fill_opacity=0.2,
		popup=f"IP: {info.get('ip', ip)}\n{info.get('city','')}, {info.get('region','')}, {info.get('country','')}\nRadius: {radius_nmi} nmi"
	).add_to(m)
	# Auto-expand map to fit the circle: compute lat/lon degree deltas from radius
	# 1 deg latitude ~= 111.32 km
	dlat = radius_m / 111320.0
	# longitude degrees scale by cos(latitude)
	dlon = radius_m / (111320.0 * math.cos(math.radians(lat))) if math.cos(math.radians(lat)) != 0 else radius_m / 111320.0
	sw = [lat - dlat, lon - dlon]
	ne = [lat + dlat, lon + dlon]
	m.fit_bounds([sw, ne])
	return m, lat, lon, info

def save_map(m, filename, format='html', delay=2):
	"""
	Save folium map as HTML or PNG.
	format: 'html' or 'png'
	delay: seconds to wait for map to render before screenshot (PNG only)
	Requires: selenium, chromedriver (in PATH)
	"""
	if format == 'html':
		m.save(filename)
		print(f"Map saved to {filename} (HTML)")
	elif format == 'png':
		tmp_html = filename + '.tmp.html'
		m.save(tmp_html)
		# Set up headless Chrome
		options = Options()
		options.add_argument('--headless')
		options.add_argument('--disable-gpu')
		options.add_argument('--window-size=1200,800')
		driver = webdriver.Chrome(options=options)
		driver.get('file://' + os.path.abspath(tmp_html))
		time.sleep(delay)  # Wait for map to render
		driver.save_screenshot(filename)
		driver.quit()
		os.remove(tmp_html)
		print(f"Map saved to {filename} (PNG)")
	else:
		raise ValueError("format must be 'html' or 'png'")

if __name__ == "__main__":
	# Use your public IP by default, or specify one
	m, lat, lon, info = plot_ip_on_map(radius_nmi=10)
	# Save as HTML
	save_map(m, "ip_map.html", format='html')
	# Save as PNG (requires selenium and chromedriver)
	save_map(m, "ip_map.png", format='png')
