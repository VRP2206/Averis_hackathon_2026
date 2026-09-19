import pytest

from sdoc.compare import (Comparator, CountNormaliser, PartyNormaliser, PortNormaliser,
                          WeightKgNormaliser)
from sdoc.models import COMPARE_FIELDS, DocType, ExtractedField, Extraction


@pytest.mark.parametrize("a,b,same", [
    ("PORT KLANG (WESTPORT), MALAYSIA (MYPKG)", "Port Klang (Westport), Malaysia (MYPKG)", True),
    ("CALLAO, PERU (PECLL)", "BUENAVENTURA, COLOMBIA (COBUN)", False),
    ("MOMBASA, KENYA (KEMBA)", "TUTICORIN, INDIA (KEMBA)", False),     # name changed, code kept
    ("SINGAPORE (SGSIN)", "SINGAPORE", True),                          # code missing on one side
])
def test_port(a, b, same):
    n = PortNormaliser()
    assert n.equal(n.normalise(a), n.normalise(b)) is same


@pytest.mark.parametrize("a,b,same", [
    ("MOORIM SP CO., LTD", "MOORIM SP CO LTD", True),
    ("KPP-ANTALIS (SINGAPORE) PTE. LTD.", "KPP-ANTALIS (SINGAPORE) PTE LTD", True),
    ("APRIL FAR EAST (M) SDN BHD", "APRIL FINE PAPER TRADING", False),
    ("NAME | 1 ROAD; CITY", "NAME", True),
])
def test_party(a, b, same):
    n = PartyNormaliser()
    assert n.equal(n.normalise(a), n.normalise(b)) is same


@pytest.mark.parametrize("raw,expected", [("3 x 40'HC", "3"), ("12", "12"), ("1 x 20'FCL", "1")])
def test_count(raw, expected):
    assert CountNormaliser().normalise(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("21,577 KG", "21577"), ("143,940", "143940"), ("21.5 MT", "21500"), ("63000 kgs", "63000")])
def test_weight(raw, expected):
    assert WeightKgNormaliser().normalise(raw) == expected


def _extraction(**values):
    fields = {f: ExtractedField(field=f, value=values.get(f), confidence=1.0) for f in COMPARE_FIELDS}
    return Extraction(doc_path="x", doc_type=DocType.SI, fields=fields)


def test_comparator_flags_only_differing_fields():
    base = dict(shipper="A", consignee="B", notify_party="C", port_of_loading="X (AAAAA)",
                port_of_discharge="Y (BBBBB)", container_count="2 x 40'HC", gross_weight_kg="40,000 KG")
    bl = dict(base, container_count="3 x 40'HC", gross_weight_kg="41,000 KG")
    cmp = Comparator().compare(_extraction(**base), _extraction(**bl))
    assert [c.field for c in cmp if not c.match] == ["container_count", "gross_weight_kg"]
