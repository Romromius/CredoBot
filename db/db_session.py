import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import logging

SqlAlchemyBase = orm.declarative_base()

__factory = None


def global_init(db_file) -> None:
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise FileExistsError("Path to db isn't specified.")

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    logging.info(f"Connecting to db at {conn_str}")

    engine = sa.create_engine(conn_str, pool_size=20, max_overflow=30, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    import db.__all_models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    try:
        return __factory()
    except TypeError:
        logging.error('__factory is None. Maybe you forgot global_init()')
