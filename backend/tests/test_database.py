from sqlalchemy import text

from app.core.database import async_session_maker


async def test_session_works() -> None:
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
