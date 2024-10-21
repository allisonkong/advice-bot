"""Library for accessing the database."""

from mysql.connector.pooling import MySQLConnectionPool, PooledMySQLConnection

import params

# Global database.Connection pool, lazily loaded and refreshed as needed.
_CNX_POOL = None


def _CreatePool() -> MySQLConnectionPool:
    mysql_params = params.GetParams().mysql_params
    return MySQLConnectionPool(pool_name="main_pool",
                               pool_size=5,
                               pool_reset_session=True,
                               **mysql_params.ConnectionArgs())


def Connect() -> PooledMySQLConnection:
    """Returns a database.Connection, creating the pool lazily.

  Raises PoolError if no connections are available.
  """
    global _CNX_POOL
    if _CNX_POOL is None:
        _CNX_POOL = _CreatePool()
    return _CNX_POOL.get_connection()
