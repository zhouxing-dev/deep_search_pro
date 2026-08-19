
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
        self.client=AsyncQdrantClient(url=self._get_url())


qdrant_client_manager=QdrantClientManager(get_db_config())