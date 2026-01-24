"""Seed travel data (UN countries, TCC destinations, microstates, visits)

Revision ID: 006
Revises: 005
Create Date: 2026-01-24

This migration seeds all travel reference data:
- 193 UN countries with continents
- 330 TCC destinations with UN country mappings
- 32 microstates (small countries needing map markers)
- 125 visits with first visit dates

NomadMania regions are NOT seeded here - use admin upload instead.
"""

from alembic import op
from sqlalchemy import text


revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


# UN countries: (name, iso_alpha2, iso_alpha3, iso_numeric, map_region_codes, continent)
UN_COUNTRIES = [
    ("Afghanistan", "AF", "AFG", "004", "004", "Asia"),
    ("Albania", "AL", "ALB", "008", "008", "Europe"),
    ("Algeria", "DZ", "DZA", "012", "012", "Africa"),
    ("Andorra", "AD", "AND", "020", "020", "Europe"),
    ("Angola", "AO", "AGO", "024", "024", "Africa"),
    ("Antigua and Barbuda", "AG", "ATG", "028", "028", "North America"),
    ("Argentina", "AR", "ARG", "032", "032", "South America"),
    ("Armenia", "AM", "ARM", "051", "051", "Asia"),
    ("Australia", "AU", "AUS", "036", "036", "Oceania"),
    ("Austria", "AT", "AUT", "040", "040", "Europe"),
    ("Azerbaijan", "AZ", "AZE", "031", "031", "Asia"),
    ("Bahamas", "BS", "BHS", "044", "044", "North America"),
    ("Bahrain", "BH", "BHR", "048", "048", "Asia"),
    ("Bangladesh", "BD", "BGD", "050", "050", "Asia"),
    ("Barbados", "BB", "BRB", "052", "052", "North America"),
    ("Belarus", "BY", "BLR", "112", "112", "Europe"),
    ("Belgium", "BE", "BEL", "056", "056", "Europe"),
    ("Belize", "BZ", "BLZ", "084", "084", "North America"),
    ("Benin", "BJ", "BEN", "204", "204", "Africa"),
    ("Bhutan", "BT", "BTN", "064", "064", "Asia"),
    ("Bolivia", "BO", "BOL", "068", "068", "South America"),
    ("Bosnia and Herzegovina", "BA", "BIH", "070", "070", "Europe"),
    ("Botswana", "BW", "BWA", "072", "072", "Africa"),
    ("Brazil", "BR", "BRA", "076", "076", "South America"),
    ("Brunei", "BN", "BRN", "096", "096", "Asia"),
    ("Bulgaria", "BG", "BGR", "100", "100", "Europe"),
    ("Burkina Faso", "BF", "BFA", "854", "854", "Africa"),
    ("Burundi", "BI", "BDI", "108", "108", "Africa"),
    ("Cabo Verde", "CV", "CPV", "132", "132", "Africa"),
    ("Cambodia", "KH", "KHM", "116", "116", "Asia"),
    ("Cameroon", "CM", "CMR", "120", "120", "Africa"),
    ("Canada", "CA", "CAN", "124", "124", "North America"),
    ("Central African Republic", "CF", "CAF", "140", "140", "Africa"),
    ("Chad", "TD", "TCD", "148", "148", "Africa"),
    ("Chile", "CL", "CHL", "152", "152", "South America"),
    ("China", "CN", "CHN", "156", "156", "Asia"),
    ("Colombia", "CO", "COL", "170", "170", "South America"),
    ("Comoros", "KM", "COM", "174", "174", "Africa"),
    ("Congo", "CG", "COG", "178", "178", "Africa"),
    ("Congo (DRC)", "CD", "COD", "180", "180", "Africa"),
    ("Costa Rica", "CR", "CRI", "188", "188", "North America"),
    ("Croatia", "HR", "HRV", "191", "191", "Europe"),
    ("Cuba", "CU", "CUB", "192", "192", "North America"),
    ("Cyprus", "CY", "CYP", "196", "196", "Europe"),
    ("Czech Republic", "CZ", "CZE", "203", "203", "Europe"),
    ("Denmark", "DK", "DNK", "208", "208,304", "Europe"),
    ("Djibouti", "DJ", "DJI", "262", "262", "Africa"),
    ("Dominica", "DM", "DMA", "212", "212", "North America"),
    ("Dominican Republic", "DO", "DOM", "214", "214", "North America"),
    ("Ecuador", "EC", "ECU", "218", "218", "South America"),
    ("Egypt", "EG", "EGY", "818", "818", "Africa"),
    ("El Salvador", "SV", "SLV", "222", "222", "North America"),
    ("Equatorial Guinea", "GQ", "GNQ", "226", "226", "Africa"),
    ("Eritrea", "ER", "ERI", "232", "232", "Africa"),
    ("Estonia", "EE", "EST", "233", "233", "Europe"),
    ("Eswatini", "SZ", "SWZ", "748", "748", "Africa"),
    ("Ethiopia", "ET", "ETH", "231", "231", "Africa"),
    ("Fiji", "FJ", "FJI", "242", "242", "Oceania"),
    ("Finland", "FI", "FIN", "246", "246", "Europe"),
    ("France", "FR", "FRA", "250", "250,254", "Europe"),
    ("Gabon", "GA", "GAB", "266", "266", "Africa"),
    ("Gambia", "GM", "GMB", "270", "270", "Africa"),
    ("Georgia", "GE", "GEO", "268", "268", "Asia"),
    ("Germany", "DE", "DEU", "276", "276", "Europe"),
    ("Ghana", "GH", "GHA", "288", "288", "Africa"),
    ("Greece", "GR", "GRC", "300", "300", "Europe"),
    ("Grenada", "GD", "GRD", "308", "308", "North America"),
    ("Guatemala", "GT", "GTM", "320", "320", "North America"),
    ("Guinea", "GN", "GIN", "324", "324", "Africa"),
    ("Guinea-Bissau", "GW", "GNB", "624", "624", "Africa"),
    ("Guyana", "GY", "GUY", "328", "328", "South America"),
    ("Haiti", "HT", "HTI", "332", "332", "North America"),
    ("Honduras", "HN", "HND", "340", "340", "North America"),
    ("Hungary", "HU", "HUN", "348", "348", "Europe"),
    ("Iceland", "IS", "ISL", "352", "352", "Europe"),
    ("India", "IN", "IND", "356", "356", "Asia"),
    ("Indonesia", "ID", "IDN", "360", "360", "Asia"),
    ("Iran", "IR", "IRN", "364", "364", "Asia"),
    ("Iraq", "IQ", "IRQ", "368", "368", "Asia"),
    ("Ireland", "IE", "IRL", "372", "372", "Europe"),
    ("Israel", "IL", "ISR", "376", "376", "Asia"),
    ("Italy", "IT", "ITA", "380", "380", "Europe"),
    ("Ivory Coast", "CI", "CIV", "384", "384", "Africa"),
    ("Jamaica", "JM", "JAM", "388", "388", "North America"),
    ("Japan", "JP", "JPN", "392", "392", "Asia"),
    ("Jordan", "JO", "JOR", "400", "400", "Asia"),
    ("Kazakhstan", "KZ", "KAZ", "398", "398", "Asia"),
    ("Kenya", "KE", "KEN", "404", "404", "Africa"),
    ("Kiribati", "KI", "KIR", "296", "296", "Oceania"),
    ("Kuwait", "KW", "KWT", "414", "414", "Asia"),
    ("Kyrgyzstan", "KG", "KGZ", "417", "417", "Asia"),
    ("Laos", "LA", "LAO", "418", "418", "Asia"),
    ("Latvia", "LV", "LVA", "428", "428", "Europe"),
    ("Lebanon", "LB", "LBN", "422", "422", "Asia"),
    ("Lesotho", "LS", "LSO", "426", "426", "Africa"),
    ("Liberia", "LR", "LBR", "430", "430", "Africa"),
    ("Libya", "LY", "LBY", "434", "434", "Africa"),
    ("Liechtenstein", "LI", "LIE", "438", "438", "Europe"),
    ("Lithuania", "LT", "LTU", "440", "440", "Europe"),
    ("Luxembourg", "LU", "LUX", "442", "442", "Europe"),
    ("Madagascar", "MG", "MDG", "450", "450", "Africa"),
    ("Malawi", "MW", "MWI", "454", "454", "Africa"),
    ("Malaysia", "MY", "MYS", "458", "458", "Asia"),
    ("Maldives", "MV", "MDV", "462", "462", "Asia"),
    ("Mali", "ML", "MLI", "466", "466", "Africa"),
    ("Malta", "MT", "MLT", "470", "470", "Europe"),
    ("Marshall Islands", "MH", "MHL", "584", "584", "Oceania"),
    ("Mauritania", "MR", "MRT", "478", "478", "Africa"),
    ("Mauritius", "MU", "MUS", "480", "480", "Africa"),
    ("Mexico", "MX", "MEX", "484", "484", "North America"),
    ("Micronesia", "FM", "FSM", "583", "583", "Oceania"),
    ("Moldova", "MD", "MDA", "498", "498", "Europe"),
    ("Monaco", "MC", "MCO", "492", "492", "Europe"),
    ("Mongolia", "MN", "MNG", "496", "496", "Asia"),
    ("Montenegro", "ME", "MNE", "499", "499", "Europe"),
    ("Morocco", "MA", "MAR", "504", "504,732", "Africa"),
    ("Mozambique", "MZ", "MOZ", "508", "508", "Africa"),
    ("Myanmar", "MM", "MMR", "104", "104", "Asia"),
    ("Namibia", "NA", "NAM", "516", "516", "Africa"),
    ("Nauru", "NR", "NRU", "520", "520", "Oceania"),
    ("Nepal", "NP", "NPL", "524", "524", "Asia"),
    ("Netherlands", "NL", "NLD", "528", "528", "Europe"),
    ("New Zealand", "NZ", "NZL", "554", "554", "Oceania"),
    ("Nicaragua", "NI", "NIC", "558", "558", "North America"),
    ("Niger", "NE", "NER", "562", "562", "Africa"),
    ("Nigeria", "NG", "NGA", "566", "566", "Africa"),
    ("North Korea", "KP", "PRK", "408", "408", "Asia"),
    ("North Macedonia", "MK", "MKD", "807", "807", "Europe"),
    ("Norway", "NO", "NOR", "578", "578", "Europe"),
    ("Oman", "OM", "OMN", "512", "512", "Asia"),
    ("Pakistan", "PK", "PAK", "586", "586", "Asia"),
    ("Palau", "PW", "PLW", "585", "585", "Oceania"),
    ("Panama", "PA", "PAN", "591", "591", "North America"),
    ("Papua New Guinea", "PG", "PNG", "598", "598", "Oceania"),
    ("Paraguay", "PY", "PRY", "600", "600", "South America"),
    ("Peru", "PE", "PER", "604", "604", "South America"),
    ("Philippines", "PH", "PHL", "608", "608", "Asia"),
    ("Poland", "PL", "POL", "616", "616", "Europe"),
    ("Portugal", "PT", "PRT", "620", "620", "Europe"),
    ("Qatar", "QA", "QAT", "634", "634", "Asia"),
    ("Romania", "RO", "ROU", "642", "642", "Europe"),
    ("Russia", "RU", "RUS", "643", "643", "Europe"),
    ("Rwanda", "RW", "RWA", "646", "646", "Africa"),
    ("Saint Kitts and Nevis", "KN", "KNA", "659", "659", "North America"),
    ("Saint Lucia", "LC", "LCA", "662", "662", "North America"),
    ("Saint Vincent and the Grenadines", "VC", "VCT", "670", "670", "North America"),
    ("Samoa", "WS", "WSM", "882", "882", "Oceania"),
    ("San Marino", "SM", "SMR", "674", "674", "Europe"),
    ("Sao Tome and Principe", "ST", "STP", "678", "678", "Africa"),
    ("Saudi Arabia", "SA", "SAU", "682", "682", "Asia"),
    ("Senegal", "SN", "SEN", "686", "686", "Africa"),
    ("Serbia", "RS", "SRB", "688", "688", "Europe"),
    ("Seychelles", "SC", "SYC", "690", "690", "Africa"),
    ("Sierra Leone", "SL", "SLE", "694", "694", "Africa"),
    ("Singapore", "SG", "SGP", "702", "702", "Asia"),
    ("Slovakia", "SK", "SVK", "703", "703", "Europe"),
    ("Slovenia", "SI", "SVN", "705", "705", "Europe"),
    ("Solomon Islands", "SB", "SLB", "090", "090", "Oceania"),
    ("Somalia", "SO", "SOM", "706", "706,-3", "Africa"),
    ("South Africa", "ZA", "ZAF", "710", "710", "Africa"),
    ("South Korea", "KR", "KOR", "410", "410", "Asia"),
    ("South Sudan", "SS", "SSD", "728", "728", "Africa"),
    ("Spain", "ES", "ESP", "724", "724", "Europe"),
    ("Sri Lanka", "LK", "LKA", "144", "144", "Asia"),
    ("Sudan", "SD", "SDN", "729", "729", "Africa"),
    ("Suriname", "SR", "SUR", "740", "740", "South America"),
    ("Sweden", "SE", "SWE", "752", "752", "Europe"),
    ("Switzerland", "CH", "CHE", "756", "756", "Europe"),
    ("Syria", "SY", "SYR", "760", "760", "Asia"),
    ("Tajikistan", "TJ", "TJK", "762", "762", "Asia"),
    ("Tanzania", "TZ", "TZA", "834", "834", "Africa"),
    ("Thailand", "TH", "THA", "764", "764", "Asia"),
    ("Timor-Leste", "TL", "TLS", "626", "626", "Asia"),
    ("Togo", "TG", "TGO", "768", "768", "Africa"),
    ("Tonga", "TO", "TON", "776", "776", "Oceania"),
    ("Trinidad and Tobago", "TT", "TTO", "780", "780", "North America"),
    ("Tunisia", "TN", "TUN", "788", "788", "Africa"),
    ("Turkey", "TR", "TUR", "792", "792", "Asia"),
    ("Turkmenistan", "TM", "TKM", "795", "795", "Asia"),
    ("Tuvalu", "TV", "TUV", "798", "798", "Oceania"),
    ("Uganda", "UG", "UGA", "800", "800", "Africa"),
    ("Ukraine", "UA", "UKR", "804", "804", "Europe"),
    ("United Arab Emirates", "AE", "ARE", "784", "784", "Asia"),
    ("United Kingdom", "GB", "GBR", "826", "826", "Europe"),
    ("United States", "US", "USA", "840", "840", "North America"),
    ("Uruguay", "UY", "URY", "858", "858", "South America"),
    ("Uzbekistan", "UZ", "UZB", "860", "860", "Asia"),
    ("Vanuatu", "VU", "VUT", "548", "548", "Oceania"),
    ("Venezuela", "VE", "VEN", "862", "862", "South America"),
    ("Vietnam", "VN", "VNM", "704", "704", "Asia"),
    ("Yemen", "YE", "YEM", "887", "887", "Asia"),
    ("Zambia", "ZM", "ZMB", "894", "894", "Africa"),
    ("Zimbabwe", "ZW", "ZWE", "716", "716", "Africa"),
]

