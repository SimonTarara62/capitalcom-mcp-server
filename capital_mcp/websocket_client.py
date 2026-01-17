"""WebSocket client for Capital.com streaming API."""

import asyncio
import json
import logging
from datetime import datetime, UTC
from typing import Any, AsyncIterator, Optional

import websockets
from websockets.asyncio.client import ClientConnection

from .config import get_config
from .errors import SessionError, UpstreamError
from .models import PriceTick
from .session import get_session_manager

logger = logging.getLogger(__name__)

# Singleton instance
_websocket_client: Optional["WebSocketClient"] = None


def get_websocket_client() -> "WebSocketClient":
    """Get or create WebSocket client singleton."""
    global _websocket_client
    if _websocket_client is None:
        _websocket_client = WebSocketClient()
    return _websocket_client


class WebSocketClient:
    """
    WebSocket client for Capital.com streaming API.

    Handles real-time price streaming with authentication, subscription management,
    and automatic reconnection.
    """

    def __init__(self):
        self.config = get_config()
        self.session_manager = get_session_manager()
        self._ws: Optional[ClientConnection] = None
        self._subscribed_epics: set[str] = set()
        self._last_ping: Optional[datetime] = None

    async def __aenter__(self) -> "WebSocketClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """
        Connect to Capital.com WebSocket API.

        Raises:
            SessionError: If WebSocket is disabled or authentication fails
            UpstreamError: If connection fails
        """
        if not self.config.cap_ws_enabled:
            raise SessionError(
                "WebSocket streaming is disabled. Set CAP_WS_ENABLED=true to enable."
            )

        # Ensure we have valid session tokens
        await self.session_manager.ensure_logged_in()
        status = self.session_manager.get_status()

        if not status.logged_in or not self.session_manager.client.session_tokens:
            raise SessionError("Not logged in. Cannot establish WebSocket connection.")

        tokens = self.session_manager.client.session_tokens
        ws_url = self.config.ws_url

        try:
            logger.info(f"Connecting to WebSocket: {ws_url}")

            # Connect with authentication headers
            self._ws = await websockets.connect(
                ws_url,
                extra_headers={
                    "CST": tokens.cst,
                    "X-SECURITY-TOKEN": tokens.x_security_token,
                },
                ping_interval=None,  # We'll handle pings manually
                close_timeout=5,
            )

            self._last_ping = datetime.now(UTC)
            logger.info("WebSocket connected successfully")

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            raise UpstreamError(f"Failed to connect to WebSocket: {e}")

    async def close(self) -> None:
        """Close WebSocket connection."""
        if self._ws:
            logger.info("Closing WebSocket connection")
            await self._ws.close()
            self._ws = None
            self._subscribed_epics.clear()
            self._last_ping = None

    async def subscribe(self, epics: list[str]) -> None:
        """
        Subscribe to price updates for given EPICs.

        Args:
            epics: List of market EPICs (max 40 per Capital.com limits)

        Raises:
            ValueError: If too many EPICs requested
            SessionError: If not connected
        """
        if len(epics) > 40:
            raise ValueError(f"Cannot subscribe to more than 40 EPICs (requested: {len(epics)})")

        if not self._ws:
            raise SessionError("WebSocket not connected. Call connect() first.")

        # Subscribe to each epic
        for epic in epics:
            subscribe_msg = {
                "destination": f"market.{epic}",
                "action": "subscribe"
            }

            try:
                await self._ws.send(json.dumps(subscribe_msg))
                self._subscribed_epics.add(epic)
                logger.debug(f"Subscribed to {epic}")
            except Exception as e:
                logger.error(f"Failed to subscribe to {epic}: {e}")
                raise UpstreamError(f"Subscription failed for {epic}: {e}")

    async def unsubscribe(self, epics: list[str]) -> None:
        """
        Unsubscribe from price updates.

        Args:
            epics: List of market EPICs to unsubscribe from
        """
        if not self._ws:
            return

        for epic in epics:
            if epic in self._subscribed_epics:
                unsubscribe_msg = {
                    "destination": f"market.{epic}",
                    "action": "unsubscribe"
                }

                try:
                    await self._ws.send(json.dumps(unsubscribe_msg))
                    self._subscribed_epics.discard(epic)
                    logger.debug(f"Unsubscribed from {epic}")
                except Exception as e:
                    logger.warning(f"Failed to unsubscribe from {epic}: {e}")

    async def _send_ping(self) -> None:
        """Send ping to keep connection alive."""
        if self._ws:
            try:
                await self._ws.ping()
                self._last_ping = datetime.now(UTC)
                logger.debug("Sent WebSocket ping")
            except Exception as e:
                logger.warning(f"Failed to send ping: {e}")

    async def _should_ping(self) -> bool:
        """Check if we should send a ping (every 5 minutes)."""
        if not self._last_ping:
            return True

        elapsed = (datetime.now(UTC) - self._last_ping).total_seconds()
        return elapsed >= 300  # 5 minutes

    def _parse_message(self, message: str) -> Optional[PriceTick]:
        """
        Parse incoming WebSocket message.

        Args:
            message: Raw JSON message from WebSocket

        Returns:
            PriceTick if it's a price update, None otherwise
        """
        try:
            data = json.loads(message)

            # Check if it's a price update message
            # Capital.com format: {"destination": "market.EPIC", "payload": {...}}
            if isinstance(data, dict) and "payload" in data:
                payload = data["payload"]
                destination = data.get("destination", "")

                # Extract EPIC from destination (e.g., "market.GOLD" -> "GOLD")
                epic = destination.replace("market.", "") if destination.startswith("market.") else None

                if epic and "bid" in payload and "offer" in payload:
                    return PriceTick(
                        epic=epic,
                        bid=float(payload["bid"]),
                        offer=float(payload["offer"]),
                        timestamp=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                        change_percent=payload.get("changePercent")
                    )

            # Heartbeat or other message types
            return None

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse WebSocket message: {e}")
            return None

    async def stream(
        self,
        duration: float = 300.0,
        reconnect_attempts: int = 3
    ) -> AsyncIterator[PriceTick]:
        """
        Stream price updates.

        Args:
            duration: Stream duration in seconds (default: 5 minutes)
            reconnect_attempts: Number of reconnection attempts on disconnect

        Yields:
            PriceTick objects as they arrive

        Raises:
            SessionError: If not connected
            UpstreamError: If connection fails after retries
        """
        if not self._ws:
            raise SessionError("WebSocket not connected. Call connect() first.")

        start_time = datetime.now(UTC)
        reconnect_count = 0

        try:
            while True:
                # Check duration timeout
                elapsed = (datetime.now(UTC) - start_time).total_seconds()
                if elapsed >= duration:
                    logger.info(f"Stream duration {duration}s reached, stopping")
                    break

                # Send ping if needed
                if await self._should_ping():
                    await self._send_ping()

                try:
                    # Receive message with timeout
                    remaining = duration - elapsed
                    timeout = min(remaining, 10.0)  # Max 10s wait per message

                    message = await asyncio.wait_for(
                        self._ws.recv(),
                        timeout=timeout
                    )

                    # Parse and yield price tick
                    tick = self._parse_message(message)
                    if tick:
                        yield tick

                except asyncio.TimeoutError:
                    # No message received, continue (normal for quiet periods)
                    continue

                except websockets.exceptions.ConnectionClosed:
                    # Connection lost, attempt reconnection
                    if reconnect_count < reconnect_attempts:
                        reconnect_count += 1
                        logger.warning(f"WebSocket disconnected, reconnecting ({reconnect_count}/{reconnect_attempts})")

                        await asyncio.sleep(2 ** reconnect_count)  # Exponential backoff

                        # Reconnect and resubscribe
                        epics_to_restore = list(self._subscribed_epics)
                        await self.close()
                        await self.connect()
                        await self.subscribe(epics_to_restore)

                        logger.info("Reconnection successful")
                    else:
                        logger.error(f"Max reconnection attempts ({reconnect_attempts}) reached")
                        raise UpstreamError("WebSocket connection lost and reconnection failed")

        finally:
            # Cleanup: unsubscribe from all EPICs
            if self._subscribed_epics:
                await self.unsubscribe(list(self._subscribed_epics))
