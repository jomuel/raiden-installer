from dataclasses import dataclass, field
from enum import Enum
from typing import NewType, TypeVar, Generic, Dict
from decimal import Decimal, getcontext

from raiden_contracts.constants import CONTRACTS_VERSION
from raiden_installer import settings

Eth_T = TypeVar("Eth_T", int, Decimal, float, str, "Wei")
Token_T = TypeVar("Token_T")
TokenTicker = NewType("TokenTicker", str)


class TokenError(Exception):
    pass


class Wei(int):
    pass


@dataclass
class Currency:
    ticker: str
    wei_ticker: str
    decimals: int = 18

    def format_value(self, wei_amount: Decimal):
        if wei_amount == 0:
            ticker = self.ticker
            value = wei_amount
        elif wei_amount >= 10 ** 15:
            ticker = self.ticker
            value = wei_amount / 10 ** self.decimals
        elif 10 ** 12 <= wei_amount < 10 ** 15:
            ticker = "T" + self.wei_ticker
            value = wei_amount / 10 ** 12
        elif 10 ** 9 <= wei_amount < 10 ** 12:
            ticker = "G" + self.wei_ticker
            value = wei_amount / 10 ** 9
        elif 10 ** 6 <= wei_amount < 10 ** 9:
            ticker = "M" + self.wei_ticker
            value = wei_amount / 10 ** 6
        else:
            ticker = self.wei_ticker
            value = wei_amount

        integral = int(value)
        frac = value % 1
        frac_string = f"{frac:.3g}"[1:] if frac else ""

        return f"{integral}{frac_string} {ticker}"


@dataclass
class Erc20Token(Currency):
    supply: int = 10 ** 21
    addresses: Dict[str, str] = field(default_factory=dict)

    @property
    def address(self) -> str:
        try:
            return self.addresses[settings.network.lower()]
        except KeyError:
            raise TokenError(f"{self.ticker} is not deployed on {settings.network}")

    @staticmethod
    def find_by_ticker(ticker):
        major, minor, _ = CONTRACTS_VERSION.split(".", 2)
        version_string = f"{major}.{minor}"
        token_list_version = {"0.25": TokensV25, "0.33": TokensV33}.get(version_string, Tokens)
        return token_list_version[ticker].value


ETH = Currency(ticker="ETH", wei_ticker="WEI")


class TokenAmount(Generic[Eth_T]):
    def __init__(self, value: Eth_T, currency: Currency):
        context = getcontext()
        context.prec = currency.decimals
        self.value = Decimal(str(value), context=context)
        if type(value) is Wei:
            self.value /= 10 ** currency.decimals

        self.currency = currency

    @property
    def ticker(self) -> TokenTicker:
        ticker = self.currency.ticker
        if ticker is None:
            raise ValueError(f"No ticker defined for {self.currency.__class__.__name__}")
        return TokenTicker(ticker)

    @property
    def formatted(self):
        return self.currency.format_value(Decimal(self.as_wei))

    @property
    def as_wei(self) -> Wei:
        return Wei(self.value * (10 ** self.currency.decimals))

    def __repr__(self):
        return f"{self.value} {self.ticker}"

    def __add__(self, other):
        if not self.__class__ == other.__class__:
            raise ValueError(f"Can not add {self.formatted} and {other.formatted}")

        return self.__class__(Wei(self.as_wei + other.as_wei), self.currency)

    def __eq__(self, other):
        return self.currency == other.currency and self.as_wei == other.as_wei

    def __lt__(self, other):
        if not self.currency == other.currency:
            raise ValueError(f"Can not compare {self.currency} with {other.currency}")
        return self.as_wei < other.as_wei

    def __le__(self, other):
        if not self.currency == other.currency:
            raise ValueError(f"Can not compare {self.currency} with {other.currency}")

        return self.as_wei <= other.as_wei

    def __gt__(self, other):
        if not self.currency == other.currency:
            raise ValueError(f"Can not compare {self.currency} with {other.currency}")
        return self.as_wei > other.as_wei

    def __ge__(self, other):
        if not self.currency == other.currency:
            raise ValueError(f"Can not compare {self.currency} with {other.currency}")

        return self.as_wei >= other.as_wei


class EthereumAmount(TokenAmount):
    def __init__(self, value: Eth_T):
        super().__init__(value, ETH)


_RDN = Erc20Token(
    ticker="RDN",
    wei_ticker="REI",
    addresses={
        "mainnet": "0x255aa6df07540cb5d3d297f0d0d4d84cb52bc8e6",
        "goerli": "0x709118121A1ccA0f32FC2C0c59752E8FEE3c2834",
        "ropsten": "0x5422Ef695ED0B1213e2B953CFA877029637D9D26",
        "rinkeby": "0x51892e7e4085df269de688b273209f3969f547e0",
        "kovan": "0x3a03155696708f517c53ffc4f696dfbfa7743795",
    },
)

_SAI = Erc20Token(
    ticker="SAI",
    wei_ticker="SEI",
    addresses={
        "mainnet": "0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359",
        "ropsten": "0xaD6D458402F60fD3Bd25163575031ACDce07538D",
        "rinkeby": "0x2448eE2641d78CC42D7AD76498917359D961A783",
        "kovan": "0xc4375b7de8af5a38a93548eb8453a498222c4ff2",
    },
)

_LondonRDN = Erc20Token(
    ticker="LDN",
    wei_ticker="REI",
    addresses={"goerli": "0x06b05eb77f6d7c4e7449105d36c7e04fa9cff3ca"},
)

_WizardToken = Erc20Token(
    ticker="WIZ",
    wei_ticker="WEI",
    addresses={"goerli": "0x95b2d84de40a0121061b105e6b54016a49621b44"},
)


class Tokens(Enum):
    RDN = _RDN
    SAI = _SAI
    LDN = _LondonRDN
    WIZ = _WizardToken


class TokensV25(Enum):
    RDN = Erc20Token(
        ticker="RDN",
        wei_ticker="REI",
        addresses={
            "mainnet": "0x255aa6df07540cb5d3d297f0d0d4d84cb52bc8e6",
            "goerli": "0x3a989d97388a39a0b5796306c615d10b7416be77",
        },
    )


class TokensV33(Enum):
    RDN = Erc20Token(
        ticker="RDN",
        wei_ticker="REI",
        addresses={
            "mainnet": "0x255aa6df07540cb5d3d297f0d0d4d84cb52bc8e6",
            "goerli": "0x709118121A1ccA0f32FC2C0c59752E8FEE3c2834",
        },
    )
    LDN = _LondonRDN
    SAI = _SAI
    WIZ = _WizardToken


ETHEREUM_REQUIRED = EthereumAmount(Wei(settings.ethereum_amount_required))

SERVICE_TOKEN_REQUIRED = TokenAmount(
    Wei(settings.service_token.amount_required),
    Erc20Token.find_by_ticker(settings.service_token.ticker),
)

TRANSFER_TOKEN_REQUIRED = TokenAmount(
    Wei(settings.transfer_token.amount_required),
    Erc20Token.find_by_ticker(settings.transfer_token.ticker),
)
