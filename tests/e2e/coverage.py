"""Registry: every MCP tool name -> the e2e test node that exercises it.

The offline test tests/test_e2e_coverage.py asserts the set of registered tools
equals these keys, and that each referenced test function exists. OPTIONAL tools
(ChatGPT search/fetch) are only checked if actually registered.
"""

E2E_COVERAGE = {
    # session
    "cap_session_status": "test_e2e_read.py::test_e2e_session_status",
    "cap_session_login": "test_e2e_read.py::test_e2e_session_login",
    "cap_session_ping": "test_e2e_read.py::test_e2e_session_ping",
    "cap_session_switch_account": "test_e2e_read.py::test_e2e_session_switch_account",
    "cap_session_logout": "test_e2e_read.py::test_e2e_session_logout",
    # market
    "cap_market_search": "test_e2e_read.py::test_e2e_market_search",
    "cap_market_get": "test_e2e_read.py::test_e2e_market_get",
    "cap_market_navigation_root": "test_e2e_read.py::test_e2e_market_navigation",
    "cap_market_navigation_node": "test_e2e_read.py::test_e2e_market_navigation",
    "cap_market_prices": "test_e2e_read.py::test_e2e_market_prices",
    "cap_market_sentiment": "test_e2e_read.py::test_e2e_market_sentiment",
    # account
    "cap_account_list": "test_e2e_read.py::test_e2e_account_list",
    "cap_account_preferences_get": "test_e2e_read.py::test_e2e_account_preferences_get",
    "cap_account_history_activity": "test_e2e_read.py::test_e2e_account_history",
    "cap_account_history_transactions": "test_e2e_read.py::test_e2e_account_history",
    "cap_account_demo_topup": "test_e2e_read.py::test_e2e_account_demo_topup",
    "cap_account_preferences_set": "test_e2e_trading.py::test_e2e_preferences_set",
    # trading read + confirm
    "cap_trade_positions_list": "test_e2e_read.py::test_e2e_positions_list",
    "cap_trade_positions_get": "test_e2e_read.py::test_e2e_positions_get_negative",
    "cap_trade_orders_list": "test_e2e_read.py::test_e2e_orders_list",
    "cap_trade_confirm_get": "test_e2e_read.py::test_e2e_confirm_get_negative",
    "cap_trade_confirm_wait": "test_e2e_trading.py::test_e2e_execute_close_position",
    # trading preview / execute / mutate
    "cap_trade_preview_position": "test_e2e_trading.py::test_e2e_preview_position",
    "cap_trade_preview_working_order": "test_e2e_trading.py::test_e2e_preview_working_order",
    "cap_trade_execute_position": "test_e2e_trading.py::test_e2e_execute_close_position",
    "cap_trade_positions_amend": "test_e2e_trading.py::test_e2e_execute_close_position",
    "cap_trade_positions_close": "test_e2e_trading.py::test_e2e_execute_close_position",
    "cap_trade_execute_working_order": "test_e2e_trading.py::test_e2e_execute_cancel_order",
    "cap_trade_orders_amend": "test_e2e_trading.py::test_e2e_execute_cancel_order",
    "cap_trade_orders_cancel": "test_e2e_trading.py::test_e2e_execute_cancel_order",
    # watchlists
    "cap_watchlists_list": "test_e2e_read.py::test_e2e_watchlist_lifecycle",
    "cap_watchlists_get": "test_e2e_read.py::test_e2e_watchlist_lifecycle",
    "cap_watchlists_create": "test_e2e_read.py::test_e2e_watchlist_lifecycle",
    "cap_watchlists_add_market": "test_e2e_read.py::test_e2e_watchlist_lifecycle",
    "cap_watchlists_remove_market": "test_e2e_read.py::test_e2e_watchlist_lifecycle",
    "cap_watchlists_delete": "test_e2e_read.py::test_e2e_watchlist_lifecycle",
    # streaming
    "cap_stream_prices": "test_e2e_stream.py::test_e2e_stream_prices",
    "cap_stream_candles": "test_e2e_stream.py::test_e2e_stream_candles",
    "cap_stream_alerts": "test_e2e_stream.py::test_e2e_stream_alerts",
    "cap_stream_portfolio": "test_e2e_stream.py::test_e2e_stream_portfolio",
}

# Tools that may or may not be registered (only checked if present).
OPTIONAL = {
    "search": "test_e2e_read.py::test_e2e_chatgpt_search",
    "fetch": "test_e2e_read.py::test_e2e_chatgpt_fetch",
}