# TCC destinations: (tcc_index, tcc_region, name)
TCC_DESTINATIONS = [
    (1, "PACIFIC OCEAN", "Austral Islands"),
    (2, "PACIFIC OCEAN", "Australia"),
    (3, "PACIFIC OCEAN", "Bismarck Archipelago (Admiralty Islands, Bougainville, New Britain, New Ireland)"),
    (4, "PACIFIC OCEAN", "Chatham Islands"),
    (5, "PACIFIC OCEAN", "Cook Islands (Aitutaki, Penrhyn, Rarotonga)"),
    (6, "PACIFIC OCEAN", "Easter Island"),
    (7, "PACIFIC OCEAN", "Fiji Islands"),
    (8, "PACIFIC OCEAN", "French Polynesia (Gambier, Tahiti, Tuamotu)"),
    (9, "PACIFIC OCEAN", "Galapagos Islands"),
    (10, "PACIFIC OCEAN", "Guam"),
    (11, "PACIFIC OCEAN", "Hawaiian Islands"),
    (12, "PACIFIC OCEAN", "Juan Fernandez Islands (Robinson Crusoe Island)"),
    (13, "PACIFIC OCEAN", "Kiribati (Gilberts, Tarawa, Ocean Island)"),
    (14, "PACIFIC OCEAN", "Line/Phoenix Islands (Canton, Christmas, Enderbury, Fanning)"),
    (15, "PACIFIC OCEAN", "Lord Howe Island"),
    (16, "PACIFIC OCEAN", "Marquesas Islands"),
    (17, "PACIFIC OCEAN", "Marshall Islands, Republic of (Eniwetok, Kwajalein, Majuro)"),
    (18, "PACIFIC OCEAN", "Micronesia, Fed.States of (Caroline Islands, Chuuk, Kosrae, Pohnpei, Yap)"),
    (19, "PACIFIC OCEAN", "Midway Island"),
    (20, "PACIFIC OCEAN", "Nauru"),
    (21, "PACIFIC OCEAN", "New Caledonia & Dependencies (L'Île-des-Pins, Loyalty Islands)"),
    (22, "PACIFIC OCEAN", "New Zealand"),
    (23, "PACIFIC OCEAN", "Niue"),
    (24, "PACIFIC OCEAN", "Norfolk Island"),
    (25, "PACIFIC OCEAN", "Northern Marianas (Saipan, Tinian)"),
    (26, "PACIFIC OCEAN", "Ogasawara (Bonin, Iwo Jima, Volcano Island)"),
    (27, "PACIFIC OCEAN", "Palau, Republic of"),
    (28, "PACIFIC OCEAN", "Papua New Guinea"),
    (29, "PACIFIC OCEAN", "Pitcairn Island"),
    (30, "PACIFIC OCEAN", "Ryukyu Islands (Okinawa)"),
    (31, "PACIFIC OCEAN", "Samoa, American"),
    (32, "PACIFIC OCEAN", "Samoa"),
    (33, "PACIFIC OCEAN", "Solomon Islands (Guadalcanal, New Georgia, Tulagi)"),
    (34, "PACIFIC OCEAN", "Tasmania"),
    (35, "PACIFIC OCEAN", "Tokelau Islands (Atafu, Fakaofu, Union)"),
    (36, "PACIFIC OCEAN", "Tonga (Nukualofa)"),
    (37, "PACIFIC OCEAN", "Tuvalu (Ellice Island, Funafuti, Vaitapu)"),
    (38, "PACIFIC OCEAN", "Vanuatu (New Hebrides Islands)"),
    (39, "PACIFIC OCEAN", "Wake Island"),
    (40, "PACIFIC OCEAN", "Wallis & Futuna Islands"),
    (41, "NORTH AMERICA", "Alaska"),
    (42, "NORTH AMERICA", "Canada"),
    (43, "NORTH AMERICA", "Mexico"),
    (44, "NORTH AMERICA", "Prince Edward Island"),
    (45, "NORTH AMERICA", "St. Pierre & Miquelon"),
    (46, "NORTH AMERICA", "United States (Contiguous)"),
    (47, "CENTRAL AMERICA", "Belize"),
    (48, "CENTRAL AMERICA", "Costa Rica"),
    (49, "CENTRAL AMERICA", "El Salvador"),
    (50, "CENTRAL AMERICA", "Guatemala"),
    (51, "CENTRAL AMERICA", "Honduras"),
    (52, "CENTRAL AMERICA", "Nicaragua"),
    (53, "CENTRAL AMERICA", "Panama"),
    (54, "SOUTH AMERICA", "Argentina"),
    (55, "SOUTH AMERICA", "Bolivia"),
    (56, "SOUTH AMERICA", "Brazil"),
    (57, "SOUTH AMERICA", "Chile"),
    (58, "SOUTH AMERICA", "Colombia"),
    (59, "SOUTH AMERICA", "Ecuador"),
    (60, "SOUTH AMERICA", "French Guiana"),
    (61, "SOUTH AMERICA", "Guyana"),
    (62, "SOUTH AMERICA", "Nueva Esparta (Margarita Island)"),
    (63, "SOUTH AMERICA", "Paraguay"),
    (64, "SOUTH AMERICA", "Peru"),
    (65, "SOUTH AMERICA", "Suriname"),
    (66, "SOUTH AMERICA", "Uruguay"),
    (67, "SOUTH AMERICA", "Venezuela"),
    (68, "CARIBBEAN", "Anguilla"),
    (69, "CARIBBEAN", "Antigua & Barbuda"),
    (70, "CARIBBEAN", "Aruba"),
    (71, "CARIBBEAN", "Bahamas"),
    (72, "CARIBBEAN", "Barbados"),
    (73, "CARIBBEAN", "Bonaire"),
    (74, "CARIBBEAN", "Cayman Islands"),
    (75, "CARIBBEAN", "Cuba"),
    (76, "CARIBBEAN", "Curacao"),
    (77, "CARIBBEAN", "Dominica"),
    (78, "CARIBBEAN", "Dominican Republic"),
    (79, "CARIBBEAN", "Grenada & Dependencies (Carriacou, Grenadines)"),
    (80, "CARIBBEAN", "Guadeloupe & Dependencies (Marie Galante)"),
    (81, "CARIBBEAN", "Haiti"),
    (82, "CARIBBEAN", "Jamaica"),
    (83, "CARIBBEAN", "Martinique"),
    (84, "CARIBBEAN", "Montserrat"),
    (85, "CARIBBEAN", "Nevis"),
    (86, "CARIBBEAN", "Puerto Rico"),
    (87, "CARIBBEAN", "Saba & Sint Eustatius"),
    (88, "CARIBBEAN", "St. Barthélemy"),
    (89, "CARIBBEAN", "St. Kitts"),
    (90, "CARIBBEAN", "St. Lucia"),
    (91, "CARIBBEAN", "St. Martin (France)"),
    (92, "CARIBBEAN", "St. Vincent & the Grenadines"),
    (93, "CARIBBEAN", "San Andres & Providencia"),
    (94, "CARIBBEAN", "Sint Maarten (Netherlands)"),
    (95, "CARIBBEAN", "Trinidad & Tobago"),
    (96, "CARIBBEAN", "Turks & Caicos Islands"),
    (97, "CARIBBEAN", "Virgin Islands, British (Tortola, etc.)"),
    (98, "CARIBBEAN", "Virgin Islands, U.S. (St. Croix, St. John, St. Thomas)"),
    (99, "ATLANTIC OCEAN", "Ascension"),
    (100, "ATLANTIC OCEAN", "Azores Islands"),
    (101, "ATLANTIC OCEAN", "Bermuda"),
    (102, "ATLANTIC OCEAN", "Canary Islands"),
    (103, "ATLANTIC OCEAN", "Cape Verde Islands"),
    (104, "ATLANTIC OCEAN", "Falkland Islands"),
    (105, "ATLANTIC OCEAN", "Faroe Islands"),
    (106, "ATLANTIC OCEAN", "Fernando de Noronha"),
    (107, "ATLANTIC OCEAN", "Greenland (Kalaallit Nunaat)"),
    (108, "ATLANTIC OCEAN", "Iceland"),
    (109, "ATLANTIC OCEAN", "Madeira"),
    (110, "ATLANTIC OCEAN", "South Georgia & the South Sandwich Islands"),
    (111, "ATLANTIC OCEAN", "St. Helena"),
    (112, "ATLANTIC OCEAN", "Tristan da Cunha"),
    (113, "EUROPE & MEDITERRANEAN", "Aland Islands"),
    (114, "EUROPE & MEDITERRANEAN", "Albania"),
    (115, "EUROPE & MEDITERRANEAN", "Andorra"),
    (116, "EUROPE & MEDITERRANEAN", "Austria"),
    (117, "EUROPE & MEDITERRANEAN", "Balearic Islands (Ibiza, Mallorca, Minorca)"),
    (118, "EUROPE & MEDITERRANEAN", "Belarus"),
    (119, "EUROPE & MEDITERRANEAN", "Belgium"),
    (120, "EUROPE & MEDITERRANEAN", "Bosnia & Herzegovina"),
    (121, "EUROPE & MEDITERRANEAN", "Bulgaria"),
    (122, "EUROPE & MEDITERRANEAN", "Corsica"),
    (123, "EUROPE & MEDITERRANEAN", "Crete"),
    (124, "EUROPE & MEDITERRANEAN", "Croatia"),
    (125, "EUROPE & MEDITERRANEAN", "Cyprus, British Sovereign Base Areas of Akrotiri & Dhekelia"),
    (126, "EUROPE & MEDITERRANEAN", "Cyprus, Republic"),
    (127, "EUROPE & MEDITERRANEAN", "Cyprus, Turkish Fed. State"),
    (128, "EUROPE & MEDITERRANEAN", "Czech Republic"),
    (129, "EUROPE & MEDITERRANEAN", "Denmark"),
    (130, "EUROPE & MEDITERRANEAN", "England"),
    (131, "EUROPE & MEDITERRANEAN", "Estonia"),
    (132, "EUROPE & MEDITERRANEAN", "Finland"),
    (133, "EUROPE & MEDITERRANEAN", "France"),
    (134, "EUROPE & MEDITERRANEAN", "Germany"),
    (135, "EUROPE & MEDITERRANEAN", "Gibraltar"),
    (136, "EUROPE & MEDITERRANEAN", "Greece"),
    (137, "EUROPE & MEDITERRANEAN", "Greek Aegean Islands (Cyclades, Dodecanese, Northern Aegean Islands)"),
    (138, "EUROPE & MEDITERRANEAN", "Guernsey & Dependencies (Alderney, Herm, Sark)"),
    (139, "EUROPE & MEDITERRANEAN", "Hungary"),
    (140, "EUROPE & MEDITERRANEAN", "Ionian Islands (Corfu, etc.)"),
    (141, "EUROPE & MEDITERRANEAN", "Ireland (Eire)"),
    (142, "EUROPE & MEDITERRANEAN", "Ireland, Northern"),
    (143, "EUROPE & MEDITERRANEAN", "Isle of Man"),
    (144, "EUROPE & MEDITERRANEAN", "Italy"),
    (145, "EUROPE & MEDITERRANEAN", "Jersey"),
    (146, "EUROPE & MEDITERRANEAN", "Kaliningrad"),
    (147, "EUROPE & MEDITERRANEAN", "Kosovo"),
    (148, "EUROPE & MEDITERRANEAN", "Lampedusa"),
    (149, "EUROPE & MEDITERRANEAN", "Latvia"),
    (150, "EUROPE & MEDITERRANEAN", "Liechtenstein"),
    (151, "EUROPE & MEDITERRANEAN", "Lithuania"),
    (152, "EUROPE & MEDITERRANEAN", "Luxembourg"),
    (153, "EUROPE & MEDITERRANEAN", "Malta"),
    (154, "EUROPE & MEDITERRANEAN", "Moldova"),
    (155, "EUROPE & MEDITERRANEAN", "Monaco"),
    (156, "EUROPE & MEDITERRANEAN", "Montenegro"),
    (157, "EUROPE & MEDITERRANEAN", "Netherlands"),
    (158, "EUROPE & MEDITERRANEAN", "North Macedonia"),
    (159, "EUROPE & MEDITERRANEAN", "Norway"),
    (160, "EUROPE & MEDITERRANEAN", "Poland"),
    (161, "EUROPE & MEDITERRANEAN", "Portugal"),
    (162, "EUROPE & MEDITERRANEAN", "Romania"),
    (163, "EUROPE & MEDITERRANEAN", "Russia"),
    (164, "EUROPE & MEDITERRANEAN", "San Marino"),
    (165, "EUROPE & MEDITERRANEAN", "Sardinia"),
    (166, "EUROPE & MEDITERRANEAN", "Scotland"),
    (167, "EUROPE & MEDITERRANEAN", "Serbia"),
    (168, "EUROPE & MEDITERRANEAN", "Sicily"),
    (169, "EUROPE & MEDITERRANEAN", "Slovakia"),
    (170, "EUROPE & MEDITERRANEAN", "Slovenia"),
    (171, "EUROPE & MEDITERRANEAN", "Spain"),
    (172, "EUROPE & MEDITERRANEAN", "Spitsbergen (Svalbard, Bear Island)"),
    (173, "EUROPE & MEDITERRANEAN", "Srpska"),
    (174, "EUROPE & MEDITERRANEAN", "Sweden"),
    (175, "EUROPE & MEDITERRANEAN", "Switzerland"),
    (176, "EUROPE & MEDITERRANEAN", "Transnistria (Pridnestrovie)"),
    (177, "EUROPE & MEDITERRANEAN", "Turkey in Europe (Istanbul)"),
    (178, "EUROPE & MEDITERRANEAN", "Ukraine"),
    (179, "EUROPE & MEDITERRANEAN", "Vatican City"),
    (180, "EUROPE & MEDITERRANEAN", "Wales"),
    (181, "ANTARCTICA", "Argentine Antarctica (Antarctic Peninsula)"),
    (182, "ANTARCTICA", "Australian Antarctic Territory (Davis, Heard, Macquarie, Mawson)"),
    (183, "ANTARCTICA", "British Antarctic Territory (Antarctic Peninsula, Graham Land, So. Orkney, So. Shetland)"),
    (184, "ANTARCTICA", "Chilean Antarctic Territory (Antarctic Peninsula)"),
    (185, "ANTARCTICA", "French Antarctica (Adélie, Kerguelen)"),
    (186, "ANTARCTICA", "New Zealand Antarctica (Ross Dependency)"),
    (187, "ANTARCTICA", "Norwegian Dependencies (Bouvet, Peter I Island, Queen Maud Land)"),
    (188, "AFRICA", "Algeria"),
    (189, "AFRICA", "Angola"),
    (190, "AFRICA", "Benin"),
    (191, "AFRICA", "Botswana"),
    (192, "AFRICA", "Burkina Faso"),
    (193, "AFRICA", "Burundi"),
    (194, "AFRICA", "Cabinda"),
    (195, "AFRICA", "Cameroon"),
    (196, "AFRICA", "Central African Republic"),
    (197, "AFRICA", "Chad"),
    (198, "AFRICA", "Congo, Democratic Republic of (Kinshasa)"),
    (199, "AFRICA", "Congo, Republic of (Brazzaville)"),
    (200, "AFRICA", "Côte d'Ivoire (Ivory Coast)"),
    (201, "AFRICA", "Djibouti"),
    (202, "AFRICA", "Egypt in Africa"),
    (203, "AFRICA", "Equatorial Guinea (Bioko)"),
    (204, "AFRICA", "Equatorial Guinea (Rio Muni)"),
    (205, "AFRICA", "Eritrea"),
    (206, "AFRICA", "Eswatini (Swaziland)"),
    (207, "AFRICA", "Ethiopia"),
    (208, "AFRICA", "Gabon"),
    (209, "AFRICA", "Gambia, The"),
    (210, "AFRICA", "Ghana"),
    (211, "AFRICA", "Guinea"),
    (212, "AFRICA", "Guinea-Bissau"),
    (213, "AFRICA", "Kenya"),
    (214, "AFRICA", "Lesotho"),
    (215, "AFRICA", "Liberia"),
    (216, "AFRICA", "Libya"),
    (217, "AFRICA", "Malawi"),
    (218, "AFRICA", "Mali"),
    (219, "AFRICA", "Mauritania"),
    (220, "AFRICA", "Morocco"),
    (221, "AFRICA", "Morocco, Spanish (Ceuta, Melilla)"),
    (222, "AFRICA", "Mozambique"),
    (223, "AFRICA", "Namibia"),
    (224, "AFRICA", "Niger"),
    (225, "AFRICA", "Nigeria"),
    (226, "AFRICA", "Rwanda"),
    (227, "AFRICA", "Sao Tome & Principe"),
    (228, "AFRICA", "Senegal"),
    (229, "AFRICA", "Sierra Leone"),
    (230, "AFRICA", "Somalia (Italian Somaliland)"),
    (231, "AFRICA", "Somaliland (British)"),
    (232, "AFRICA", "South Africa"),
    (233, "AFRICA", "South Sudan"),
    (234, "AFRICA", "Sudan"),
    (235, "AFRICA", "Tanzania"),
    (236, "AFRICA", "Togo"),
    (237, "AFRICA", "Tunisia"),
    (238, "AFRICA", "Uganda"),
    (239, "AFRICA", "Western Sahara"),
    (240, "AFRICA", "Zambia"),
    (241, "AFRICA", "Zanzibar"),
    (242, "AFRICA", "Zimbabwe"),
    (243, "MIDDLE EAST", "Abu Dhabi"),
    (244, "MIDDLE EAST", "Ajman"),
    (245, "MIDDLE EAST", "Bahrain"),
    (246, "MIDDLE EAST", "Dubai"),
    (247, "MIDDLE EAST", "Egypt in Asia (Sinai Peninsula)"),
    (248, "MIDDLE EAST", "Fujairah"),
    (249, "MIDDLE EAST", "Iran"),
    (250, "MIDDLE EAST", "Iraq"),
    (251, "MIDDLE EAST", "Israel"),
    (252, "MIDDLE EAST", "Jordan"),
    (253, "MIDDLE EAST", "Kuwait"),
    (254, "MIDDLE EAST", "Lebanon"),
    (255, "MIDDLE EAST", "Oman"),
    (256, "MIDDLE EAST", "Palestine"),
    (257, "MIDDLE EAST", "Qatar"),
    (258, "MIDDLE EAST", "Ras Al Khaimah"),
    (259, "MIDDLE EAST", "Saudi Arabia"),
    (260, "MIDDLE EAST", "Sharjah"),
    (261, "MIDDLE EAST", "Syria"),
    (262, "MIDDLE EAST", "Umm Al Qaiwain"),
    (263, "MIDDLE EAST", "Yemen"),
    (264, "INDIAN OCEAN", "Andaman-Nicobar Islands"),
    (265, "INDIAN OCEAN", "British Indian Ocean Territory (Chagos Archipelago, Diego Garcia)"),
    (266, "INDIAN OCEAN", "Christmas Island"),
    (267, "INDIAN OCEAN", "Cocos (Keeling) Islands"),
    (268, "INDIAN OCEAN", "Comoros (Anjouan, Grand Comoro, Moheli)"),
    (269, "INDIAN OCEAN", "Lakshadweep"),
    (270, "INDIAN OCEAN", "Madagascar"),
    (271, "INDIAN OCEAN", "Maldives"),
    (272, "INDIAN OCEAN", "Mauritius & Dependencies (Agalega, St. Brandon)"),
    (273, "INDIAN OCEAN", "Mayotte (Dzaoudzi)"),
    (274, "INDIAN OCEAN", "Reunion"),
    (275, "INDIAN OCEAN", "Rodrigues Island"),
    (276, "INDIAN OCEAN", "Seychelles"),
    (277, "INDIAN OCEAN", "Socotra"),
    (278, "INDIAN OCEAN", "Zil Elwannyen Sesel (Aldabra, Amirante Islands, Farquhar)"),
    (279, "ASIA", "Abkhazia"),
    (280, "ASIA", "Afghanistan"),
    (281, "ASIA", "Armenia"),
    (282, "ASIA", "Azerbaijan"),
    (283, "ASIA", "Bangladesh"),
    (284, "ASIA", "Bhutan"),
    (285, "ASIA", "Brunei"),
    (286, "ASIA", "Cambodia"),
    (287, "ASIA", "China, People's Republic"),
    (288, "ASIA", "Georgia"),
    (289, "ASIA", "Hainan Island"),
    (290, "ASIA", "Hong Kong"),
    (291, "ASIA", "India"),
    (292, "ASIA", "Indonesia (Java)"),
    (293, "ASIA", "Japan"),
    (294, "ASIA", "Jeju Island (South Korea)"),
    (295, "ASIA", "Kalimantan (Indonesian Borneo)"),
    (296, "ASIA", "Kashmir"),
    (297, "ASIA", "Kazakhstan"),
    (298, "ASIA", "Korea, North"),
    (299, "ASIA", "Korea, South"),
    (300, "ASIA", "Kyrgyzstan"),
    (301, "ASIA", "Laos"),
    (302, "ASIA", "Lesser Sunda Islands (Bali, Timor, Indonesia)"),
    (303, "ASIA", "Macau"),
    (304, "ASIA", "Malaysia"),
    (305, "ASIA", "Maluku Islands"),
    (306, "ASIA", "Mongolia, Republic"),
    (307, "ASIA", "Myanmar (Burma)"),
    (308, "ASIA", "Nakhchivan"),
    (309, "ASIA", "Nepal"),
    (310, "ASIA", "Pakistan"),
    (311, "ASIA", "Papua (Irian Jaya)"),
    (312, "ASIA", "Philippines"),
    (313, "ASIA", "Russia in Asia (incl. Siberia)"),
    (314, "ASIA", "Sabah (North Borneo)"),
    (315, "ASIA", "Sarawak"),
    (316, "ASIA", "Sikkim"),
    (317, "ASIA", "Singapore"),
    (318, "ASIA", "South Ossetia"),
    (319, "ASIA", "Sri Lanka (Ceylon)"),
    (320, "ASIA", "Sulawesi (Celebes, Indonesia)"),
    (321, "ASIA", "Sumatra (Indonesia)"),
    (322, "ASIA", "Taiwan. R.O.C."),
    (323, "ASIA", "Tajikistan"),
    (324, "ASIA", "Thailand"),
    (325, "ASIA", "Tibet"),
    (326, "ASIA", "Timor-Leste"),
    (327, "ASIA", "Turkey in Asia (Anatolia, Ankara, Izmir)"),
    (328, "ASIA", "Turkmenistan"),
    (329, "ASIA", "Uzbekistan"),
    (330, "ASIA", "Vietnam"),
]

