from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.core.database import Base
from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.evidence import models as evidence_models  # noqa: F401
from app.modules.projects import models as project_models  # noqa: F401
from app.modules.sources import models as source_models  # noqa: F401

config = context.config
fileConfig(config.config_file_name)
settings = get_settings()
url = settings.migration_database_url
if not url:
    raise RuntimeError("MIGRATION_DATABASE_URL is required; do not migrate using the runtime role")

if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(url, hide_parameters=True)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
