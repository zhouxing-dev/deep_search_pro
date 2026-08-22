import os

from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import init_chat_model

#加载配置文件,确保找到.env文件，递归查询当前项目文件
# override=True：.env 中的值覆盖进程里已有的同名环境变量，避免旧 key 残留导致 invalid_api_key
load_dotenv(find_dotenv(), override=True)

model=init_chat_model(
    model=os.getenv("LLM_QWEN3.7"),
    # 通义千问走 OpenAI 兼容接口（OPENAI_BASE_URL / OPENAI_API_KEY），需显式指定 provider
    model_provider="openai",
)