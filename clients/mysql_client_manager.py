from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from utils.env_utils import get_db_config


class MysqlClientManger:
    """
    数据库驱动
    """
    def __init__(self,config:dict):
        self.engine: AsyncEngine | None=None
        self.config = config
        self.session_factory: async_sessionmaker | None = None

    def _get_url(self):
        return f"mysql+asyncmy://{self.config["user"]}:{self.config["password"]}@{self.config['host']}:{self.config['port']}/{self.config['database']}"

    def init(self):
        self.engine = create_async_engine(self._get_url(),pool_size=10,pool_pre_ping=True)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)



db_client_manager=MysqlClientManger(get_db_config())
