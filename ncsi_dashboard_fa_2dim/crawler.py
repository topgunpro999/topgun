import requests
from bs4 import BeautifulSoup
import json
import os

NCSI_URL = "https://ncsi.ega.ee/ncsi-index/?order=rank"
TOP_N = 20
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "ncsi_top20.json")

# Add or modify country coordinates as needed to match the exact string from the website
COUNTRY_COORDINATES = {
    "United States": (37.0902, -95.7129),
    "United Kingdom": (55.3781, -3.4360),
    "Estonia": (58.5953, 25.0136),
    "Finland": (61.9241, 25.7482),
    "Netherlands": (52.1326, 5.2913),
    "Norway": (60.4720, 8.4689),
    "Sweden": (60.1282, 18.6435),
    "Denmark": (56.2639, 9.5018),
    "Singapore": (1.3521, 103.8198),
    "Lithuania": (55.1694, 23.8813),
    "Czech Republic": (49.8175, 15.4730),
    "Japan": (36.2048, 138.2529),
    "Belgium": (50.8503, 4.3517),
    "Australia": (-25.2744, 133.7751),
    "Germany": (51.1657, 10.4515),
    "Canada": (56.1304, -106.3468),
    # IMPORTANT: Changed from "South Korea" to "Korea (Republic of)" to match crawler output
    "Korea (Republic of)": (35.9078, 127.7669),
    "France": (46.2276, 2.2137),
    "Poland": (51.9194, 19.1451),
    "Latvia": (56.8796, 24.6032),
    "Georgia": (42.3154, 43.3569),
    "Ireland": (53.1424, -7.6921),
    "Portugal": (39.3999, -8.2245),
    "Slovenia": (46.1512, 14.9955),
    "Malaysia": (4.2105, 101.9758),
    "Saudi Arabia": (23.8859, 45.0792),
    "Spain": (40.4637, -3.7493),
    "Austria": (47.5162, 14.5501),
    "Italy": (41.8719, 12.5674),
    "Croatia": (45.1, 15.2),
    "United Arab Emirates": (23.4241, 53.8478),
    "Israel": (31.0461, 34.8516),
    "Romania": (45.9432, 24.9668),
    "Hungary": (47.1625, 19.5033),
    "Turkey": (38.9637, 35.2433),
    "Greece": (39.0742, 21.8243),
    "Ukraine": (48.3794, 31.1656),
    "Brazil": (-14.2350, -51.9253),
    "India": (20.5937, 78.9629),
    "China": (35.8617, 104.1954),
    "Albania": (41.1533, 20.1683),
    "Serbia": (44.0165, 21.0059),
    "Switzerland": (46.8182, 8.2275),
    "Slovakia": (48.6690, 19.6990),
    "Moldova (Republic of)": (47.4116, 28.3699),
    "Cyprus": (35.1264, 33.4299),
    "Jordan": (30.5852, 36.2384),
    "Azerbaijan": (40.1431, 47.5769),
    "South Africa": (-30.5595, 22.9375), # Added
    "New Zealand": (-40.9006, 174.8860), # Added
    "Argentina": (-34.0000, -64.0000), # Added
    "Mexico": (23.6345, -102.5528), # Added
    "Chile": (-35.6751, -71.5430), # Added
    "Colombia": (4.5709, -74.2973), # Added
    "Peru": (-9.1900, -75.0152), # Added
    "Egypt": (26.8206, 30.8025), # Added
    "Morocco": (31.7917, -7.0926), # Added
    "Nigeria": (9.0820, 8.6753), # Added
    "Kenya": (-1.286389, 36.817223), # Added
}


def crawl_ncsi():
    print(f"[Crawler] Starting crawl from URL: {NCSI_URL}")
    countries_data = []
    try:
        response = requests.get(NCSI_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table')
        if not table:
            print("[Crawler ERROR] Could not find the main table on the page. Website structure might have changed significantly.")
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            return []

        rows = table.select('tbody tr')
        print(f"[Crawler] Found {len(rows)} table rows in total.")

        processed_count = 0
        for i, row in enumerate(rows):
            if processed_count >= TOP_N:
                break

            rank_cell = row.select_one('td:nth-child(1)')
            
            country_name = ""
            country_name_td = row.select_one('td:nth-child(3)') 

            if country_name_td:
                country_name_link = country_name_td.select_one('a')
                if country_name_link:
                    country_name = country_name_link.text.strip()
            
            # Use specific CSS classes/selectors for robustness
            security_index_cell = row.select_one('td:nth-child(4) .c-blue-light.value-size')
            digital_level_cell = row.select_one('td:nth-child(5) .value-size')
            difference_cell = row.select_one('td:nth-child(6) .value-size')

            if all([rank_cell, country_name, security_index_cell, digital_level_cell, difference_cell]):
                rank = rank_cell.text.strip().replace('.', '')
                
                try:
                    security_index = float(security_index_cell.text.strip())
                except ValueError:
                    print(f"[Crawler WARNING] Could not parse security_index for {country_name}: '{security_index_cell.text.strip()}'. Skipping row.")
                    continue

                try:
                    digital_level = float(digital_level_cell.text.strip())
                except ValueError:
                    print(f"[Crawler WARNING] Could not parse digital_level for {country_name}: '{digital_level_cell.text.strip()}'. Skipping row.")
                    continue

                difference = difference_cell.text.strip() # Keep as string as it can be negative with '-'

                if country_name in COUNTRY_COORDINATES:
                    lat, lon = COUNTRY_COORDINATES.get(country_name)
                    countries_data.append({
                        "rank": int(rank),
                        "country": country_name,
                        "security_index": security_index,
                        "digital_level": digital_level,
                        "difference": difference,
                        "latitude": lat,
                        "longitude": lon
                    })
                    processed_count += 1
                else:
                    print(f"[Crawler WARNING] Country '{country_name}' (Rank {rank}) not found in COUNTRY_COORDINATES. Skipping.")
            else:
                missing_parts = []
                if not rank_cell: missing_parts.append('rank')
                if not country_name: missing_parts.append('country_name')
                if not security_index_cell: missing_parts.append('security_index')
                if not digital_level_cell: missing_parts.append('digital_level')
                if not difference_cell: missing_parts.append('difference')
                print(f"[Crawler WARNING] Missing one or more expected cells in row {i+1} ({', '.join(missing_parts)}). Skipping row.")


        print(f"[Crawler] Finished processing. Total data collected: {len(countries_data)} items.")
        if not countries_data:
            print("[Crawler WARNING] No valid country data was collected. Check selectors and COUNTRY_COORDINATES.")

        # No need to sort and limit again here, as TOP_N already handled in the loop
        final_countries = countries_data 

        os.makedirs(DATA_DIR, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_countries, f, ensure_ascii=False, indent=4)

        print(f"[Crawler] NCSI 데이터 크롤링 및 상위 {len(final_countries)}개국 정보 저장 완료: {OUTPUT_FILE}")
        return final_countries

    except requests.exceptions.RequestException as e:
        print(f"[Crawler ERROR] Network or HTTP error during crawl: {e}")
        return []
    except Exception as e:
        print(f"[Crawler ERROR] General error during crawl: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    crawl_ncsi()