# TCC to UN country mappings: tcc_index -> UN country name (for linking)
# Only includes TCC destinations that map to a UN country
TCC_TO_UN = {
    2: "Australia", 7: "Fiji", 13: "Kiribati", 17: "Marshall Islands",
    18: "Micronesia", 20: "Nauru", 22: "New Zealand", 27: "Palau",
    28: "Papua New Guinea", 32: "Samoa", 33: "Solomon Islands",
    36: "Tonga", 37: "Tuvalu", 38: "Vanuatu",
    42: "Canada", 43: "Mexico", 46: "United States",
    47: "Belize", 48: "Costa Rica", 49: "El Salvador", 50: "Guatemala",
    51: "Honduras", 52: "Nicaragua", 53: "Panama",
    54: "Argentina", 55: "Bolivia", 56: "Brazil", 57: "Chile",
    58: "Colombia", 59: "Ecuador", 61: "Guyana", 63: "Paraguay",
    64: "Peru", 65: "Suriname", 66: "Uruguay", 67: "Venezuela",
    69: "Antigua and Barbuda", 72: "Barbados", 75: "Cuba",
    77: "Dominica", 78: "Dominican Republic", 81: "Haiti", 82: "Jamaica",
    89: "Saint Kitts and Nevis", 90: "Saint Lucia",
    92: "Saint Vincent and the Grenadines", 95: "Trinidad and Tobago",
    103: "Cabo Verde", 108: "Iceland",
    114: "Albania", 115: "Andorra", 116: "Austria", 118: "Belarus",
    119: "Belgium", 120: "Bosnia and Herzegovina", 121: "Bulgaria",
    124: "Croatia", 126: "Cyprus", 128: "Czech Republic", 129: "Denmark",
    131: "Estonia", 132: "Finland", 133: "France", 134: "Germany",
    136: "Greece", 139: "Hungary", 141: "Ireland", 144: "Italy",
    149: "Latvia", 150: "Liechtenstein", 151: "Lithuania", 152: "Luxembourg",
    153: "Malta", 154: "Moldova", 155: "Monaco", 156: "Montenegro",
    157: "Netherlands", 158: "North Macedonia", 159: "Norway", 160: "Poland",
    161: "Portugal", 162: "Romania", 163: "Russia", 164: "San Marino",
    167: "Serbia", 169: "Slovakia", 170: "Slovenia", 171: "Spain",
    174: "Sweden", 175: "Switzerland", 178: "Ukraine", 179: "Vatican City",
    188: "Algeria", 189: "Angola", 190: "Benin", 191: "Botswana",
    192: "Burkina Faso", 193: "Burundi", 195: "Cameroon",
    196: "Central African Republic", 197: "Chad", 198: "Congo (DRC)",
    199: "Congo", 200: "Ivory Coast", 201: "Djibouti", 202: "Egypt",
    205: "Eritrea", 206: "Eswatini", 207: "Ethiopia", 208: "Gabon",
    209: "Gambia", 210: "Ghana", 211: "Guinea", 212: "Guinea-Bissau",
    213: "Kenya", 214: "Lesotho", 215: "Liberia", 216: "Libya",
    217: "Malawi", 218: "Mali", 219: "Mauritania", 220: "Morocco",
    222: "Mozambique", 223: "Namibia", 224: "Niger", 225: "Nigeria",
    226: "Rwanda", 227: "Sao Tome and Principe", 228: "Senegal",
    229: "Sierra Leone", 230: "Somalia", 232: "South Africa",
    233: "South Sudan", 234: "Sudan", 235: "Tanzania", 236: "Togo",
    237: "Tunisia", 238: "Uganda", 240: "Zambia", 242: "Zimbabwe",
    245: "Bahrain", 249: "Iran", 250: "Iraq", 251: "Israel",
    252: "Jordan", 253: "Kuwait", 254: "Lebanon", 255: "Oman",
    257: "Qatar", 259: "Saudi Arabia", 261: "Syria", 263: "Yemen",
    268: "Comoros", 270: "Madagascar", 271: "Maldives", 272: "Mauritius",
    276: "Seychelles",
    280: "Afghanistan", 281: "Armenia", 282: "Azerbaijan",
    283: "Bangladesh", 284: "Bhutan", 285: "Brunei", 286: "Cambodia",
    287: "China", 288: "Georgia", 291: "India", 293: "Japan",
    297: "Kazakhstan", 298: "North Korea", 299: "South Korea",
    300: "Kyrgyzstan", 301: "Laos", 304: "Malaysia", 306: "Mongolia",
    307: "Myanmar", 309: "Nepal", 310: "Pakistan", 312: "Philippines",
    317: "Singapore", 319: "Sri Lanka", 323: "Tajikistan",
    324: "Thailand", 326: "Timor-Leste", 328: "Turkmenistan",
    329: "Uzbekistan", 330: "Vietnam",
    # UK parts map to United Kingdom
    130: "United Kingdom", 142: "United Kingdom", 166: "United Kingdom", 180: "United Kingdom",
    # Turkey parts
    177: "Turkey", 327: "Turkey",
}

