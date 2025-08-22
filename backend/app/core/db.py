from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI), echo=settings.DATABASE_ECHO, future=True
)
async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: AsyncSession) -> None:  # noqa ARG001
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines

    # async with engine.begin() as conn:
    #     # await conn.run_sync(SQLModel.metadata.drop_all)
    #     await conn.run_sync(SQLModel.metadata.create_all)
    pass
