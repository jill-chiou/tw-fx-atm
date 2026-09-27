<!-- English draft for applicant review; check wording and current data before publishing. -->

# Taiwan Foreign-Currency ATM Map

English | [繁體中文](README.md)

**Live demo: https://jill-chiou.github.io/tw-fx-atm**

An interactive map of foreign-currency ATMs in Taiwan, built from an official 100-plus-page PDF that could not be searched or mapped. The current dataset is based on the FISC list dated 31 August 2026 (refreshed on 27 September 2026): 2,378 locations across 17 banks, of which 2,366 have coordinates and appear on the map. Users can filter by bank and currency and find the nearest ATMs.

**At a glance:** solo project, built May–July 2026, data refreshed June and September 2026 · Python (pdfplumber, requests, BeautifulSoup), SQLite, JavaScript (Leaflet.js), GitHub Pages · no backend and no running costs.

---

## Why I built it

Before a trip abroad, finding an ATM that dispenses foreign currency in Taiwan meant checking bank websites one by one. The complete list already exists: Taiwan's Financial Information Service Co. (FISC), the interbank clearing operator, publishes it — but only as a PDF with no search, filtering, or map.

This project turns that PDF into a service people can actually use.

## What it does

- **Find ATMs near you:** device geolocation with results sorted by distance
- **Filter by bank and currency** (USD, JPY, CNY, HKD, EUR); filters combine, e.g. "Bank A and EUR"
- **Works on any phone:** a static website with no app install, login, or API key
- **Monthly refresh workflow:** an update script compares each new FISC PDF with the current dataset; I run it and check the output by hand

## How it's built

```
FISC PDF (108 pages, list dated 31 August 2026)
  → pdfplumber table extraction → 2,363 rows
  → minus 7 rows the banks confirm are not public or no longer exist
    plus 22 ATMs listed on bank websites but missing from FISC
  → 2,378 locations
  → TGOS batch geocoding (Taiwan's official address geocoder)
      → 2,366 of 2,378 have coordinates (99.5%)
  → currency support for all 17 banks
      (8 scraped programmatically, 8 fixed bank-wide policies confirmed
       on official websites, 1 recorded manually)
  → SQLite pipeline → JSON → Leaflet.js map on GitHub Pages
```

Key decisions:

- **TGOS instead of OpenStreetMap's Nominatim:** it is more accurate for Chinese-language Taiwanese addresses.
- **A static site instead of a hosted backend:** the service costs nothing to run and has no server to maintain or secure.
- **SQLite as the integration layer:** location and currency data from 18 sources are joined in one place, so coverage gaps can be checked with SQL queries.

The technical decision log is in [`docs/`](docs/) (written in Chinese).

## Running it as a service

A map that silently goes stale or shows wrong locations is worse than no map. The operational design:

- **Monthly update script** (`update_from_fisc.py`): downloads the latest FISC PDF, parses it, and compares every field with the current dataset. If nothing changed, it stops. If something changed, locations already known keep their verified coordinates, while new ones are marked `pending` and hidden until geocoded. A missing pin is better than a wrong one.
- **Scrapers fail loudly and never overwrite good data:** each scraper writes its output only after a fully successful run, so a failure cannot corrupt the published data. The merge step keeps the last successful result.
- **Layered coordinate validation:**
  - automated range and sanity checks on every point;
  - a manual audit of 30 randomly sampled locations against Google Maps (30/30 passed in May, which only supports an approximate 95% upper bound of 10% on the error rate; reasoning in [`docs/06`](docs/06-geocoding-validation.md));
  - a cross-check against the coordinates that 8 banks publish themselves (`check_coords_vs_bank.py`). Of 1,949 comparable locations, 89% are within 50 m of the bank's own coordinates and 4.6% are more than 200 m apart. A large gap means the two sources disagree, not that my coordinate is necessarily the wrong one; some bank coordinates are clearly wrong themselves.

  Re-checking the May sample in September turned up one location placed next door. Tracing it showed a systematic cause: when an address lists several street numbers (e.g. "No. 361 & 363"), the geocoder matched a different number in 8 of 9 cases, one of them 14 km away. The 3 cases I could confirm against bank coordinates are corrected through an override list that survives future re-imports.

**What the September 2026 refresh involved:** the new FISC list added 479 rows and removed 82 (Taishin Bank alone grew by about 400 ATMs). The run also caught two silent website changes, both fixed: First Bank's API began returning XML by default, and Cathay United Bank switched to full-width brackets in branch names, which broke name matching. SinoPac's website and the FISC list also disagreed on 11 branches; I treated the FISC list, the official interbank record, as the source of which machines exist, and labelled currencies conservatively where the bank website was silent.

## Known limitations

- **Manual refresh cadence:** refreshes are triggered by hand. None ran between June and 27 September 2026, so FISC changes in that period were not reflected until then.
- **Unresolved coordinate disagreements:** 90 locations are more than 200 m from the bank's own coordinates and have not yet been reviewed one by one; 6 more multi-number addresses have no independent reference to check against.
- **12 locations could not be geocoded** (some addresses contain characters the source PDF cannot render) and are not shown on the map.
- **8 SinoPac branches** are listed by FISC but not on SinoPac's website; they are kept and labelled JPY only, the most common configuration among SinoPac's listed ATMs.
- **No automated alerting:** a bank website redesign breaks that bank's scraper, and the break is found only during the monthly manual run.
- **Bank-wide currency policies:** for 8 banks, per-machine differences cannot be reflected, because the banks do not publish machine-level data.
- **First Bank is marked conservatively:** its website lists CNY/HKD for "some machines" only, so only USD/JPY are shown, which may understate coverage.

## Data sources

| Data | Source | Cadence |
|---|---|---|
| ATM locations | FISC, official list of ATMs that dispense foreign currency (PDF) | Published monthly; refreshed manually here |
| Geocoding | TGOS (Ministry of the Interior geospatial platform), batch address matching | Per refresh |
| Currency support | Official websites of the 17 banks (method documented per bank in `scripts/`) | Per refresh |