# TCC destinations with their own map polygon (de facto states)
TCC_MAP_CODES = {
    147: "-2",  # Kosovo
    231: "-3",  # Somaliland
}

# Microstates: (name, longitude, latitude, map_region_code)
MICROSTATES = [
    ("Liechtenstein", 9.55, 47.16, "438"),
    ("Monaco", 7.42, 43.73, "492"),
    ("San Marino", 12.46, 43.94, "674"),
    ("Vatican City", 12.45, 41.90, "336"),
    ("Andorra", 1.52, 42.51, "020"),
    ("Malta", 14.38, 35.94, "470"),
    ("Luxembourg", 6.13, 49.61, "442"),
    ("Singapore", 103.82, 1.35, "702"),
    ("Bahrain", 50.56, 26.07, "048"),
    ("Maldives", 73.22, 3.20, "462"),
    ("Brunei", 114.73, 4.54, "096"),
    ("Tuvalu", 179.19, -8.52, "798"),
    ("Nauru", 166.93, -0.52, "520"),
    ("Palau", 134.58, 7.51, "585"),
    ("Marshall Islands", 171.18, 7.13, "584"),
    ("Micronesia", 158.21, 6.88, "583"),
    ("Kiribati", -157.36, 1.87, "296"),
    ("Samoa", -171.76, -13.76, "882"),
    ("Tonga", -175.20, -21.18, "776"),
    ("Fiji", 178.07, -17.71, "242"),
    ("Vanuatu", 166.96, -15.38, "548"),
    ("Solomon Islands", 160.16, -9.43, "090"),
    ("Seychelles", 55.49, -4.68, "690"),
    ("Mauritius", 57.55, -20.35, "480"),
    ("Comoros", 43.87, -11.65, "174"),
    ("Sao Tome and Principe", 6.73, 0.19, "678"),
    ("Cabo Verde", -23.52, 14.93, "132"),
    ("Barbados", -59.54, 13.19, "052"),
    ("Saint Lucia", -60.98, 13.91, "662"),
    ("Saint Vincent and the Grenadines", -61.20, 13.25, "670"),
    ("Grenada", -61.68, 12.12, "308"),
    ("Antigua and Barbuda", -61.80, 17.06, "028"),
    ("Saint Kitts and Nevis", -62.78, 17.34, "659"),
    ("Dominica", -61.37, 15.42, "212"),
    ("Trinidad and Tobago", -61.25, 10.69, "780"),
]

