from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import select
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    async with engine.begin() as conn:
        from app.models import user, clinic, doctor, patient, appointment, visit, prescription, bill, blocked_slot  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

    # Seed initial data
    async with AsyncSessionLocal() as session:
        from app.models.user import User, UserRole
        from app.models.clinic import Clinic
        from app.core.security import hash_password

        # Check if users exist
        result = await session.execute(select(User).limit(1))
        first_user = result.scalar_one_or_none()

        if not first_user:
            # Create a default clinic
            default_clinic = Clinic(
                name="MediCall Demo Clinic",
                address="123 Health Street",
                phone="9988776655",
                gstin="22AAAAA0000A1Z5"
            )
            session.add(default_clinic)
            await session.commit()
            
            # Create default admin user
            admin_user = User(
                name="Admin User",
                email="admin@medicall.com",
                hashed_password=hash_password("admin123"),
                role=UserRole.superadmin,
                clinic_id=default_clinic.id
            )
            session.add(admin_user)
            await session.commit()
            print("Seeded database with default clinic and admin@medicall.com user")
