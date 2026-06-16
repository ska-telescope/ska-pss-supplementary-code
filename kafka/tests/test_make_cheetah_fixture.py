import pytest

from kafka.tools.make_cheetah_fixture import parse_spccl_row

SPCCL_HEADER = "MJD(decimal days)\tdm(dimensionless)\twidth(ms)\tsigma\tlabel"
SPCCL_ROWS = [
    "56000.0000602978\t298.8\t1024\t13.22\t48611",
    "56000.0000617659\t368.8\t1024\t15.75\t54056",
    "56000.0001523378\t653.6\t512\t11.58\t129371",
]


def _write_spccl(tmp_path, header=SPCCL_HEADER, rows=SPCCL_ROWS):
    p = tmp_path / "demo.spccl"
    p.write_text(header + "\n" + "\n".join(rows) + "\n")
    return p


@pytest.mark.unit
def test_parse_spccl_row_returns_expected_scalars(tmp_path):
    path = _write_spccl(tmp_path)
    out = parse_spccl_row(str(path), row=0)
    assert out == {
        "mjd":   56000.0000602978,
        "dm":    pytest.approx(298.8, rel=1e-6),
        "width": pytest.approx(1024.0, rel=1e-6),
        "snr":   pytest.approx(13.22, rel=1e-6),
    }


@pytest.mark.unit
def test_parse_spccl_row_picks_row_n(tmp_path):
    path = _write_spccl(tmp_path)
    out = parse_spccl_row(str(path), row=2)
    assert out["mjd"] == 56000.0001523378
    assert out["width"] == pytest.approx(512.0, rel=1e-6)


@pytest.mark.unit
def test_parse_spccl_row_rejects_bad_header(tmp_path):
    path = _write_spccl(tmp_path, header="not\tthe\texpected\theader\trow")
    with pytest.raises(ValueError, match="unexpected .spccl header"):
        parse_spccl_row(str(path), row=0)


@pytest.mark.unit
def test_parse_spccl_row_rejects_row_out_of_range(tmp_path):
    path = _write_spccl(tmp_path)
    with pytest.raises(IndexError, match="row 9 not present"):
        parse_spccl_row(str(path), row=9)
