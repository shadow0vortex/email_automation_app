"""
Database Manager - PostgreSQL Operations
Handles all database interactions with connection pooling and error handling
"""

import psycopg2
from psycopg2 import pool, extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
import os
from datetime import datetime
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations"""
    
    def __init__(self, config_path="config/database.json"):
        self.config_path = config_path
        self.connection_pool = None
        self.config = self.load_config()
        self.init_connection_pool()
    
    def load_config(self):
        """Load database configuration from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default configuration
                return {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'email_automation',
                    'user': 'email_app_user',
                    'password': 'secure_password'
                }
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return None
    
    def save_config(self, config):
        """Save database configuration to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            self.config = config
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def init_connection_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            if self.config:
                self.connection_pool = pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=self.config['host'],
                    port=self.config['port'],
                    database=self.config['database'],
                    user=self.config['user'],
                    password=self.config['password']
                )
                logger.info("Connection pool created successfully")
                return True
        except Exception as e:
            logger.error(f"Error creating connection pool: {e}")
            self.connection_pool = None
            return False
    
    def get_connection(self):
        """Get a connection from the pool"""
        if self.connection_pool:
            try:
                return self.connection_pool.getconn()
            except Exception as e:
                logger.error(f"Error getting connection: {e}")
                return None
        return None
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)
    
    def test_connection(self):
        """Test database connection"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                self.return_connection(conn)
                return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query, params=None, fetch=False):
        """Execute a query with error handling"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return None
            
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            cursor.execute(query, params)
            
            if fetch:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            conn.commit()
            cursor.close()
            return result
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Query execution error: {e}")
            return None
        finally:
            if conn:
                self.return_connection(conn)
    
    # ==================== CAMPAIGN OPERATIONS ====================
    
    def create_campaign(self, name, total_emails, subject="", template_used=""):
        """Create a new email campaign"""
        try:
            campaign_id = str(uuid.uuid4())
            query = """
                INSERT INTO campaigns (id, name, total_emails, subject, template_used)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            result = self.execute_query(
                query, 
                (campaign_id, name, total_emails, subject, template_used),
                fetch=True
            )
            return campaign_id if result else None
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return None
    
    def update_campaign(self, campaign_id, successful=0, failed=0, pending=0):
        """Update campaign statistics"""
        try:
            query = """
                UPDATE campaigns 
                SET successful = successful + %s,
                    failed = failed + %s,
                    pending = pending + %s,
                    end_time = CASE 
                        WHEN (successful + failed + %s + %s) >= total_emails 
                        THEN CURRENT_TIMESTAMP 
                        ELSE end_time 
                    END
                WHERE id = %s
            """
            self.execute_query(query, (successful, failed, pending, successful, failed, campaign_id))
            return True
        except Exception as e:
            logger.error(f"Error updating campaign: {e}")
            return False
    
    def get_campaign(self, campaign_id):
        """Get campaign details"""
        query = "SELECT * FROM campaigns WHERE id = %s"
        result = self.execute_query(query, (campaign_id,), fetch=True)
        return result[0] if result else None
    
    def get_recent_campaigns(self, limit=10):
        """Get recent campaigns"""
        query = """
            SELECT id, name, total_emails, successful, failed, 
                   start_time, end_time
            FROM campaigns 
            ORDER BY start_time DESC 
            LIMIT %s
        """
        return self.execute_query(query, (limit,), fetch=True)
    
    # ==================== EMAIL LOG OPERATIONS ====================
    
    def log_email(self, recipient_email, recipient_name, subject, status, 
                  error_message=None, campaign_id=None):
        """Log an email sending attempt"""
        try:
            query = """
                INSERT INTO email_logs 
                (recipient_email, recipient_name, subject, status, error_message, campaign_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.execute_query(
                query, 
                (recipient_email, recipient_name, subject, status, error_message, campaign_id)
            )
            
            # Update campaign statistics
            if campaign_id:
                if status == 'Success':
                    self.update_campaign(campaign_id, successful=1)
                elif status == 'Failed':
                    self.update_campaign(campaign_id, failed=1)
            
            return True
        except Exception as e:
            logger.error(f"Error logging email: {e}")
            return False
    
    def log_emails_batch(self, email_logs):
        """Batch insert email logs for better performance"""
        conn = None
        try:
            conn = self.get_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            query = """
                INSERT INTO email_logs 
                (recipient_email, recipient_name, subject, status, error_message, campaign_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            extras.execute_batch(cursor, query, email_logs)
            conn.commit()
            cursor.close()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Batch insert error: {e}")
            return False
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_logs(self, limit=1000, campaign_id=None, status_filter=None):
        """Retrieve email logs with optional filters"""
        try:
            query = """
                SELECT recipient_email, recipient_name, subject, status, 
                       error_message, timestamp, campaign_id
                FROM email_logs
            """
            params = []
            conditions = []
            
            if campaign_id:
                conditions.append("campaign_id = %s")
                params.append(campaign_id)
            
            if status_filter and status_filter != 'All':
                conditions.append("status = %s")
                params.append(status_filter)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            return self.execute_query(query, tuple(params), fetch=True)
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            return []
    
    def get_log_statistics(self, campaign_id=None):
        """Get email statistics"""
        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending
            FROM email_logs
        """
        
        if campaign_id:
            query += " WHERE campaign_id = %s"
            result = self.execute_query(query, (campaign_id,), fetch=True)
        else:
            result = self.execute_query(query, fetch=True)
        
        return result[0] if result else None
    
    # ==================== CONFIGURATION OPERATIONS ====================
    
    def save_config_value(self, key, value):
        """Save configuration key-value pair"""
        try:
            query = """
                INSERT INTO config (key, value, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (key) 
                DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
            """
            self.execute_query(query, (key, value))
            return True
        except Exception as e:
            logger.error(f"Error saving config value: {e}")
            return False
    
    def get_config_value(self, key, default=None):
        """Retrieve configuration value"""
        try:
            query = "SELECT value FROM config WHERE key = %s"
            result = self.execute_query(query, (key,), fetch=True)
            return result[0]['value'] if result else default
        except Exception as e:
            logger.error(f"Error getting config value: {e}")
            return default
    
    def get_all_config(self):
        """Get all configuration values"""
        query = "SELECT key, value FROM config"
        return self.execute_query(query, fetch=True)
    
    # ==================== TEMPLATE OPERATIONS ====================
    
    def save_template(self, name, subject, body_html, placeholders):
        """Save email template"""
        try:
            query = """
                INSERT INTO templates (name, subject, body_html, placeholders)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """
            result = self.execute_query(
                query, 
                (name, subject, body_html, placeholders),
                fetch=True
            )
            return result[0]['id'] if result else None
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            return None
    
    def get_templates(self, active_only=True):
        """Get all templates"""
        query = "SELECT * FROM templates"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"
        return self.execute_query(query, fetch=True)
    
    def get_template(self, template_id):
        """Get specific template"""
        query = "SELECT * FROM templates WHERE id = %s"
        result = self.execute_query(query, (template_id,), fetch=True)
        return result[0] if result else None
    
    # ==================== RECIPIENT OPERATIONS ====================
    
    def add_recipient(self, email, name=None, company=None, custom_fields=None):
        """Add or update recipient"""
        try:
            query = """
                INSERT INTO recipients (email, name, company, custom_fields)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    company = EXCLUDED.company,
                    custom_fields = EXCLUDED.custom_fields,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            custom_json = json.dumps(custom_fields) if custom_fields else None
            result = self.execute_query(query, (email, name, company, custom_json), fetch=True)
            return result[0]['id'] if result else None
        except Exception as e:
            logger.error(f"Error adding recipient: {e}")
            return None
    
    def get_recipients(self, active_only=True):
        """Get all recipients"""
        query = "SELECT * FROM recipients"
        if active_only:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"
        return self.execute_query(query, fetch=True)
    
    # ==================== CLEANUP OPERATIONS ====================
    
    def cleanup_old_logs(self, days=90):
        """Delete logs older than specified days"""
        try:
            query = """
                DELETE FROM email_logs 
                WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '%s days'
            """
            result = self.execute_query(query, (days,))
            logger.info(f"Deleted {result} old log entries")
            return result
        except Exception as e:
            logger.error(f"Error cleaning up logs: {e}")
            return 0
    
    def close_all_connections(self):
        """Close all connections in pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All connections closed")