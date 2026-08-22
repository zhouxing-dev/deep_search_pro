import asyncio
import hashlib
import os.path
import uuid
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader, UnstructuredExcelLoader, \
    DirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from clients.embedding_client_manager import embedding_client_manager
from clients.qdrant_client_manager import qdrant_client_manager
from repositories.qdrant_repository import QdrantRepository
from utils.auto_encoding_text_loader import AutoEncodingTextLoader

# 读取md5文件
base_path = Path(__file__).parent
md5_file_path = base_path / 'md5.txt'

def load_document():
    """
    加载文档，基于md5去重
    :return:
    """
    supported_extensions = [".docx", ".pdf", ".xlsx",'.txt']
    all_documents=[]
    md5_set=set()
    if not os.path.exists(md5_file_path):
        with open(md5_file_path,'w',encoding='utf-8'):
            pass
    else:
        with open(md5_file_path,'r',encoding='utf-8') as f:
            md5_set={line.strip()  for line in f.readlines() if line.strip()}

    for ext in supported_extensions:
        pattern=f"*{ext}"
        if ext == ".pdf":
            loader_cls=PyMuPDFLoader
            loader_kwargs={}
        elif ext == ".docx":
            loader_cls=Docx2txtLoader
            loader_kwargs={}
        elif ext == ".txt":
            loader_cls=AutoEncodingTextLoader
            loader_kwargs={"encoding":"utf-8"}
        else:
            loader_cls=UnstructuredExcelLoader
            loader_kwargs={}

        loader=DirectoryLoader(
            str(base_path/'知识库文件'),
            glob=pattern,
            loader_cls=loader_cls,
            loader_kwargs=loader_kwargs,
            recursive=True
        )
        # documents=loader.load()

        documents=loader.lazy_load()
        new_count =0
        md5_value_list=[]
        for document in documents:
            text_bytes=document.page_content.encode('utf-8')
            print(document.page_content)
            length=len(text_bytes)
            if length == 0 :
                continue
            start=0
            hash_obj=hashlib.md5()
            while start < length:
                chunk_size=4096
                chunk=text_bytes[start:start+chunk_size]
                hash_obj.update(chunk)
                start+=chunk_size
            md5_value = hash_obj.hexdigest()
            if md5_value not in md5_set:
                all_documents.append(document)
                # _save_md5(md5_value_list)
                md5_value_list.append(md5_value)
                new_count+=1
            else:
                print(f"文档已处理过，将会跳过：{document.metadata.get('source')}")
        _save_md5(md5_value_list)
    return all_documents


def split_document(documents:List[Document]):
    """
    分割文档，使用文本分割器将 list 的document分割为 比较小的块，并且为每个块添加元数据信息
    :param documents:
    :return:
    """
    print("before split"+"|".join([document.page_content for document in documents])+"|")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
    )
    splits=text_splitter.split_documents(documents)
    for i, split in enumerate(splits):
        source=split.metadata.get('source', 'unknown')
        split.metadata['chunk_id']=f"{uuid.uuid4()}"
        split.metadata['doc_id']=split.metadata.get('doc_id', 'unknown')
        split.metadata['source']=source

    return splits





def _save_md5(md5_value_list):
    """
    保存md5
    :param md5_value_list:
    :return:
    """
    if not md5_value_list:
        return
    try:
        with open(base_path/'md5.txt','a',encoding='utf-8') as f:
            f.write('\n'.join(md5_value_list)+'\n')
    except Exception as e:
        print(f"保存md5错误：{e}")


async def upload_file():
    """
    知识库向量化
    :return: 向量化结果统计信息（新增文档数、切片数）
    """
    embedding_client_manager.init()
    qdrant_client_manager.init()
    documents=load_document()
    if len(documents)==0:
        print("没有需要上传的文档")
        return {"new_documents": 0, "chunks": 0, "message": "没有需要上传的文档"}
    #分割文档
    splits=split_document(documents)
    # 分割后的文档向量化
    embedding_texts=[split.page_content for split in splits]
    embeddings:List[List[float]]=[]
    # [[1.3,1.2,33,1.4],[1.3,1.6,1.9]]
    for i in range(0,len(embedding_texts),2):
        batch_embedding_texts=embedding_texts[i:i+2]
        if batch_embedding_texts:
            max_len = max(len(str(text)) for text in batch_embedding_texts)
            print(f"当前送入向量的最大文本长度: {max_len} 字符")
        batch_embeddings=await embedding_client_manager.client.aembed_documents(batch_embedding_texts)
        embeddings.extend(batch_embeddings)
    ids=[split.metadata['chunk_id'] for split in splits]
    payloads=[{"page_content":split.page_content} for split in splits]
    qdrant=QdrantRepository(qdrant_client_manager.client)
    await qdrant.ensure_collection()
    await qdrant.upsert(ids=ids,embeddings=embeddings,payloads=payloads)
    print(f"知识库向量化完成：新增文档 {len(documents)} 个，写入切片 {len(splits)} 个")
    return {"new_documents": len(documents), "chunks": len(splits), "message": "知识库向量化完成"}

if __name__ == '__main__':
    asyncio.run(upload_file())