# Visits with dates: tcc_index -> first_visit_date (ISO format)
VISITS = {
    42: "2024-05-01",  # Canada
    46: "2019-05-01",  # United States (Contiguous)
    54: "2024-11-01",  # Argentina
    56: "2024-11-01",  # Brazil
    63: "2024-11-01",  # Paraguay
    66: "2024-11-01",  # Uruguay
    102: "2023-09-01",  # Canary Islands
    103: "2022-05-01",  # Cape Verde Islands
    107: "2025-09-01",  # Greenland
    108: "2020-06-01",  # Iceland
    109: "2023-12-01",  # Madeira
    113: "2025-07-01",  # Aland Islands
    114: "2021-05-01",  # Albania
    115: "2016-09-01",  # Andorra
    116: "2008-11-01",  # Austria
    117: "2019-09-01",  # Balearic Islands
    118: "2018-07-01",  # Belarus
    119: "2016-11-01",  # Belgium
    120: "2021-07-01",  # Bosnia & Herzegovina
    121: "2007-08-01",  # Bulgaria
    122: "2025-06-01",  # Corsica
    123: "2025-06-01",  # Crete
    124: "2015-07-01",  # Croatia
    125: "2015-12-01",  # Cyprus, British Sovereign Base Areas
    126: "2015-12-01",  # Cyprus, Republic
    127: "2020-01-01",  # Cyprus, Turkish Fed. State
    128: "2008-09-01",  # Czech Republic
    129: "2008-08-01",  # Denmark
    130: "2021-10-01",  # England
    131: "2019-04-01",  # Estonia
    132: "2008-08-01",  # Finland
    133: "2015-04-01",  # France
    134: "2008-11-01",  # Germany
    135: "2024-01-01",  # Gibraltar
    136: "2019-02-01",  # Greece
    137: "2024-06-01",  # Greek Aegean Islands
    138: "2023-09-01",  # Guernsey & Dependencies
    139: "2011-11-01",  # Hungary
    140: "2023-09-01",  # Ionian Islands
    141: "2021-08-01",  # Ireland (Eire)
    142: "2024-03-01",  # Ireland, Northern
    143: "2025-03-01",  # Isle of Man
    144: "2012-08-01",  # Italy
    145: "2023-09-01",  # Jersey
    147: "2022-01-01",  # Kosovo
    149: "2016-07-01",  # Latvia
    150: "2018-06-01",  # Liechtenstein
    151: "2016-07-01",  # Lithuania
    152: "2016-07-01",  # Luxembourg
    153: "2018-10-01",  # Malta
    154: "2019-11-01",  # Moldova
    155: "2019-05-01",  # Monaco
    156: "2019-10-01",  # Montenegro
    157: "2013-04-01",  # Netherlands
    158: "2017-11-01",  # North Macedonia
    159: "2008-08-01",  # Norway
    160: "2010-10-01",  # Poland
    161: "2014-09-01",  # Portugal
    162: "2018-09-01",  # Romania
    163: "1990-01-01",  # Russia
    164: "2018-10-01",  # San Marino
    165: "2025-10-01",  # Sardinia
    166: "2023-11-01",  # Scotland
    167: "2016-12-01",  # Serbia
    168: "2021-10-01",  # Sicily
    169: "2015-09-01",  # Slovakia
    170: "2015-07-01",  # Slovenia
    171: "2011-09-01",  # Spain
    172: "2024-07-01",  # Spitsbergen
    173: "2021-07-01",  # Srpska
    174: "2008-08-01",  # Sweden
    175: "2017-08-01",  # Switzerland
    176: "2019-11-01",  # Transnistria
    177: "2015-02-01",  # Turkey in Europe
    178: "2017-10-01",  # Ukraine
    179: "2012-08-01",  # Vatican City
    180: "2023-03-01",  # Wales
    188: "2024-04-01",  # Algeria
    201: "2025-11-01",  # Djibouti
    202: "2023-12-01",  # Egypt in Africa
    209: "2025-04-01",  # Gambia
    219: "2025-04-01",  # Mauritania
    220: "2017-12-01",  # Morocco
    228: "2025-04-01",  # Senegal
    231: "2025-11-01",  # Somaliland
    237: "2021-12-01",  # Tunisia
    238: "2024-12-01",  # Uganda
    239: "2025-04-01",  # Western Sahara
    243: "2018-12-01",  # Abu Dhabi
    244: "2018-12-01",  # Ajman
    245: "2023-01-01",  # Bahrain
    246: "2018-12-01",  # Dubai
    248: "2018-12-01",  # Fujairah
    250: "2025-02-01",  # Iraq
    251: "2022-04-01",  # Israel
    252: "2020-02-01",  # Jordan
    253: "2023-06-01",  # Kuwait
    254: "2019-12-01",  # Lebanon
    255: "2024-12-01",  # Oman
    256: "2022-04-01",  # Palestine
    257: "2018-04-01",  # Qatar
    258: "2018-12-01",  # Ras Al Khaimah
    259: "2023-01-01",  # Saudi Arabia
    260: "2018-12-01",  # Sharjah
    261: "2025-10-01",  # Syria
    262: "2018-12-01",  # Umm Al Qaiwain
    276: "2017-01-01",  # Seychelles
    277: "2022-12-01",  # Socotra
    281: "2017-09-01",  # Armenia
    282: "2019-08-01",  # Azerbaijan
    287: "2018-04-01",  # China
    288: "2017-09-01",  # Georgia
    291: "2017-02-01",  # India
    294: "2025-05-01",  # Jeju Island
    297: "2006-07-01",  # Kazakhstan
    299: "2025-04-01",  # Korea, South
    300: "2022-10-01",  # Kyrgyzstan
    304: "2023-05-01",  # Malaysia
    313: "1985-05-01",  # Russia in Asia
    317: "2023-04-01",  # Singapore
    323: "2022-10-01",  # Tajikistan
    327: "2024-03-01",  # Turkey in Asia
    328: "2024-10-01",  # Turkmenistan
    329: "2022-09-01",  # Uzbekistan
    330: "2025-12-01",  # Vietnam
}


