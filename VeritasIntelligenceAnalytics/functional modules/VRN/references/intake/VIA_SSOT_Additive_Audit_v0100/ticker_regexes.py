"""Opt-in lexical validators. Source: ADDITIVE_CANDIDATE.json. No existing repo rule replaced."""
import re

TW_STOCK_REGEX = '^(?:[1-9][0-9]{3})$(?![\\s\\S])'
TW_YFINANCE_STOCK_REGEX = '^(?:[1-9][0-9]{3})\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_STOCK_REGEX = '^(?:[1-9][0-9]{3}) TT$(?![\\s\\S])'
TW_PASSIVE_STOCK_ETF_REGEX = '^(?:00[0-9]{2,4})$(?![\\s\\S])'
TW_YFINANCE_PASSIVE_STOCK_ETF_REGEX = '^(?:00[0-9]{2,4})\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_PASSIVE_STOCK_ETF_REGEX = '^(?:00[0-9]{2,4}) TT$(?![\\s\\S])'
TW_ACTIVE_STOCK_ETF_REGEX = '^(?:00[0-9]{3}A)$(?![\\s\\S])'
TW_YFINANCE_ACTIVE_STOCK_ETF_REGEX = '^(?:00[0-9]{3}A)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_ACTIVE_STOCK_ETF_REGEX = '^(?:00[0-9]{3}A) TT$(?![\\s\\S])'
TW_PASSIVE_BOND_ETF_REGEX = '^(?:00[0-9]{3}B)$(?![\\s\\S])'
TW_YFINANCE_PASSIVE_BOND_ETF_REGEX = '^(?:00[0-9]{3}B)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_PASSIVE_BOND_ETF_REGEX = '^(?:00[0-9]{3}B) TT$(?![\\s\\S])'
TW_ACTIVE_BOND_ETF_REGEX = '^(?:00[0-9]{3}D)$(?![\\s\\S])'
TW_YFINANCE_ACTIVE_BOND_ETF_REGEX = '^(?:00[0-9]{3}D)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_ACTIVE_BOND_ETF_REGEX = '^(?:00[0-9]{3}D) TT$(?![\\s\\S])'
TW_LEVERAGED_ETF_REGEX = '^(?:00[0-9]{3}L)$(?![\\s\\S])'
TW_YFINANCE_LEVERAGED_ETF_REGEX = '^(?:00[0-9]{3}L)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_LEVERAGED_ETF_REGEX = '^(?:00[0-9]{3}L) TT$(?![\\s\\S])'
TW_INVERSE_ETF_REGEX = '^(?:00[0-9]{3}R)$(?![\\s\\S])'
TW_YFINANCE_INVERSE_ETF_REGEX = '^(?:00[0-9]{3}R)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_INVERSE_ETF_REGEX = '^(?:00[0-9]{3}R) TT$(?![\\s\\S])'
TW_FUTURES_ETF_REGEX = '^(?:00[0-9]{3}U)$(?![\\s\\S])'
TW_YFINANCE_FUTURES_ETF_REGEX = '^(?:00[0-9]{3}U)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_FUTURES_ETF_REGEX = '^(?:00[0-9]{3}U) TT$(?![\\s\\S])'
TW_BALANCED_ETF_REGEX = '^(?:00[0-9]{3}T)$(?![\\s\\S])'
TW_YFINANCE_BALANCED_ETF_REGEX = '^(?:00[0-9]{3}T)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_BALANCED_ETF_REGEX = '^(?:00[0-9]{3}T) TT$(?![\\s\\S])'
TW_FOREIGN_CURRENCY_STANDARD_ETF_REGEX = '^(?:00[0-9]{3}K)$(?![\\s\\S])'
TW_YFINANCE_FOREIGN_CURRENCY_STANDARD_ETF_REGEX = '^(?:00[0-9]{3}K)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_FOREIGN_CURRENCY_STANDARD_ETF_REGEX = '^(?:00[0-9]{3}K) TT$(?![\\s\\S])'
TW_FOREIGN_CURRENCY_BOND_ETF_REGEX = '^(?:00[0-9]{3}C)$(?![\\s\\S])'
TW_YFINANCE_FOREIGN_CURRENCY_BOND_ETF_REGEX = '^(?:00[0-9]{3}C)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_FOREIGN_CURRENCY_BOND_ETF_REGEX = '^(?:00[0-9]{3}C) TT$(?![\\s\\S])'
TW_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX = '^(?:00[0-9]{3}M)$(?![\\s\\S])'
TW_YFINANCE_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX = '^(?:00[0-9]{3}M)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX = '^(?:00[0-9]{3}M) TT$(?![\\s\\S])'
TW_FOREIGN_CURRENCY_INVERSE_ETF_REGEX = '^(?:00[0-9]{3}S)$(?![\\s\\S])'
TW_YFINANCE_FOREIGN_CURRENCY_INVERSE_ETF_REGEX = '^(?:00[0-9]{3}S)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_FOREIGN_CURRENCY_INVERSE_ETF_REGEX = '^(?:00[0-9]{3}S) TT$(?![\\s\\S])'
TW_FOREIGN_CURRENCY_FUTURES_ETF_REGEX = '^(?:00[0-9]{3}V)$(?![\\s\\S])'
TW_YFINANCE_FOREIGN_CURRENCY_FUTURES_ETF_REGEX = '^(?:00[0-9]{3}V)\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_FOREIGN_CURRENCY_FUTURES_ETF_REGEX = '^(?:00[0-9]{3}V) TT$(?![\\s\\S])'
TW_ETF_REGEX = '^(?:(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V))$(?![\\s\\S])'
TW_YFINANCE_ETF_REGEX = '^(?:(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V))\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_ETF_REGEX = '^(?:(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V)) TT$(?![\\s\\S])'
TW_SECURITY_REGEX = '^(?:(?:[1-9][0-9]{3}|(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V)))$(?![\\s\\S])'
TW_YFINANCE_SECURITY_REGEX = '^(?:(?:[1-9][0-9]{3}|(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V)))\\.(?:TW|TWO)$(?![\\s\\S])'
TW_BLOOMBERG_SECURITY_REGEX = '^(?:(?:[1-9][0-9]{3}|(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V))) TT$(?![\\s\\S])'

