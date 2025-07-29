import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# [수정] 아래 두 함수는 기존 코드를 그대로 사용합니다.
def get_engine():
    try:
        # this works with Flask-SQLAlchemy<3 and Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except (TypeError, AttributeError):
        # this works with Flask-SQLAlchemy>=3
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    (이하 주석 생략)
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, 
        target_metadata=get_metadata(), 
        literal_binds=True,
        # [수정] SQLite 등에서 제약조건 오류를 방지하기 위해 아래 두 줄 추가
        render_as_batch=True,
        naming_convention=get_metadata().naming_convention,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    (이하 주석 생략)
    """
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    conf_args = current_app.extensions['migrate'].configure_args
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives
    
    # [수정] 이름 규칙을 conf_args에 명시적으로 추가
    conf_args['naming_convention'] = get_metadata().naming_convention
    # [수정] batch 모드 렌더링을 추가
    conf_args['render_as_batch'] = True

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()