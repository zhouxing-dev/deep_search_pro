import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.tools import tool

from api.monitor import monitor
from clients.mysql_client_manager import db_client_manager
from repositories.mysql_repository import MysqlRepository

load_dotenv()



@tool
async def list_sql_tables()-> Annotated[str, "数据库中可用的表名列表，以逗号分割"]:
    """
    列出配置的 MySQL 数据库中所有可用的表。
    核心用途：
        AI Agent 需要查看数据库中有哪些表时调用，为后续执行 SQL 查询提供基础信息。
    返回值：
        str: 成功时返回 "可用数据表：表1, 表2, ..."；
             配置缺失时返回错误提示；
             执行异常时返回具体错误信息。
    异常处理：
        捕获数据库连接/执行 SQL 时的所有 Error 异常，返回可读的错误信息，避免 Agent 崩溃。
    """
    #埋点
    monitor.report_tool(tool_name="数据库表获取工具")
    #建立数据库链接
    db_client_manager.init()
    async with db_client_manager.session_factory() as db_session:
        mysql_repository=MysqlRepository(db_session)
        res=await mysql_repository.get_table_list()
    return res


@tool
async def get_table_data(table_name):
    """
    查询指定表名的数据！当工具调用之前，必须先调用list_sql_tables完成表名的校验！
    此工具的作用 1完成单表数据的查询2.可以为多表查询提供表结果信息（列名和数据格式）
    :param table_name: 表名
    :return:
    """
    #建立数据库链接
    db_client_manager.init()
    monitor.report_tool(tool_name="表中数据查询工具")
    async with db_client_manager.session_factory() as db_session:
        mysql_repository=MysqlRepository(db_session)
        res=await mysql_repository.get_table_data(table_name)
    return res

@tool
async def execute_sql(sql):
    """
    这是一个查询sql的工具，可以支持在数据库查询数据
    :param sql:sql语句
    :return: 数据库查询结果
    """
    #建立数据库链接
    db_client_manager.init()
    monitor.report_tool(tool_name="执行自定义sql工具")
    async with db_client_manager.session_factory() as db_session:
        mysql_repository=MysqlRepository(db_session)
        res=await mysql_repository.execute_sql(sql)
    return res


if __name__ == '__main__':
    result = asyncio.run(execute_sql.ainvoke({"sql": "select * from drugs limit 1"}))
