"""
Database utility module for Student Portal.
Provides database utility functions for service layer.
"""

from flask import current_app
from . import db


def get_db():
    """Get the database instance for the current app context."""
    return db


def get_db_instance():
    """Get the SQLAlchemy instance."""
    return db


# For backward compatibility with existing code that expects a connection-like object
# We'll implement a minimal interface that works with SQLAlchemy 2.0+
def execute_query(query, params=None):
    """Execute a SQL query and return results.

    Args:
        query (str): SQL query string
        params (tuple|dict, optional): Parameters for the query

    Returns:
        ResultProxy: SQLAlchemy result object
    """
    with db.engine.connect() as conn:
        if params:
            result = conn.execute(db.text(query), params)
        else:
            result = conn.execute(db.text(query))
        return result