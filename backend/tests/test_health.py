import unittest
from unittest.mock import patch

from fastapi import FastAPI
import httpx

from app.api.health import router


class HealthEndpointTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = FastAPI()
        cls.app.include_router(router)

    async def get(self, path):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get(path)

    async def test_liveness_does_not_check_dependencies(self):
        with (
            patch("app.api.health._check_database") as database_check,
            patch("app.api.health._check_vector_store") as vector_store_check,
        ):
            response = await self.get("/health/live")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "alive"})
        database_check.assert_not_called()
        vector_store_check.assert_not_called()

    async def test_readiness_returns_ready_when_dependencies_work(self):
        with (
            patch("app.api.health._check_database") as database_check,
            patch(
                "app.api.health._check_vector_store"
            ) as vector_store_check,
        ):
            response = await self.get("/health/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ready",
                "checks": {
                    "database": "ok",
                    "vector_store": "ok",
                },
            },
        )
        database_check.assert_called_once()
        vector_store_check.assert_called_once()

    async def test_readiness_returns_unavailable_when_a_dependency_fails(self):
        with (
            patch(
                "app.api.health._check_database",
                side_effect=RuntimeError("database unavailable"),
            ),
            patch(
                "app.api.health._check_vector_store"
            ) as vector_store_check,
            patch("app.api.health.logger.exception") as log_exception,
        ):
            response = await self.get("/health/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {
                "status": "not_ready",
                "checks": {
                    "database": "unavailable",
                    "vector_store": "ok",
                },
            },
        )
        vector_store_check.assert_called_once()
        log_exception.assert_called_once()


if __name__ == "__main__":
    unittest.main()
