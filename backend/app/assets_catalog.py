"""Fixed subscription and hardware product lists for the Assets tab."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogItem:
    key: str
    label: str


SUBSCRIPTION_PRODUCTS: tuple[CatalogItem, ...] = (
    CatalogItem("ocp", "OCP"),
    CatalogItem("oke", "OKE"),
    CatalogItem("ovm", "OVM"),
    CatalogItem("rhel", "RHEL"),
    CatalogItem("aap", "AAP"),
    CatalogItem("acs", "ACS"),
    CatalogItem("acm", "ACM"),
)

HARDWARE_PRODUCTS: tuple[CatalogItem, ...] = (
    CatalogItem("hp", "HP"),
    CatalogItem("dell", "Dell"),
    CatalogItem("cisco", "Cisco"),
    CatalogItem("palo_alto", "Palo Alto"),
    CatalogItem("fortinet", "Fortinet"),
)

# Pre-seed asset rows for these (domain, display name) — matches Tasks priority accounts.
ASSET_SEED_COMPANIES: tuple[tuple[str, str], ...] = (
    ("exxonmobil.com", "ExxonMobil"),
    ("conocophillips.com", "ConocoPhillips"),
    ("uniti.com", "Windstream / Uniti"),
    ("eprod.io", "Enterprise Partner Products (EPP)"),
)

SUBSCRIPTION_KEYS = {item.key for item in SUBSCRIPTION_PRODUCTS}
HARDWARE_KEYS = {item.key for item in HARDWARE_PRODUCTS}