REGEX_BY_NAME = {'TW_STOCK_REGEX': '^(?:[1-9][0-9]{3})$(?![\\s\\S])', 'TW_YFINANCE_STOCK_REGEX': '^(?:[1-9][0-9]{3})\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_STOCK_REGEX': '^(?:[1-9][0-9]{3}) TT$(?![\\s\\S])', 'TW_PASSIVE_STOCK_ETF_REGEX': '^(?:00[0-9]{2,4})$(?![\\s\\S])', 'TW_YFINANCE_PASSIVE_STOCK_ETF_REGEX': '^(?:00[0-9]{2,4})\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_PASSIVE_STOCK_ETF_REGEX': '^(?:00[0-9]{2,4}) TT$(?![\\s\\S])', 'TW_ACTIVE_STOCK_ETF_REGEX': '^(?:00[0-9]{3}A)$(?![\\s\\S])', 'TW_YFINANCE_ACTIVE_STOCK_ETF_REGEX': '^(?:00[0-9]{3}A)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_ACTIVE_STOCK_ETF_REGEX': '^(?:00[0-9]{3}A) TT$(?![\\s\\S])', 'TW_PASSIVE_BOND_ETF_REGEX': '^(?:00[0-9]{3}B)$(?![\\s\\S])', 'TW_YFINANCE_PASSIVE_BOND_ETF_REGEX': '^(?:00[0-9]{3}B)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_PASSIVE_BOND_ETF_REGEX': '^(?:00[0-9]{3}B) TT$(?![\\s\\S])', 'TW_ACTIVE_BOND_ETF_REGEX': '^(?:00[0-9]{3}D)$(?![\\s\\S])', 'TW_YFINANCE_ACTIVE_BOND_ETF_REGEX': '^(?:00[0-9]{3}D)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_ACTIVE_BOND_ETF_REGEX': '^(?:00[0-9]{3}D) TT$(?![\\s\\S])', 'TW_LEVERAGED_ETF_REGEX': '^(?:00[0-9]{3}L)$(?![\\s\\S])', 'TW_YFINANCE_LEVERAGED_ETF_REGEX': '^(?:00[0-9]{3}L)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_LEVERAGED_ETF_REGEX': '^(?:00[0-9]{3}L) TT$(?![\\s\\S])', 'TW_INVERSE_ETF_REGEX': '^(?:00[0-9]{3}R)$(?![\\s\\S])', 'TW_YFINANCE_INVERSE_ETF_REGEX': '^(?:00[0-9]{3}R)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_INVERSE_ETF_REGEX': '^(?:00[0-9]{3}R) TT$(?![\\s\\S])', 'TW_FUTURES_ETF_REGEX': '^(?:00[0-9]{3}U)$(?![\\s\\S])', 'TW_YFINANCE_FUTURES_ETF_REGEX': '^(?:00[0-9]{3}U)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_FUTURES_ETF_REGEX': '^(?:00[0-9]{3}U) TT$(?![\\s\\S])', 'TW_BALANCED_ETF_REGEX': '^(?:00[0-9]{3}T)$(?![\\s\\S])', 'TW_YFINANCE_BALANCED_ETF_REGEX': '^(?:00[0-9]{3}T)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_BALANCED_ETF_REGEX': '^(?:00[0-9]{3}T) TT$(?![\\s\\S])', 'TW_FOREIGN_CURRENCY_STANDARD_ETF_REGEX': '^(?:00[0-9]{3}K)$(?![\\s\\S])', 'TW_YFINANCE_FOREIGN_CURRENCY_STANDARD_ETF_REGEX': '^(?:00[0-9]{3}K)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_FOREIGN_CURRENCY_STANDARD_ETF_REGEX': '^(?:00[0-9]{3}K) TT$(?![\\s\\S])', 'TW_FOREIGN_CURRENCY_BOND_ETF_REGEX': '^(?:00[0-9]{3}C)$(?![\\s\\S])', 'TW_YFINANCE_FOREIGN_CURRENCY_BOND_ETF_REGEX': '^(?:00[0-9]{3}C)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_FOREIGN_CURRENCY_BOND_ETF_REGEX': '^(?:00[0-9]{3}C) TT$(?![\\s\\S])', 'TW_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX': '^(?:00[0-9]{3}M)$(?![\\s\\S])', 'TW_YFINANCE_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX': '^(?:00[0-9]{3}M)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_FOREIGN_CURRENCY_LEVERAGED_ETF_REGEX': '^(?:00[0-9]{3}M) TT$(?![\\s\\S])', 'TW_FOREIGN_CURRENCY_INVERSE_ETF_REGEX': '^(?:00[0-9]{3}S)$(?![\\s\\S])', 'TW_YFINANCE_FOREIGN_CURRENCY_INVERSE_ETF_REGEX': '^(?:00[0-9]{3}S)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_FOREIGN_CURRENCY_INVERSE_ETF_REGEX': '^(?:00[0-9]{3}S) TT$(?![\\s\\S])', 'TW_FOREIGN_CURRENCY_FUTURES_ETF_REGEX': '^(?:00[0-9]{3}V)$(?![\\s\\S])', 'TW_YFINANCE_FOREIGN_CURRENCY_FUTURES_ETF_REGEX': '^(?:00[0-9]{3}V)\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_FOREIGN_CURRENCY_FUTURES_ETF_REGEX': '^(?:00[0-9]{3}V) TT$(?![\\s\\S])', 'TW_ETF_REGEX': '^(?:(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V))$(?![\\s\\S])', 'TW_YFINANCE_ETF_REGEX': '^(?:(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V))\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_ETF_REGEX': '^(?:(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V)) TT$(?![\\s\\S])', 'TW_SECURITY_REGEX': '^(?:(?:[1-9][0-9]{3}|(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V)))$(?![\\s\\S])', 'TW_YFINANCE_SECURITY_REGEX': '^(?:(?:[1-9][0-9]{3}|(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V)))\\.(?:TW|TWO)$(?![\\s\\S])', 'TW_BLOOMBERG_SECURITY_REGEX': '^(?:(?:[1-9][0-9]{3}|(?:00[0-9]{2,4}|00[0-9]{3}A|00[0-9]{3}B|00[0-9]{3}D|00[0-9]{3}L|00[0-9]{3}R|00[0-9]{3}U|00[0-9]{3}T|00[0-9]{3}K|00[0-9]{3}C|00[0-9]{3}M|00[0-9]{3}S|00[0-9]{3}V))) TT$(?![\\s\\S])'}

def validate_ticker(value: str, regex_name: str) -> bool:
    """Validate spelling only; does not verify a security or provider listing."""
    if regex_name not in REGEX_BY_NAME:
        raise KeyError(regex_name)
    return isinstance(value, str) and re.fullmatch(REGEX_BY_NAME[regex_name], value) is not None
