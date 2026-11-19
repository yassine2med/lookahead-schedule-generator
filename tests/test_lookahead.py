from datetime import date

import pytest

from lookahead import core
from lookahead.cli import main

HEADER = "activity,trade,location,start,finish\n"


@pytest.fixture
def csv_file(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text(HEADER +
                 "Frame walls,Carpentry,Level 1,2026-03-09,2026-03-20\n"
                 "Rough electrical,Electrical,Level 1,2026-03-16,2026-03-18\n"
                 "Pour slab,Concrete,Level 2,2026-02-02,2026-02-06\n"
                 "Roofing,Roofing,Roof,2026-04-20,2026-04-30\n")
    return f


def test_monday():
    assert core.monday(date(2026, 3, 11)) == date(2026, 3, 9)
    assert core.monday(date(2026, 3, 9)) == date(2026, 3, 9)


def test_load(csv_file):
    assert len(core.load(csv_file)) == 4


def test_three_weeks_default(csv_file):
    weeks = core.build(core.load(csv_file), date(2026, 3, 11))
    assert [w[0] for w in weeks] == [date(2026, 3, 9), date(2026, 3, 16), date(2026, 3, 23)]


def test_status_values(csv_file):
    weeks = core.build(core.load(csv_file), date(2026, 3, 9))
    w1 = dict((a.name, s) for a, s in weeks[0][1])
    w2 = dict((a.name, s) for a, s in weeks[1][1])
    assert w1["Frame walls"] == "starts"
    assert w2["Frame walls"] == "finishes"
    assert w2["Rough electrical"] == "starts and finishes"


def test_continues(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text(HEADER + "Long job,Trade,Area,2026-03-02,2026-03-27\n")
    weeks = core.build(core.load(f), date(2026, 3, 9), 3)
    assert weeks[0][1][0][1] == "continues"


def test_outside_window_excluded(csv_file):
    names = [a.name for _, rows in core.build(core.load(csv_file), date(2026, 3, 9)) for a, _ in rows]
    assert "Pour slab" not in names and "Roofing" not in names


def test_empty_week_message(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text(HEADER)
    assert "nothing scheduled" in core.render(core.build(core.load(f), date(2026, 3, 9), 1))


def test_weeks_must_be_positive(csv_file):
    with pytest.raises(ValueError):
        core.build(core.load(csv_file), date(2026, 3, 9), 0)


def test_finish_before_start(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text(HEADER + "A,T,L,2026-03-10,2026-03-01\n")
    with pytest.raises(ValueError, match="before start"):
        core.load(f)


def test_missing_column(tmp_path):
    f = tmp_path / "s.csv"
    f.write_text("activity,trade\nA,T\n")
    with pytest.raises(ValueError, match="missing column"):
        core.load(f)


def test_by_trade(csv_file):
    counts = core.by_trade(core.build(core.load(csv_file), date(2026, 3, 9)))
    assert counts == {"Carpentry": 2, "Electrical": 1}


def test_cli_bad_date(csv_file, capsys):
    assert main([str(csv_file), "--from", "soon"]) == 2


def test_cli_runs(csv_file, capsys):
    assert main([str(csv_file), "--from", "2026-03-09", "--trades"]) == 0
    assert "Week of 2026-03-09" in capsys.readouterr().out
