"""Transport abstraction layer with pluggable backends."""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from .protocol import SyncMessage

logger = logging.getLogger(__name__)

MessageHandler = Callable[[SyncMessage], Any]


class Transport(ABC):
    """Abstract transport backend."""

    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def send(self, peer_id: str, message: SyncMessage) -> bool: ...

    @abstractmethod
    def on_message(self, handler: MessageHandler) -> None: ...


class TCPTransport(Transport):
    """TCP transport with direct peer connections."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8101) -> None:
        self.host = host
        self.port = port
        self._server: asyncio.Server | None = None
        self._handler: MessageHandler | None = None
        self._connections: dict[str, tuple[asyncio.StreamReader, asyncio.StreamWriter]] = {}

    async def start(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_connection, self.host, self.port
        )
        logger.info("TCP transport listening on %s:%d", self.host, self.port)

    async def stop(self) -> None:
        for peer_id, (_, writer) in self._connections.items():
            writer.close()
        self._connections.clear()
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def send(self, peer_id: str, message: SyncMessage) -> bool:
        conn = self._connections.get(peer_id)
        if not conn:
            return False
        _, writer = conn
        try:
            data = message.to_json().encode("utf-8")
            writer.write(len(data).to_bytes(4, "big") + data)
            await writer.drain()
            return True
        except (ConnectionError, OSError) as e:
            logger.warning("Failed to send to %s: %s", peer_id, e)
            self._connections.pop(peer_id, None)
            return False

    def on_message(self, handler: MessageHandler) -> None:
        self._handler = handler

    async def connect(self, peer_id: str, host: str, port: int) -> bool:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            self._connections[peer_id] = (reader, writer)
            asyncio.create_task(self._read_loop(peer_id, reader))
            return True
        except (ConnectionError, OSError) as e:
            logger.warning("Failed to connect to %s (%s:%d): %s", peer_id, host, port, e)
            return False

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        peer_addr = writer.get_extra_info("peername")
        logger.info("Incoming connection from %s", peer_addr)
        # Temporary ID until handshake identifies the peer
        temp_id = f"pending-{peer_addr[0]}:{peer_addr[1]}"
        self._connections[temp_id] = (reader, writer)
        await self._read_loop(temp_id, reader)

    async def _read_loop(self, peer_id: str, reader: asyncio.StreamReader) -> None:
        try:
            while True:
                length_bytes = await reader.readexactly(4)
                length = int.from_bytes(length_bytes, "big")
                data = await reader.readexactly(length)
                msg = SyncMessage.from_json(data.decode("utf-8"))

                # Update connection mapping with real sender ID
                if msg.sender_id and msg.sender_id != peer_id:
                    if peer_id in self._connections:
                        self._connections[msg.sender_id] = self._connections.pop(peer_id)
                    peer_id = msg.sender_id

                if self._handler:
                    await asyncio.coroutine(lambda: self._handler(msg))() \
                        if not asyncio.iscoroutinefunction(self._handler) \
                        else await self._handler(msg)
        except (asyncio.IncompleteReadError, ConnectionError, OSError):
            logger.info("Connection closed for peer %s", peer_id)
            self._connections.pop(peer_id, None)


class RedisTransport(Transport):
    """Redis pub/sub transport for same-node inter-module sync."""

    def __init__(self, url: str = "redis://localhost:6379", channel_prefix: str = "survive:sync:") -> None:
        self.url = url
        self.channel_prefix = channel_prefix
        self._handler: MessageHandler | None = None
        self._redis: Any = None
        self._pubsub: Any = None
        self._listen_task: asyncio.Task | None = None

    async def start(self) -> None:
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self.url)
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(f"{self.channel_prefix}broadcast")
            self._listen_task = asyncio.create_task(self._listen())
            logger.info("Redis transport connected to %s", self.url)
        except Exception as e:
            logger.warning("Redis transport unavailable: %s", e)

    async def stop(self) -> None:
        if self._listen_task:
            self._listen_task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe()
        if self._redis:
            await self._redis.close()

    async def send(self, peer_id: str, message: SyncMessage) -> bool:
        if not self._redis:
            return False
        try:
            channel = f"{self.channel_prefix}{peer_id}"
            await self._redis.publish(channel, message.to_json())
            return True
        except Exception as e:
            logger.warning("Redis send failed: %s", e)
            return False

    def on_message(self, handler: MessageHandler) -> None:
        self._handler = handler

    async def _listen(self) -> None:
        try:
            async for msg in self._pubsub.listen():
                if msg["type"] == "message" and self._handler:
                    try:
                        sync_msg = SyncMessage.from_json(msg["data"])
                        self._handler(sync_msg)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning("Invalid sync message on Redis: %s", e)
        except asyncio.CancelledError:
            pass


class SerialTransport(Transport):
    """Serial/radio transport for ham radio and sneakernet.

    Binary-optimized with chunking for low-bandwidth links.
    """

    def __init__(
        self,
        device: str = "/dev/ttyUSB0",
        baud_rate: int = 9600,
        chunk_size: int = 256,
    ) -> None:
        self.device = device
        self.baud_rate = baud_rate
        self.chunk_size = chunk_size
        self._handler: MessageHandler | None = None
        self._running = False

    async def start(self) -> None:
        logger.info("Serial transport configured for %s @ %d baud", self.device, self.baud_rate)
        self._running = True

    async def stop(self) -> None:
        self._running = False

    async def send(self, peer_id: str, message: SyncMessage) -> bool:
        from .protocol import chunk_message
        chunks = chunk_message(message, self.chunk_size)
        logger.info("Would send %d chunks via serial to %s", len(chunks), peer_id)
        # Actual serial I/O deferred to hardware integration
        return True

    def on_message(self, handler: MessageHandler) -> None:
        self._handler = handler


class TransportManager:
    """Manages multiple transport backends."""

    def __init__(self) -> None:
        self._transports: dict[str, Transport] = {}
        self._handler: MessageHandler | None = None

    def add(self, name: str, transport: Transport) -> None:
        self._transports[name] = transport
        if self._handler:
            transport.on_message(self._handler)

    def on_message(self, handler: MessageHandler) -> None:
        self._handler = handler
        for transport in self._transports.values():
            transport.on_message(handler)

    async def start_all(self) -> None:
        for name, transport in self._transports.items():
            try:
                await transport.start()
            except Exception as e:
                logger.warning("Transport %s failed to start: %s", name, e)

    async def stop_all(self) -> None:
        for transport in self._transports.values():
            try:
                await transport.stop()
            except Exception:
                pass

    async def send(self, peer_id: str, message: SyncMessage) -> bool:
        for name, transport in self._transports.items():
            if await transport.send(peer_id, message):
                return True
        return False

    def get(self, name: str) -> Transport | None:
        return self._transports.get(name)
