from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MysqlRepository:
    """
    数据库仓库
    """
    def __init__(self,session:AsyncSession):
        self.session=session

    async def get_table_list(self):
        sql=f"show tables"
        res=await self.session.execute(text(sql))
        res2=res.mappings().fetchall()
        print(res2)
        return ",".join([i['Tables_in_pharma_db'] for i in res2])

    async def get_table_data(self, table_name):
        sql=f"select * from {table_name} limit 100"
        res=await self.session.execute(text(sql))
        res1=res.mappings().fetchall()
        if not res:
            return f"数据表{table_name}为空"
        head=[key for key in res1[0].keys()]
        head_str=",".join(head)+"\n"
        for row in res1:
            head_str+=",".join([str(value) for value in row.values()])+"\n"
        return head_str

    async def execute_sql(self, sql:str):
        sql=sql.strip()
        if sql.startswith("select"):
            res = await self.session.execute(text(sql))
            res1 = res.mappings().fetchall()
            if not res:
                return f"自定义SQL查询结果为空"
            head = [key for key in res1[0].keys()]
            head_str = ",".join(head) + "\n"
            for row in res1:
                head_str += ",".join([str(value) for value in row.values()]) + "\n"
            print(head_str)
            return head_str
        else:
            return "此工具只支持查询语句"