def upgrade():
    conn = op.get_bind()

    # 1. Insert UN countries
    for name, a2, a3, num, codes, continent in UN_COUNTRIES:
        conn.execute(text(
            f"""INSERT INTO un_countries (name, iso_alpha2, iso_alpha3, iso_numeric, map_region_codes, continent)
                VALUES ('{name.replace("'", "''")}', '{a2}', '{a3}', '{num}', '{codes}', '{continent}')"""
        ))

    # 2. Build UN country ID lookup
    result = conn.execute(text("SELECT id, name FROM un_countries"))
    un_ids = {row[1]: row[0] for row in result}

    # 3. Insert TCC destinations
    for tcc_idx, region, name in TCC_DESTINATIONS:
        un_name = TCC_TO_UN.get(tcc_idx)
        un_id = un_ids.get(un_name) if un_name else None
        map_code = TCC_MAP_CODES.get(tcc_idx)

        un_id_sql = str(un_id) if un_id else "NULL"
        map_code_sql = f"'{map_code}'" if map_code else "NULL"
        name_escaped = name.replace("'", "''")
        region_escaped = region.replace("'", "''")

        conn.execute(text(
            f"""INSERT INTO tcc_destinations (name, tcc_region, tcc_index, un_country_id, map_region_code)
                VALUES ('{name_escaped}', '{region_escaped}', {tcc_idx}, {un_id_sql}, {map_code_sql})"""
        ))

    # 4. Build TCC destination ID lookup
    result = conn.execute(text("SELECT id, tcc_index FROM tcc_destinations"))
    tcc_ids = {row[1]: row[0] for row in result}

    # 5. Insert visits
    for tcc_idx, visit_date in VISITS.items():
        tcc_id = tcc_ids.get(tcc_idx)
        if tcc_id:
            conn.execute(text(
                f"""INSERT INTO visits (tcc_destination_id, first_visit_date)
                    VALUES ({tcc_id}, '{visit_date}')"""
            ))

    # 6. Insert microstates
    for name, lon, lat, code in MICROSTATES:
        name_escaped = name.replace("'", "''")
        conn.execute(text(
            f"""INSERT INTO microstates (name, longitude, latitude, map_region_code)
                VALUES ('{name_escaped}', {lon}, {lat}, '{code}')"""
        ))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("DELETE FROM visits"))
    conn.execute(text("DELETE FROM microstates"))
    conn.execute(text("DELETE FROM tcc_destinations"))
    conn.execute(text("DELETE FROM un_countries"))
