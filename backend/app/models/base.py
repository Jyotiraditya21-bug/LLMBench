from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy database models.

    Automatically resolves table names as the snake_case pluralized version of the class name,
    and injects timestamp columns.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # Generate snake_case table name from ClassName (e.g. TestCase -> test_case)
        import re
        name = cls.__name__
        pattern = re.compile(r'(?<!^)(?=[A-Z])')
        name = pattern.sub('_', name).lower()
        
        # Pluralize simple cases
        if name.endswith('y'):
            return name[:-1] + 'ies'
        elif name.endswith('s'):
            return name + 'es'
        else:
            return name + 's'

    # Autoincrement integer primary key is default for all schemas
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Standard timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
