from typing import Callable, AsyncContextManager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from bottaxi.config import DbConfig


async def create_session_pool(db: DbConfig, echo=False) -> Callable[[], AsyncContextManager[AsyncSession]]:
	engine = create_async_engine(
		db.construct_sqlalchemy_url(),
		query_cache_size=1200,
		pool_size=20,
		max_overflow=200,
		future=True,
		echo=echo
	)

	session_pool = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

	return session_pool
