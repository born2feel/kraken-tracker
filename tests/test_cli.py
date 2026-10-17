from cbr_rates.cli import main
from cbr_rates.client import CBR_DAILY_URL, CBR_DYNAMIC_URL, CbrClient

from .conftest import FakeResponse, FakeSession


def make_client(daily_xml, dynamic_xml=b""):
    return CbrClient(
        FakeSession(
            {CBR_DAILY_URL: FakeResponse(daily_xml), CBR_DYNAMIC_URL: FakeResponse(dynamic_xml)}
        )
    )


def test_rates_prints_selected_codes(capsys, daily_xml):
    code = main(["rates", "--codes", "usd,eur"], make_client(daily_xml))

    out = capsys.readouterr().out
    assert code == 0
    assert "17.10.2026" in out
    assert "USD" in out and "81.5432" in out
    assert "CNY" not in out


def test_update_writes_csv(tmp_path, capsys, daily_xml):
    path = tmp_path / "rates.csv"

    code = main(["update", "--file", str(path), "--codes", "USD,EUR"], make_client(daily_xml))

    assert code == 0
    assert "2 new" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8").startswith("date,code,name")


def test_plot_from_api(tmp_path, daily_xml, dynamic_xml):
    out = tmp_path / "usd.png"

    code = main(["plot", "USD", "-o", str(out)], make_client(daily_xml, dynamic_xml))

    assert code == 0
    assert out.read_bytes().startswith(b"\x89PNG")


def test_errors_are_reported_without_traceback(capsys):
    client = CbrClient(FakeSession({CBR_DAILY_URL: FakeResponse(status=500)}))

    code = main(["rates", "--date", "2026-01-15"], client)

    assert code == 1
    assert capsys.readouterr().err.startswith("error:")
