
from qdrant_client import AsyncQdrantClient

from utils.env_utils import get_db_config


class QdrantClientManager:
    """
    向量数据库驱动
    """
    def __init__(self,conf: dict):
        self.client:AsyncQdrantClient | None=None
        self.config:dict = conf

    def _get_url(self):
        return f"http://{self.config['qdrant_host']}:{self.config['qdrant_port']}"

    def init(self):
        # 复用已创建的客户端，避免每次调用都新建 aiohttp session 导致连接泄漏
        if self.client is None:
            self.client = AsyncQdrantClient(
                url=self._get_url(),
                # 客户端 1.18 与服务端 1.16 次版本差>1，跳过版本校验告警
                check_compatibility=False,
            )

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None


qdrant_client_manager=QdrantClientManager(get_db_config())