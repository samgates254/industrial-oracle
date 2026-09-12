"""Unit tests for Redis manager and in-memory cache operations."""

import asyncio
import unittest
from industrial_oracle.core.redis import InMemoryRedisClient, RedisManager


class TestRedis(unittest.TestCase):
    def test_in_memory_redis_crud(self):
        async def run():
            client = InMemoryRedisClient()
            self.assertTrue(await client.ping())

            # Set and Get
            await client.set("key1", "value1")
            val = await client.get("key1")
            self.assertEqual(val, "value1")

            # Exists
            exists = await client.exists("key1", "nonexistent")
            self.assertEqual(exists, 1)

            # Delete
            deleted = await client.delete("key1")
            self.assertEqual(deleted, 1)
            self.assertIsNone(await client.get("key1"))

        asyncio.run(run())

    def test_redis_manager_lifecycle(self):
        async def run():
            mgr = RedisManager("redis://invalid-host:6379/0")
            client = await mgr.get_client()
            self.assertIsNotNone(client)
            self.assertTrue(await client.ping())
            await mgr.close()

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
