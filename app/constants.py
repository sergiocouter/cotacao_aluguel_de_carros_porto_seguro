from __future__ import annotations

import re

LOCALIZA_NAME = "Localiza"
MOVIDA_NAME = "Movida"

LOCALIZA_URL = "https://www.localiza.com/brasil/pt-br"
LOCALIZA_AIRPORT_URL = (
    "https://www.localiza.com/brasil/pt-br/rede-de-agencias/aeroporto-de-porto-seguro"
)
MOVIDA_URL = "https://www.movida.com.br/"
MOVIDA_RESERVATION_URL = "https://www.movida.com.br/reserva/escolha-seu-veiculo"
MOVIDA_STORE_URL = "https://www.movida.com.br/loja/porto-seguro-aeroporto"

PLAYWRIGHT_VIEWPORT = {"width": 1440, "height": 1200}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
)

AIRPORT_KEYWORDS = ("aeroporto", "airport", "aeropuerto", "bps")
PORTO_SEGURO_KEYWORDS = ("porto seguro", "porto-seguro")
AIRPORT_LOCATION_VARIATIONS = (
    "Aeroporto de Porto Seguro",
    "Porto Seguro Airport",
    "Porto Seguro Aeroporto",
    "Aeroporto Porto Seguro",
    "Porto Seguro - Aeroporto",
)

OPTIONAL_ADDON_KEYWORDS = (
    "protecao",
    "protecao total",
    "seguro",
    "seguro extra",
    "cobertura",
    "terceiros",
    "vidros",
    "pneus",
    "gps",
    "acessorio",
    "acessorios",
    "cadeirinha",
    "assento de elevacao",
    "bebê conforto",
    "upgrade",
    "upgrade de categoria",
    "condutor adicional",
    "motorista adicional",
    "adicional opcional",
)

POLICY_KEYWORDS = (
    "quilometragem",
    "km",
    "franquia",
    "cancelamento",
    "protecao",
    "seguro",
    "retirada",
    "devolucao",
)

OBSERVATION_KEYWORDS = (
    "automatico",
    "manual",
    "ar-condicionado",
    "ar condicionado",
    "porta-malas",
    "porta malas",
    "lugares",
    "passageiros",
)

MOVIDA_MAINTENANCE_PATTERNS = (
    re.compile(r"manuten[cç][aã]o", re.IGNORECASE),
    re.compile(r"voltaremos em breve", re.IGNORECASE),
    re.compile(r"sorry|oops", re.IGNORECASE),
)

LOCALIZA_SELECTORS = {
    "cookie_accept": [
        {"kind": "role", "role": "button", "name": re.compile(r"aceitar|concordo|ok", re.I)},
        {"kind": "text", "text": re.compile(r"aceitar|concordo", re.I)},
        {"kind": "css", "text": "button#onetrust-accept-btn-handler"},
    ],
    "pickup_location_input": [
        {
            "kind": "placeholder",
            "text": re.compile(r"onde voc[eê] quer retirar o carro", re.I),
        },
        {"kind": "label", "text": re.compile(r"retirar o carro", re.I)},
        {"kind": "css", "text": "input[placeholder*='retirar']"},
        {"kind": "css", "text": "input[name*='pickup'], input[id*='pickup']"},
    ],
    "return_location_input": [
        {"kind": "placeholder", "text": re.compile(r"devolu", re.I)},
        {"kind": "label", "text": re.compile(r"devolu", re.I)},
        {"kind": "css", "text": "input[placeholder*='devolu']"},
        {"kind": "css", "text": "input[name*='return'], input[id*='return']"},
    ],
    "pickup_date_input": [
        {"kind": "label", "text": re.compile(r"data", re.I)},
        {"kind": "placeholder", "text": re.compile(r"dd/mm/aaaa|data", re.I)},
        {"kind": "css", "text": "input[type='date']"},
        {"kind": "css", "text": "input[name*='date'], input[id*='date']"},
    ],
    "date_inputs": [
        {"kind": "css", "text": "input[type='date']"},
        {"kind": "css", "text": "input[name*='date'], input[id*='date']"},
        {"kind": "css", "text": "input[placeholder*='Data']"},
    ],
    "pickup_time_input": [
        {"kind": "label", "text": re.compile(r"hora", re.I)},
        {"kind": "placeholder", "text": re.compile(r"hora", re.I)},
        {"kind": "css", "text": "input[type='time']"},
        {"kind": "css", "text": "input[name*='time'], input[id*='time']"},
    ],
    "time_inputs": [
        {"kind": "css", "text": "input[type='time']"},
        {"kind": "css", "text": "input[name*='time'], input[id*='time']"},
        {"kind": "css", "text": "input[placeholder*='Hora']"},
    ],
    "search_button": [
        {"kind": "role", "role": "button", "name": re.compile(r"buscar|reservar|cotar", re.I)},
        {"kind": "text", "text": re.compile(r"buscar|reservar|cotar", re.I)},
        {"kind": "css", "text": "button[type='submit']"},
    ],
    "location_suggestions": [
        {"kind": "css", "text": "[role='option']"},
        {"kind": "css", "text": "li"},
        {"kind": "css", "text": "[class*='suggest'] [class*='item'], [class*='autocomplete'] li"},
    ],
    "agency_name": [
        {"kind": "text", "text": re.compile(r"porto seguro.*aeroporto|aeroporto.*porto seguro", re.I)},
        {"kind": "css", "text": "[data-testid*='agency'], [class*='agency'], [class*='location']"},
    ],
    "result_cards": [
        {"kind": "css", "text": "[data-testid*='vehicle-card']"},
        {"kind": "css", "text": "[class*='vehicle-card'], [class*='result-card'], [class*='car-card']"},
        {"kind": "css", "text": "article, section [class*='card']"},
    ],
    "result_section": [
        {"kind": "css", "text": "[data-testid*='results']"},
        {"kind": "css", "text": "[class*='results'], [class*='search-result']"},
        {"kind": "css", "text": "main"},
    ],
}

