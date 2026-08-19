from typing import Literal

from langchain_core.tools import tool
from tavily import TavilyClient

from api.monitor import monitor

tavily_client=TavilyClient(api_key="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")


@tool
def internet_search(query: str,
                    max_results: int = 5,
                    topic: Literal["news", "finance", "general"] = "general",
                    include_raw_content: bool = False
                    ):
    """
    互联网搜索工具! 用于网络信息搜索
    :param query: 搜索关键词
    :param max_results: 返回的条数
    :param topic: 查询新闻类型
    :param include_raw_content: 是否精简 false 精简 true 详细
    :return: 查询结果
    """
    monitor.report_tool(tool_name="网络搜索工具",args={"query":query,"max_results":max_results,"topic":topic,"include_raw_content":include_raw_content})
    return tavily_client.search(query=query,topic=topic,max_results=max_results,include_raw_content=include_raw_content)