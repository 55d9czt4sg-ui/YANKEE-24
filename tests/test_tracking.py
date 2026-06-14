import pytest

from yankee.tracking import db


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


def test_watchlist_add_remove(db_path):
    db.add_to_watchlist("AAPL", notes="Watching for breakout", db_path=db_path)
    db.add_to_watchlist("msft", db_path=db_path)

    watchlist = db.get_watchlist(db_path=db_path)
    assert sorted(watchlist["Ticker"]) == ["AAPL", "MSFT"]

    db.remove_from_watchlist("aapl", db_path=db_path)
    watchlist = db.get_watchlist(db_path=db_path)
    assert list(watchlist["Ticker"]) == ["MSFT"]


def test_watchlist_upsert_updates_notes(db_path):
    db.add_to_watchlist("AAPL", notes="first", db_path=db_path)
    db.add_to_watchlist("AAPL", notes="second", db_path=db_path)

    watchlist = db.get_watchlist(db_path=db_path)
    assert len(watchlist) == 1
    assert watchlist.iloc[0]["Notes"] == "second"


def test_log_trade_invalid_side_raises(db_path):
    with pytest.raises(ValueError):
        db.log_trade("AAPL", "HOLD", 10, 100.0, db_path=db_path)


def test_open_positions_average_cost(db_path):
    db.log_trade("AAPL", "BUY", 10, 100.0, executed_at="2024-01-01T00:00:00", db_path=db_path)
    db.log_trade("AAPL", "BUY", 10, 120.0, executed_at="2024-01-02T00:00:00", db_path=db_path)

    positions = db.get_open_positions(db_path=db_path)
    aapl = positions[positions["Ticker"] == "AAPL"].iloc[0]

    assert aapl["Quantity"] == 20
    assert aapl["AvgCost"] == pytest.approx(110.0)
    assert aapl["CostBasis"] == pytest.approx(2200.0)


def test_open_positions_excludes_closed(db_path):
    db.log_trade("AAPL", "BUY", 10, 100.0, executed_at="2024-01-01T00:00:00", db_path=db_path)
    db.log_trade("AAPL", "SELL", 10, 110.0, executed_at="2024-01-02T00:00:00", db_path=db_path)

    positions = db.get_open_positions(db_path=db_path)
    assert positions.empty


def test_get_trades_filters_by_ticker(db_path):
    db.log_trade("AAPL", "BUY", 10, 100.0, executed_at="2024-01-01T00:00:00", db_path=db_path)
    db.log_trade("MSFT", "BUY", 5, 200.0, executed_at="2024-01-01T00:00:00", db_path=db_path)

    aapl_trades = db.get_trades(ticker="AAPL", db_path=db_path)
    assert len(aapl_trades) == 1
    assert aapl_trades.iloc[0]["Ticker"] == "AAPL"
