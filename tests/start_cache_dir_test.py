"""Tests for Velbus.start() cache directory creation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from velbusaio.controller import Velbus


class TestVelbusStartCacheDir:
    """Cache dir must exist for VLP-based setups (e.g. DALI modules still cache)."""

    @pytest.mark.asyncio
    async def test_start_creates_cache_dir_when_using_vlp_file(self, tmp_path):
        cache_dir = tmp_path / "velbuscache"
        velbus = Velbus("", cache_dir=str(cache_dir), vlp_file="/fake.vlp")

        mock_vlp = MagicMock()
        mock_vlp.read = AsyncMock()
        mock_vlp.get.return_value = []

        with patch("velbusaio.controller.VlpFile", return_value=mock_vlp):
            velbus._memory_coordinator.schedule_prefetch = MagicMock()
            await velbus.start()

        assert cache_dir.is_dir()
