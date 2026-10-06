# QC summary

Source: `aqi_station_daily.csv` — 179,237 station-days, 579 stations, 01 Sep 2025 to 31 Aug 2026.

## Row-level flags

| Flag | Rule | Rows | % of rows | Stations affected |
|---|---|---:|---:|---:|
| `flag_flatline` | >= 5 identical consecutive daily PM2.5/PM10 values | 529 | 0.30% | 21 |
| `flag_pm_inversion` | PM2.5 > PM10 on the same day | 168 | 0.09% | 79 |
| `flag_extreme_o3` | 8-hour O3 max > 400 ug/m3 | 13 | 0.01% | 7 |
| `flag_extreme_pm` | PM2.5 > 600 or PM10 > 1000 ug/m3 | 1 | 0.00% | 1 |
| **`flag_any`** | any of the above | **711** | **0.40%** | **103** |

Valid AQI days before QC: 164,791  ->  after QC (`aqi_qc`): 164,080 (711 removed).

## Station-level verdict

- stations in file: **579**
- any flat-lined days (run >= 5): **21** (those days are flagged out, the station is kept)
- instrument treated as broken (>= 30 flat-lined days or AQI std < 5): **6**
- below 273 valid AQI days after flags: **183**

- **ranking panel** (>= 273 days, >= 9 months with >= 15 days, instrument sound): **396 stations** — use for annual means and top-N tables
- **map panel** (>= 182 days, instrument sound): **488 stations** — use for spatial maps and hotspot surfaces

### Stations excluded even from the map panel

