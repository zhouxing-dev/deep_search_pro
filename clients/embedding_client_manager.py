from typing import List

import aiohttp

from utils.env_utils import get_db_config


class TEIEmbeddingClient:
    """HuggingFace Text Embedding Inference (TEI) 客户端"""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """关闭 session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """异步嵌入多个文档"""
        session = await self._get_session()
        async with session.post(
                f"{self.base_url}/embed",
                json={"inputs": texts},
                headers={"Content-Type": "application/json"}
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def aembed_query(self, text: str) -> List[float]:
        """异步嵌入单个查询"""
        result = await self.aembed_documents([text])
        return result[0]

class EmbeddingClientManager:
    """
    向量数据库驱动
    """
    def __init__(self,conf:dict):
        self.client: TEIEmbeddingClient |None =None
        self.config= conf

    def _get_url(self):
        return f"{self.config['embedding_url']}"


    def init(self):
        self.client=TEIEmbeddingClient(self._get_url())

embedding_client_manager=EmbeddingClientManager(get_db_config())