import asyncio

from langchain_core.tools import tool

from clients.embedding_client_manager import embedding_client_manager
from clients.qdrant_client_manager import QdrantClientManager, qdrant_client_manager
from repositories.qdrant_repository import QdrantRepository


# @tool
async def rag_search(query: str):
    """
    需要进行本地知识库检索时调用此方法
    :param query: 需要检索的内容
    :return: 知识库中检索到的结果
    """
    qdrant_client_manager.init()
    embedding_client_manager.init()
    embedding =await embedding_client_manager.client.aembed_query(query)
    answers=await QdrantRepository(qdrant_client_manager.client).rag_search(embedding)
    [print(answer) for answer in answers]
    return "正在检索中..."

if __name__ == '__main__':
    asyncio.run(rag_search("每一个委员会由什么组成"))