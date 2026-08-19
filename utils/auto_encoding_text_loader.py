from typing import Iterator, List

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document


class AutoEncodingTextLoader(TextLoader):
    def __init__(self,file_path,encodings:List=None,**kwargs):
        self.encodings=encodings or ['utf-8','gbk']
        super().__init__(file_path=file_path,**kwargs)

    def lazy_load(self) -> Iterator[Document]:
        last_exception=None
        for encoding in self.encodings:
            try:
                self.encoding=encoding
                yield from super().lazy_load()
                return
            except (UnicodeDecodeError, RuntimeError) as e:
                # 记录最后一次异常，继续尝试下一种编码
                last_exception = e
                continue

        # 如果所有编码都失败了，抛出异常
        raise RuntimeError(
            f"Error loading {self.file_path}. Tried encodings: {self.encodings}"
        ) from last_exception

