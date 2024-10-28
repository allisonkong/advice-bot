"""Library for accessing the database."""

from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

from advice_bot import params

# Global database.Connection pool, lazily loaded and refreshed as needed.
_CNX_POOL = None


def _CreatePool() -> MySQLConnectionPool:
    return MySQLConnectionPool(pool_name="main_pool",
                               pool_size=5,
                               pool_reset_session=True,
                               **params.MysqlConnectionArgs())


def Connect() -> PooledMySQLConnection:
    """Returns a database.Connection, creating the pool lazily.

  Raises PoolError if no connections are available.
  """
    global _CNX_POOL
    if _CNX_POOL is None:
        _CNX_POOL = _CreatePool()
    return _CNX_POOL.get_connection()
