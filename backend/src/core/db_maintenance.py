"""
Database Maintenance and Optimization
Handles scheduled VACUUM ANALYZE and query performance monitoring
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .database import get_db_session

logger = structlog.get_logger()


class DatabaseMaintenance:
    """
    Database maintenance operations including VACUUM, ANALYZE,
    and performance monitoring.
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.maintenance_history: List[Dict[str, Any]] = []
        self.is_running = False
        
    async def vacuum_analyze_tables(
        self,
        session: Optional[AsyncSession] = None,
        tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run VACUUM ANALYZE on specified tables or all tables.
        
        Args:
            session: Database session (will create one if not provided)
            tables: List of table names (all tables if None)
            
        Returns:
            Dictionary with maintenance results
        """
        start_time = datetime.now()
        results = {
            "start_time": start_time.isoformat(),
            "tables_processed": [],
            "errors": [],
            "duration_seconds": 0
        }
        
        # Use provided session or create new one
        if session is None:
            async for db_session in get_db_session():
                session = db_session
                break
        
        try:
            # Get list of tables if not specified
            if tables is None:
                table_query = """
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """
                result = await session.execute(text(table_query))
                tables = [row[0] for row in result.fetchall()]
            
            logger.info(f"Starting VACUUM ANALYZE for {len(tables)} tables")
            
            # Process each table
            for table_name in tables:
                try:
                    # VACUUM ANALYZE cannot run in a transaction
                    await session.execute(text("COMMIT"))
                    await session.execute(
                        text(f"VACUUM ANALYZE {table_name}")
                    )
                    results["tables_processed"].append(table_name)
                    logger.debug(f"✅ VACUUM ANALYZE completed for {table_name}")
                    
                except Exception as e:
                    error_msg = f"Failed to VACUUM ANALYZE {table_name}: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            results["duration_seconds"] = duration
            results["end_time"] = datetime.now().isoformat()
            
            # Store in history
            self.maintenance_history.append(results)
            
            # Keep only last 30 days of history
            cutoff = datetime.now() - timedelta(days=30)
            self.maintenance_history = [
                h for h in self.maintenance_history
                if datetime.fromisoformat(h["start_time"]) > cutoff
            ]
            
            logger.info(
                f"✅ VACUUM ANALYZE completed: {len(results['tables_processed'])} tables "
                f"in {duration:.2f} seconds"
            )
            
        except Exception as e:
            logger.error(f"VACUUM ANALYZE failed: {e}")
            results["errors"].append(str(e))
        
        return results
    
    async def analyze_slow_queries(
        self,
        session: Optional[AsyncSession] = None,
        threshold_ms: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Analyze slow queries using pg_stat_statements.
        
        Args:
            session: Database session
            threshold_ms: Minimum query time in milliseconds
            
        Returns:
            List of slow queries with statistics
        """
        if session is None:
            async for db_session in get_db_session():
                session = db_session
                break
        
        slow_queries = []
        
        try:
            # Check if pg_stat_statements extension is available
            check_extension = """
                SELECT EXISTS (
                    SELECT 1 
                    FROM pg_extension 
                    WHERE extname = 'pg_stat_statements'
                )
            """
            result = await session.execute(text(check_extension))
            has_extension = result.scalar()
            
            if not has_extension:
                logger.warning("pg_stat_statements extension not installed")
                return []
            
            # Get slow queries
            slow_query_sql = """
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    stddev_exec_time,
                    rows,
                    100.0 * shared_blks_hit / 
                        NULLIF(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements
                WHERE mean_exec_time > :threshold_ms
                ORDER BY mean_exec_time DESC
                LIMIT 20
            """
            
            result = await session.execute(
                text(slow_query_sql),
                {"threshold_ms": threshold_ms}
            )
            
            for row in result.fetchall():
                slow_queries.append({
                    "query": row[0][:200],  # Truncate long queries
                    "calls": row[1],
                    "total_time_ms": round(row[2], 2),
                    "mean_time_ms": round(row[3], 2),
                    "stddev_time_ms": round(row[4], 2) if row[4] else 0,
                    "rows": row[5],
                    "cache_hit_percent": round(row[6], 2) if row[6] else 0
                })
            
            logger.info(f"Found {len(slow_queries)} slow queries (>{threshold_ms}ms)")
            
        except Exception as e:
            logger.error(f"Failed to analyze slow queries: {e}")
        
        return slow_queries
    
    async def get_table_statistics(
        self,
        session: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Get table size and bloat statistics.
        
        Returns:
            List of table statistics
        """
        if session is None:
            async for db_session in get_db_session():
                session = db_session
                break
        
        table_stats = []
        
        try:
            stats_query = """
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                                   pg_relation_size(schemaname||'.'||tablename)) AS indexes_size,
                    n_live_tup AS live_rows,
                    n_dead_tup AS dead_rows,
                    CASE WHEN n_live_tup > 0 
                         THEN round(100.0 * n_dead_tup / n_live_tup, 2)
                         ELSE 0 
                    END AS dead_percent,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """
            
            result = await session.execute(text(stats_query))
            
            for row in result.fetchall():
                table_stats.append({
                    "schema": row[0],
                    "table": row[1],
                    "total_size": row[2],
                    "table_size": row[3],
                    "indexes_size": row[4],
                    "live_rows": row[5],
                    "dead_rows": row[6],
                    "dead_percent": row[7],
                    "last_vacuum": row[8].isoformat() if row[8] else None,
                    "last_autovacuum": row[9].isoformat() if row[9] else None,
                    "last_analyze": row[10].isoformat() if row[10] else None,
                    "last_autoanalyze": row[11].isoformat() if row[11] else None
                })
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
        
        return table_stats
    
    async def optimize_indexes(
        self,
        session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Identify and suggest index optimizations.
        
        Returns:
            Dictionary with index optimization suggestions
        """
        if session is None:
            async for db_session in get_db_session():
                session = db_session
                break
        
        suggestions = {
            "unused_indexes": [],
            "duplicate_indexes": [],
            "missing_indexes": []
        }
        
        try:
            # Find unused indexes
            unused_query = """
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
                    idx_scan AS index_scans
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                AND indexrelid != 0
                ORDER BY pg_relation_size(indexrelid) DESC
            """
            
            result = await session.execute(text(unused_query))
            for row in result.fetchall():
                suggestions["unused_indexes"].append({
                    "schema": row[0],
                    "table": row[1],
                    "index": row[2],
                    "size": row[3],
                    "scans": row[4]
                })
            
            # Find duplicate indexes (simplified check)
            
            # Note: This is a simplified check. In production, you'd want
            # a more sophisticated duplicate detection
            
        except Exception as e:
            logger.error(f"Failed to optimize indexes: {e}")
        
        return suggestions
    
    def schedule_maintenance(
        self,
        vacuum_hour: int = 3,
        vacuum_minute: int = 0
    ):
        """
        Schedule daily VACUUM ANALYZE.
        
        Args:
            vacuum_hour: Hour to run (0-23)
            vacuum_minute: Minute to run (0-59)
        """
        if self.is_running:
            logger.warning("Maintenance scheduler already running")
            return
        
        # Schedule daily VACUUM ANALYZE
        self.scheduler.add_job(
            self.vacuum_analyze_tables,
            CronTrigger(hour=vacuum_hour, minute=vacuum_minute),
            id="daily_vacuum",
            replace_existing=True,
            max_instances=1
        )
        
        # Schedule hourly slow query analysis
        self.scheduler.add_job(
            self.analyze_slow_queries,
            CronTrigger(minute=0),  # Every hour at minute 0
            id="hourly_slow_queries",
            replace_existing=True,
            max_instances=1
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            f"✅ Database maintenance scheduled: "
            f"VACUUM at {vacuum_hour:02d}:{vacuum_minute:02d} daily"
        )
    
    def stop_maintenance(self):
        """Stop the maintenance scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Database maintenance scheduler stopped")
    
    def get_maintenance_status(self) -> Dict[str, Any]:
        """
        Get current maintenance status and history.
        
        Returns:
            Dictionary with maintenance status
        """
        jobs = []
        if self.scheduler.running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
        
        return {
            "is_running": self.is_running,
            "scheduled_jobs": jobs,
            "recent_maintenance": self.maintenance_history[-5:] if self.maintenance_history else [],
            "total_runs": len(self.maintenance_history)
        }


# Singleton instance
_db_maintenance = None


def get_db_maintenance() -> DatabaseMaintenance:
    """Get or create the database maintenance singleton."""
    global _db_maintenance
    
    if _db_maintenance is None:
        _db_maintenance = DatabaseMaintenance()
    
    return _db_maintenance