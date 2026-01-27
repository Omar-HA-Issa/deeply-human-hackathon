"""
Country border mappings using ISO2 codes.
Maps each country to its neighboring countries that share a land border.
"""

# ISO2 country code to list of neighboring ISO2 codes
COUNTRY_BORDERS = {
    # Europe
    "AD": ["ES", "FR"],  # Andorra
    "AL": ["GR", "ME", "MK", "XK"],  # Albania
    "AT": ["CH", "CZ", "DE", "HU", "IT", "LI", "SI", "SK"],  # Austria
    "BA": ["HR", "ME", "RS"],  # Bosnia and Herzegovina
    "BE": ["DE", "FR", "LU", "NL"],  # Belgium
    "BG": ["GR", "MK", "RO", "RS", "TR"],  # Bulgaria
    "BY": ["LT", "LV", "PL", "RU", "UA"],  # Belarus
    "CH": ["AT", "DE", "FR", "IT", "LI"],  # Switzerland
    "CZ": ["AT", "DE", "PL", "SK"],  # Czech Republic
    "DE": ["AT", "BE", "CH", "CZ", "DK", "FR", "LU", "NL", "PL"],  # Germany
    "DK": ["DE"],  # Denmark
    "EE": ["LV", "RU"],  # Estonia
    "ES": ["AD", "FR", "GI", "MA", "PT"],  # Spain
    "FI": ["NO", "RU", "SE"],  # Finland
    "FR": ["AD", "BE", "CH", "DE", "ES", "IT", "LU", "MC"],  # France
    "GB": ["IE"],  # United Kingdom
    "GR": ["AL", "BG", "MK", "TR"],  # Greece
    "HR": ["BA", "HU", "ME", "RS", "SI"],  # Croatia
    "HU": ["AT", "HR", "RO", "RS", "SI", "SK", "UA"],  # Hungary
    "IE": ["GB"],  # Ireland
    "IT": ["AT", "CH", "FR", "SI", "SM", "VA"],  # Italy
    "LI": ["AT", "CH"],  # Liechtenstein
    "LT": ["BY", "LV", "PL", "RU"],  # Lithuania
    "LU": ["BE", "DE", "FR"],  # Luxembourg
    "LV": ["BY", "EE", "LT", "RU"],  # Latvia
    "MC": ["FR"],  # Monaco
    "MD": ["RO", "UA"],  # Moldova
    "ME": ["AL", "BA", "HR", "RS", "XK"],  # Montenegro
    "MK": ["AL", "BG", "GR", "RS", "XK"],  # North Macedonia
    "NL": ["BE", "DE"],  # Netherlands
    "NO": ["FI", "RU", "SE"],  # Norway
    "PL": ["BY", "CZ", "DE", "LT", "RU", "SK", "UA"],  # Poland
    "PT": ["ES"],  # Portugal
    "RO": ["BG", "HU", "MD", "RS", "UA"],  # Romania
    "RS": ["BA", "BG", "HR", "HU", "ME", "MK", "RO", "XK"],  # Serbia
    "RU": ["AZ", "BY", "CN", "EE", "FI", "GE", "KZ", "LT", "LV", "MN", "NO", "PL", "UA", "KP"],  # Russia
    "SE": ["FI", "NO"],  # Sweden
    "SI": ["AT", "HR", "HU", "IT"],  # Slovenia
    "SK": ["AT", "CZ", "HU", "PL", "UA"],  # Slovakia
    "SM": ["IT"],  # San Marino
    "UA": ["BY", "HU", "MD", "PL", "RO", "RU", "SK"],  # Ukraine
    "VA": ["IT"],  # Vatican City
    "XK": ["AL", "ME", "MK", "RS"],  # Kosovo

    # Asia
    "AE": ["OM", "SA"],  # United Arab Emirates
    "AF": ["CN", "IR", "PK", "TJ", "TM", "UZ"],  # Afghanistan
    "AM": ["AZ", "GE", "IR", "TR"],  # Armenia
    "AZ": ["AM", "GE", "IR", "RU", "TR"],  # Azerbaijan
    "BD": ["IN", "MM"],  # Bangladesh
    "BN": ["MY"],  # Brunei
    "BT": ["CN", "IN"],  # Bhutan
    "CN": ["AF", "BT", "IN", "KG", "KP", "KZ", "LA", "MM", "MN", "NP", "PK", "RU", "TJ", "VN"],  # China
    "GE": ["AM", "AZ", "RU", "TR"],  # Georgia
    "ID": ["MY", "PG", "TL"],  # Indonesia
    "IL": ["EG", "JO", "LB", "PS", "SY"],  # Israel
    "IN": ["BD", "BT", "CN", "MM", "NP", "PK"],  # India
    "IQ": ["IR", "JO", "KW", "SA", "SY", "TR"],  # Iraq
    "IR": ["AF", "AM", "AZ", "IQ", "PK", "TM", "TR"],  # Iran
    "JO": ["IL", "IQ", "PS", "SA", "SY"],  # Jordan
    "JP": [],  # Japan (island nation)
    "KG": ["CN", "KZ", "TJ", "UZ"],  # Kyrgyzstan
    "KH": ["LA", "TH", "VN"],  # Cambodia
    "KP": ["CN", "KR", "RU"],  # North Korea
    "KR": ["KP"],  # South Korea
    "KW": ["IQ", "SA"],  # Kuwait
    "KZ": ["CN", "KG", "RU", "TM", "UZ"],  # Kazakhstan
    "LA": ["CN", "KH", "MM", "TH", "VN"],  # Laos
    "LB": ["IL", "SY"],  # Lebanon
    "LK": [],  # Sri Lanka (island nation)
    "MM": ["BD", "CN", "IN", "LA", "TH"],  # Myanmar
    "MN": ["CN", "RU"],  # Mongolia
    "MY": ["BN", "ID", "TH"],  # Malaysia
    "NP": ["CN", "IN"],  # Nepal
    "OM": ["AE", "SA", "YE"],  # Oman
    "PH": [],  # Philippines (island nation)
    "PK": ["AF", "CN", "IN", "IR"],  # Pakistan
    "PS": ["EG", "IL", "JO"],  # Palestine
    "QA": ["SA"],  # Qatar
    "SA": ["AE", "BH", "IQ", "JO", "KW", "OM", "QA", "YE"],  # Saudi Arabia
    "SG": ["MY"],  # Singapore
    "SY": ["IL", "IQ", "JO", "LB", "TR"],  # Syria
    "TH": ["KH", "LA", "MM", "MY"],  # Thailand
    "TJ": ["AF", "CN", "KG", "UZ"],  # Tajikistan
    "TL": ["ID"],  # Timor-Leste
    "TM": ["AF", "IR", "KZ", "UZ"],  # Turkmenistan
    "TR": ["AM", "AZ", "BG", "GE", "GR", "IR", "IQ", "SY"],  # Turkey
    "TW": [],  # Taiwan (island)
    "UZ": ["AF", "KG", "KZ", "TJ", "TM"],  # Uzbekistan
    "VN": ["CN", "KH", "LA"],  # Vietnam
    "YE": ["OM", "SA"],  # Yemen

    # Africa
    "AO": ["CD", "CG", "NA", "ZM"],  # Angola
    "BF": ["BJ", "CI", "GH", "ML", "NE", "TG"],  # Burkina Faso
    "BI": ["CD", "RW", "TZ"],  # Burundi
    "BJ": ["BF", "NE", "NG", "TG"],  # Benin
    "BW": ["NA", "ZA", "ZM", "ZW"],  # Botswana
    "CD": ["AO", "BI", "CF", "CG", "RW", "SS", "TZ", "UG", "ZM"],  # DRC
    "CF": ["CD", "CM", "SS", "TD"],  # Central African Republic
    "CG": ["AO", "CD", "CM", "GA"],  # Republic of Congo
    "CI": ["BF", "GH", "GN", "LR", "ML"],  # Ivory Coast
    "CM": ["CF", "CG", "GA", "GQ", "NG", "TD"],  # Cameroon
    "DJ": ["ER", "ET", "SO"],  # Djibouti
    "DZ": ["EH", "LY", "MA", "ML", "MR", "NE", "TN"],  # Algeria
    "EG": ["IL", "LY", "PS", "SD"],  # Egypt
    "EH": ["DZ", "MA", "MR"],  # Western Sahara
    "ER": ["DJ", "ET", "SD"],  # Eritrea
    "ET": ["DJ", "ER", "KE", "SD", "SO", "SS"],  # Ethiopia
    "GA": ["CG", "CM", "GQ"],  # Gabon
    "GH": ["BF", "CI", "TG"],  # Ghana
    "GM": ["SN"],  # Gambia
    "GN": ["CI", "GW", "LR", "ML", "SL", "SN"],  # Guinea
    "GQ": ["CM", "GA"],  # Equatorial Guinea
    "GW": ["GN", "SN"],  # Guinea-Bissau
    "KE": ["ET", "SO", "SS", "TZ", "UG"],  # Kenya
    "LR": ["CI", "GN", "SL"],  # Liberia
    "LS": ["ZA"],  # Lesotho
    "LY": ["DZ", "EG", "NE", "SD", "TD", "TN"],  # Libya
    "MA": ["DZ", "EH", "ES"],  # Morocco
    "MG": [],  # Madagascar (island)
    "ML": ["BF", "CI", "DZ", "GN", "MR", "NE", "SN"],  # Mali
    "MR": ["DZ", "EH", "ML", "SN"],  # Mauritania
    "MU": [],  # Mauritius (island)
    "MW": ["MZ", "TZ", "ZM"],  # Malawi
    "MZ": ["MW", "SZ", "TZ", "ZA", "ZM", "ZW"],  # Mozambique
    "NA": ["AO", "BW", "ZA", "ZM"],  # Namibia
    "NE": ["BF", "BJ", "DZ", "LY", "ML", "NG", "TD"],  # Niger
    "NG": ["BJ", "CM", "NE", "TD"],  # Nigeria
    "RW": ["BI", "CD", "TZ", "UG"],  # Rwanda
    "SC": [],  # Seychelles (island)
    "SD": ["CF", "EG", "ER", "ET", "LY", "SS", "TD"],  # Sudan
    "SL": ["GN", "LR"],  # Sierra Leone
    "SN": ["GM", "GN", "GW", "ML", "MR"],  # Senegal
    "SO": ["DJ", "ET", "KE"],  # Somalia
    "SS": ["CD", "CF", "ET", "KE", "SD", "UG"],  # South Sudan
    "SZ": ["MZ", "ZA"],  # Eswatini
    "TD": ["CF", "CM", "LY", "NE", "NG", "SD"],  # Chad
    "TG": ["BF", "BJ", "GH"],  # Togo
    "TN": ["DZ", "LY"],  # Tunisia
    "TZ": ["BI", "CD", "KE", "MW", "MZ", "RW", "UG", "ZM"],  # Tanzania
    "UG": ["CD", "KE", "RW", "SS", "TZ"],  # Uganda
    "ZA": ["BW", "LS", "MZ", "NA", "SZ", "ZW"],  # South Africa
    "ZM": ["AO", "BW", "CD", "MW", "MZ", "NA", "TZ", "ZW"],  # Zambia
    "ZW": ["BW", "MZ", "ZA", "ZM"],  # Zimbabwe

    # North America
    "BZ": ["GT", "MX"],  # Belize
    "CA": ["US"],  # Canada
    "CR": ["NI", "PA"],  # Costa Rica
    "CU": [],  # Cuba (island)
    "DO": ["HT"],  # Dominican Republic
    "GT": ["BZ", "HN", "MX", "SV"],  # Guatemala
    "HN": ["GT", "NI", "SV"],  # Honduras
    "HT": ["DO"],  # Haiti
    "JM": [],  # Jamaica (island)
    "MX": ["BZ", "GT", "US"],  # Mexico
    "NI": ["CR", "HN"],  # Nicaragua
    "PA": ["CO", "CR"],  # Panama
    "SV": ["GT", "HN"],  # El Salvador
    "US": ["CA", "MX"],  # United States

    # South America
    "AR": ["BO", "BR", "CL", "PY", "UY"],  # Argentina
    "BO": ["AR", "BR", "CL", "PE", "PY"],  # Bolivia
    "BR": ["AR", "BO", "CO", "GF", "GY", "PE", "PY", "SR", "UY", "VE"],  # Brazil
    "CL": ["AR", "BO", "PE"],  # Chile
    "CO": ["BR", "EC", "PA", "PE", "VE"],  # Colombia
    "EC": ["CO", "PE"],  # Ecuador
    "GF": ["BR", "SR"],  # French Guiana
    "GY": ["BR", "SR", "VE"],  # Guyana
    "PE": ["BO", "BR", "CL", "CO", "EC"],  # Peru
    "PY": ["AR", "BO", "BR"],  # Paraguay
    "SR": ["BR", "GF", "GY"],  # Suriname
    "UY": ["AR", "BR"],  # Uruguay
    "VE": ["BR", "CO", "GY"],  # Venezuela

    # Oceania
    "AU": [],  # Australia (island continent)
    "FJ": [],  # Fiji (islands)
    "NZ": [],  # New Zealand (islands)
    "PG": ["ID"],  # Papua New Guinea
}
