from typing import List

from qdrant_client import AsyncQdrantClient
from qdrant_client.grpc import ScoredPoint
from qdrant_client.http.models import VectorParams, Distance, PointStruct


class QdrantRepository:
    """
    向量数据库仓库
    """
    collection_name="knowledge"
    def __init__(self,client:AsyncQdrantClient):
        self.client=client


    async def ensure_collection(self):
        if not await self.client.collection_exists(self.collection_name):
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )

    async def upsert(self, ids, embeddings, payloads):
        points:list[PointStruct]=[PointStruct(id=id,vector=embedding,payload=payload) for id,embedding,payload  in zip(ids,embeddings,payloads)]
        for i in range(0,len(points),20):
            await self.client.upsert(
                collection_name=self.collection_name,
                points=points[i:i+20]
            )

    async def rag_search(self, embedding: str)->List[str]:
        answer=await self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            score_threshold=0.5,
            limit=5
        )
        print(answer)
        return [str(point.payload['page_content']) for point in answer.points]