| Station | City | State | Valid AQI days | Flat-lined days | Reason |
|---|---|---|---:|---:|---|
| Haji Colony, Raichur - KSPCB | Raichur | Karnataka | 0 | 0 | coverage below 50% |
| Deshpande Nagar, Hubballi - KSPCB | Hubballi | Karnataka | 3 | 0 | coverage below 50% |
| Wave City, Ghaziabad - UPPCB | Ghaziabad | Uttar Pradesh | 4 | 0 | broken instrument, coverage below 50% |
| Nagar Palika Parishad, Baraut - UPPCB | Baraut | Uttar Pradesh | 10 | 0 | coverage below 50% |
| Naubad, Bidar - KSPCB | Bidar | Karnataka | 17 | 0 | coverage below 50% |
| Skara Yokma, Leh - LPCC | Leh | Ladakh | 17 | 0 | coverage below 50% |
| Police Line, Sri Vijaya Puram - ANPCC | Sri Vijaya Puram | Andaman and Nicobar | 17 | 0 | coverage below 50% |
| Chinna Bharatham Colony, Srikakulam - APPCB | Srikakulam | Andhra Pradesh | 18 | 0 | coverage below 50% |
| B.Katihalli, Hassan - KSPCB | Hassan | Karnataka | 21 | 0 | coverage below 50% |
| Brahmagiri, Udupi - KSPCB | Udupi | Karnataka | 24 | 0 | coverage below 50% |
| Rama Rao Peta, Kakinada - APPCB | Kakinada | Andhra Pradesh | 25 | 0 | coverage below 50% |
| Rajanpur, Gajraula - UPPCB | Gajraula | Uttar Pradesh | 28 | 0 | coverage below 50% |
| Vigyan Nagar, Alwar - RSPCB | Alwar | Rajasthan | 31 | 0 | coverage below 50% |
| New Tehsil, Shamli - UPPCB | Shamli | Uttar Pradesh | 32 | 0 | coverage below 50% |
| Ashwini Nagar, Haveri - KSPCB | Haveri | Karnataka | 32 | 0 | coverage below 50% |
| Anand Nagar, Raebareli - UPPCB | Raebareli | Uttar Pradesh | 34 | 0 | coverage below 50% |
| VOC Nagar_SIPCOT, Ranipet - TNPCB | Ranipet | Tamil Nadu | 34 | 0 | coverage below 50% |
| Gandhi Nagar_Ennore, Chennai - TNPCB | Chennai | Tamil Nadu | 38 | 0 | coverage below 50% |
| New Anaj Mandi, Khairthal - RSPCB | Khairthal | Rajasthan | 43 | 0 | coverage below 50% |
| Ponnusamy Nagar, Namakkal - TNPCB | Namakkal | Tamil Nadu | 50 | 0 | coverage below 50% |
| Vasanthapuram, Vellore - TNPCB | Vellore | Tamil Nadu | 51 | 0 | coverage below 50% |
| Sita Rama Nagar, Kurnool - APPCB | Kurnool | Andhra Pradesh | 54 | 0 | coverage below 50% |
| Kilambi, Kanchipuram - TNPCB | Kanchipuram | Tamil Nadu | 55 | 0 | coverage below 50% |
| Indira Nagar, Raebareli - NTPC Unchahar | Raebareli | Uttar Pradesh | 57 | 0 | coverage below 50% |
| Vasai West, Mumbai - MPCB | Mumbai | Maharashtra | 58 | 0 | coverage below 50% |
| Pali Dungra, Mathura - UPPCB | Mathura | Uttar Pradesh | 59 | 0 | coverage below 50% |
| Dadupura, Fatehpur Sikri - UPPCB | Fatehpur Sikri | Uttar Pradesh | 61 | 0 | coverage below 50% |
| Alandur Bus Depot, Chennai - CPCB | Chennai | Tamil Nadu | 64 | 0 | coverage below 50% |
| Sona College of Technology, Salem - TNPCB | Salem | Tamil Nadu | 66 | 0 | coverage below 50% |
| Crescent University, Chengalpattu - TNPCB | Chengalpattu | Tamil Nadu | 66 | 0 | coverage below 50% |
| Lal Bahadur Shastri Nagar, Kalaburagi - KSPCB | Kalaburagi | Karnataka | 66 | 0 | coverage below 50% |
| St Joseph College, Tiruchirappalli - TNPCB | Tiruchirappalli | Tamil Nadu | 72 | 0 | coverage below 50% |
| Velippalayam, Nagapattinam - TNPCB | Nagapattinam | Tamil Nadu | 76 | 0 | coverage below 50% |
| Bharathidasan University, Palkalaiperur - TNPCB | Palkalaiperur | Tamil Nadu | 78 | 0 | coverage below 50% |
| Municipal Corporation Office, Tirunelveli - TNPCB | Tirunelveli | Tamil Nadu | 79 | 0 | coverage below 50% |
| KHB Colony, Karwar - KSPCB | Karwar | Karnataka | 80 | 0 | coverage below 50% |
| 15th Mile-Nongthymmai, Byrnihat -Meghalaya PCB | Byrnihat | Meghalaya | 81 | 5 | coverage below 50% |
| JN Stadium, Shillong - Meghalaya PCB | Shillong | Meghalaya | 84 | 0 | coverage below 50% |
| Bombay Castel, Ooty - TNPCB | Ooty | Tamil Nadu | 84 | 6 | coverage below 50% |
| Keelapalur, Ariyalur - TNPCB | Ariyalur | Tamil Nadu | 84 | 0 | coverage below 50% |
| Collectorate Office, Virudhunagar - TNPCB | Virudhunagar | Tamil Nadu | 87 | 0 | coverage below 50% |
| RVCE-Mailasandra, Bengaluru - KSPCB | Bengaluru | Karnataka | 93 | 0 | coverage below 50% |
| Kumaran College, Tirupur - TNPCB | Tirupur | Tamil Nadu | 102 | 0 | coverage below 50% |
| Parisutham Nagar, Thanjavur - TNPCB | Thanjavur | Tamil Nadu | 103 | 0 | coverage below 50% |
| Lodhi Road, Delhi - IITM | Delhi | Delhi | 107 | 0 | coverage below 50% |
| Koyana Nagar, Satara - MPCB | Satara | Maharashtra | 107 | 0 | coverage below 50% |
| Govindpuram, Ghaziabad - UPPCB | Ghaziabad | Uttar Pradesh | 109 | 0 | coverage below 50% |
| Mendonsa Colony, Dindigul - TNPCB | Dindigul | Tamil Nadu | 111 | 0 | coverage below 50% |
| Ved Vihar-Loni, Ghaziabad - UPPCB | Ghaziabad | Uttar Pradesh | 116 | 0 | coverage below 50% |
| Thimmalapura, Tumakuru - KSPCB | Tumakuru | Karnataka | 119 | 0 | coverage below 50% |
| MIET College, Meerut - UPPCB | Meerut | Uttar Pradesh | 119 | 0 | coverage below 50% |
| SRM University, Modinagar - UPPCB | Modinagar | Uttar Pradesh | 123 | 0 | coverage below 50% |
| Devaraj Urs Badavane, Davanagere - KSPCB | Davanagere | Karnataka | 126 | 0 | coverage below 50% |
| Panchal Nagar, Gadag - KSPCB | Gadag | Karnataka | 127 | 0 | coverage below 50% |
| Kamadenu Nagar, Karur - TNPCB | Karur | Tamil Nadu | 128 | 0 | coverage below 50% |
| SIPCOT Nathampannai, Pudukottai - TNPCB | Pudukottai | Tamil Nadu | 128 | 0 | coverage below 50% |
| Ramteerth Nagar, Belgaum - KSPCB | Belgaum | Karnataka | 132 | 0 | coverage below 50% |
| Prashant Garden, Khora - UPPCB | Khora | Uttar Pradesh | 137 | 0 | coverage below 50% |
| Ambedkar Nagar, Nellore - APPCB | Nellore | Andhra Pradesh | 139 | 0 | coverage below 50% |
| Diwator Nagar, Koppal - KSPCB | Koppal | Karnataka | 141 | 0 | coverage below 50% |
| Sector-53, Chandigarh - CPCC | Chandigarh | Chandigarh | 141 | 0 | coverage below 50% |
| Uchapatti, Madurai - TNPCB | Madurai | Tamil Nadu | 145 | 0 | coverage below 50% |
| Chinchpada, Ambernath - MPCB | Ambernath | Maharashtra | 147 | 0 | coverage below 50% |
| Kudikadu, Cuddalore - TNPCB | Cuddalore | Tamil Nadu | 148 | 0 | coverage below 50% |
| Chalai Bazaar, Ramanathapuram - TNPCB | Ramanathapuram | Tamil Nadu | 149 | 0 | coverage below 50% |
| Deen Dayal Nagar, Sagar - MPPCB | Sagar | Madhya Pradesh | 151 | 0 | coverage below 50% |
| Kandivali East, Mumbai - MPCB | Mumbai | Maharashtra | 155 | 15 | coverage below 50% |
| Ashta Vinayak Nagar, Hingoli - MPCB | Hingoli | Maharashtra | 158 | 0 | coverage below 50% |
| District Court, Eluru - APPCB | Eluru | Andhra Pradesh | 160 | 0 | coverage below 50% |
| Polayathode, Kollam - Kerala PCB | Kollam | Kerala | 161 | 0 | coverage below 50% |
| Vithalwadi, Ulhasnagar - MPCB | Ulhasnagar | Maharashtra | 162 | 0 | coverage below 50% |
| Talkatora Garden, Delhi - DPCC | Delhi | Delhi | 162 | 0 | coverage below 50% |
| Srinivas Nagar Colony, Machilipatnam - APPCB | Machilipatnam | Andhra Pradesh | 162 | 0 | coverage below 50% |
| Bir, Beed - MPCB | Beed | Maharashtra | 163 | 0 | coverage below 50% |
| Kalu Nagar, Dombivli - MPCB | Dombivli | Maharashtra | 164 | 0 | coverage below 50% |
| Tata Stadium, Jorapokhar - JSPCB | Jorapokhar | Jharkhand | 165 | 0 | coverage below 50% |
| Rajendra Nagar North, Guntur - APPCB | Guntur | Andhra Pradesh | 168 | 0 | coverage below 50% |
| Shivaji Nagar, Rishikesh - UKPCB | Rishikesh | Uttarakhand | 169 | 144 | broken instrument, coverage below 50% |
| Bollaram Industrial Area, Hyderabad - TSPCB | Hyderabad | Telangana | 172 | 0 | coverage below 50% |
| Udyogamandal, Eloor - Kerala PCB | Eloor | Kerala | 176 | 0 | coverage below 50% |
| Commonwealth Sports Complex, Delhi - DPCC | Delhi | Delhi | 176 | 0 | coverage below 50% |
| Sector-2, Rourkela - OSPCB | Rourkela | Odisha | 176 | 47 | broken instrument, coverage below 50% |
| NSUT Jaffarpur, Delhi - DPCC | Delhi | Delhi | 177 | 0 | coverage below 50% |
| Cantonment Area, Delhi - DPCC | Delhi | Delhi | 177 | 0 | coverage below 50% |
| Urban Estate-II, Hisar - HSPCB | Hisar | Haryana | 179 | 0 | coverage below 50% |
| IGNOU_Maidan Garhi, Delhi - DPCC | Delhi | Delhi | 179 | 0 | coverage below 50% |
| Kanuru, Vijayawada - APPCB | Vijayawada | Andhra Pradesh | 179 | 0 | coverage below 50% |
| JNU, Delhi - DPCC | Delhi | Delhi | 181 | 0 | coverage below 50% |
| Murthal, Sonipat - HSPCB | Sonipat | Haryana | 199 | 71 | broken instrument |
| Arya Nagar, Bahadurgarh - HSPCB | Bahadurgarh | Haryana | 236 | 60 | broken instrument |
| Velachery Res. Area, Chennai - CPCB | Chennai | Tamil Nadu | 249 | 56 | broken instrument |

## Notes carried over from the source data

- 15 August 2026 is missing for every station: the CPCB feed carries the timestamps but all values are NA (nationwide transmission gap), so the year has 364 days.
- 579 of the 605 stations in the CPCB network appear here; 16 publish no hourly file and 10 have no usable readings in the window.
- AQI is blank wherever CPCB's rule is not met (fewer than three pollutants, or no PM2.5/PM10). These are genuine gaps and are not imputed.
- Active stations grow from 471 (Sep 2025) to 540 (Aug 2026), so national trend lines should use a fixed station panel or city medians.
- Group cities as (state, city): Aurangabad and Byrnihat each occur in two states.

Written by `scripts/qc_flags.py`. Original `aqi_station_daily.csv` is unchanged; use `aqi_station_daily_qc.csv` and the `aqi_qc` column for analysis.