MOVIDA_SELECTORS = {
    "cookie_accept": [
        {"kind": "role", "role": "button", "name": re.compile(r"aceitar|concordo|ok", re.I)},
        {"kind": "text", "text": re.compile(r"aceitar|concordo", re.I)},
        {"kind": "css", "text": "button#onetrust-accept-btn-handler"},
    ],
    "pickup_location_input": [
        {"kind": "label", "text": re.compile(r"retirada|ag[eê]ncia|loja", re.I)},
        {"kind": "placeholder", "text": re.compile(r"retirada|ag[eê]ncia|loja", re.I)},
        {"kind": "css", "text": "input[placeholder*='retirada']"},
        {"kind": "css", "text": "input[name*='pickup'], input[id*='pickup'], input[name*='agency']"},
    ],
    "return_location_input": [
        {"kind": "label", "text": re.compile(r"devolu", re.I)},
        {"kind": "placeholder", "text": re.compile(r"devolu", re.I)},
        {"kind": "css", "text": "input[placeholder*='devolu']"},
        {"kind": "css", "text": "input[name*='return'], input[id*='return']"},
    ],
    "pickup_date_input": [
        {"kind": "label", "text": re.compile(r"data", re.I)},
        {"kind": "placeholder", "text": re.compile(r"dd/mm/aaaa|data", re.I)},
        {"kind": "css", "text": "input[type='date']"},
        {"kind": "css", "text": "input[name*='date'], input[id*='date']"},
    ],
    "date_inputs": [
        {"kind": "css", "text": "input[type='date']"},
        {"kind": "css", "text": "input[name*='date'], input[id*='date']"},
        {"kind": "css", "text": "input[placeholder*='Data']"},
    ],
    "pickup_time_input": [
        {"kind": "label", "text": re.compile(r"hora", re.I)},
        {"kind": "placeholder", "text": re.compile(r"hora", re.I)},
        {"kind": "css", "text": "input[type='time']"},
        {"kind": "css", "text": "input[name*='time'], input[id*='time']"},
    ],
    "time_inputs": [
        {"kind": "css", "text": "input[type='time']"},
        {"kind": "css", "text": "input[name*='time'], input[id*='time']"},
        {"kind": "css", "text": "input[placeholder*='Hora']"},
    ],
    "search_button": [
        {"kind": "role", "role": "button", "name": re.compile(r"buscar|reservar|continuar|ver ve[ií]culos", re.I)},
        {"kind": "text", "text": re.compile(r"buscar|reservar|continuar|ver ve[ií]culos", re.I)},
        {"kind": "css", "text": "button[type='submit']"},
    ],
    "location_suggestions": [
        {"kind": "css", "text": "[role='option']"},
        {"kind": "css", "text": "li"},
        {"kind": "css", "text": "[class*='suggest'] [class*='item'], [class*='autocomplete'] li"},
    ],
    "agency_name": [
        {"kind": "text", "text": re.compile(r"porto seguro.*aeroporto|aeroporto.*porto seguro", re.I)},
        {"kind": "css", "text": "[data-testid*='agency'], [class*='agency'], [class*='location']"},
    ],
    "result_cards": [
        {"kind": "css", "text": "[data-testid*='vehicle-card']"},
        {"kind": "css", "text": "[class*='vehicle-card'], [class*='result-card'], [class*='car-card']"},
        {"kind": "css", "text": "article, section [class*='card']"},
    ],
    "result_section": [
        {"kind": "css", "text": "[data-testid*='results']"},
        {"kind": "css", "text": "[class*='results'], [class*='search-result']"},
        {"kind": "css", "text": "main"},
    ],
}
