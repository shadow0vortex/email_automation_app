"""
Database Setup - Automatic PostgreSQL initialization
Creates database, tables, and initial configuration on first run
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handles automatic database setup and initialization"""
    
    def __init__(self, config):
        self.config = config
    
    def create_database(self):
        """Create the email_automation database if it doesn't exist"""
        try:
            # Connect to default postgres database
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database='postgres',
                user=self.config['user'],
                password=self.config['password']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config['database'],)
            )
            exists = cursor.fetchone()
            
            if not exists:
                cursor.execute(f"CREATE DATABASE {self.config['database']}")
                logger.info(f"Database '{self.config['database']}' created successfully")
            else:
                logger.info(f"Database '{self.config['database']}' already exists")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    def create_tables(self):
        """Create all required tables"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()
            
            # Enable UUID extension
            cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
            
            # Table: campaigns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name VARCHAR(255) NOT NULL,
                    total_emails INTEGER NOT NULL DEFAULT 0,
                    successful INTEGER NOT NULL DEFAULT 0,
                    failed INTEGER NOT NULL DEFAULT 0,
                    pending INTEGER NOT NULL DEFAULT 0,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    created_by VARCHAR(255),
                    subject TEXT,
                    template_used TEXT
                )
            """)
            logger.info("Table 'campaigns' created")
            
            # Table: email_logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_logs (
                    id SERIAL PRIMARY KEY,
                    recipient_email VARCHAR(255) NOT NULL,
                    recipient_name VARCHAR(255),
                    subject TEXT,
                    status VARCHAR(20) NOT NULL CHECK (status IN ('Success', 'Failed', 'Pending')),
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    campaign_id UUID,
                    sent_by VARCHAR(255),
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
                )
            """)
            logger.info("Table 'email_logs' created")
            
            # Table: config
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key VARCHAR(100) PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Table 'config' created")
            
            # Table: recipients
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recipients (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    company VARCHAR(255),
                    custom_fields JSONB,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.info("Table 'recipients' created")
            
            # Table: templates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    subject TEXT,
                    body_html TEXT NOT NULL,
                    placeholders TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            logger.info("Table 'templates' created")
            
            # Table: email_queue (for scheduled emails)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS email_queue (
                    id SERIAL PRIMARY KEY,
                    recipient_email VARCHAR(255) NOT NULL,
                    subject TEXT NOT NULL,
                    body_html TEXT NOT NULL,
                    scheduled_time TIMESTAMP NOT NULL,
                    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Sent', 'Failed', 'Cancelled')),
                    campaign_id UUID,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE SET NULL
                )
            """)
            logger.info("Table 'email_queue' created")
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def create_indexes(self):
        """Create database indexes for performance"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_email_logs_campaign ON email_logs(campaign_id)",
                "CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status)",
                "CREATE INDEX IF NOT EXISTS idx_email_logs_timestamp ON email_logs(timestamp DESC)",
                "CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email)",
                "CREATE INDEX IF NOT EXISTS idx_campaigns_start_time ON campaigns(start_time DESC)",
                "CREATE INDEX IF NOT EXISTS idx_campaigns_end_time ON campaigns(end_time)",
                "CREATE INDEX IF NOT EXISTS idx_recipients_email ON recipients(email)",
                "CREATE INDEX IF NOT EXISTS idx_recipients_active ON recipients(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_templates_name ON templates(name)",
                "CREATE INDEX IF NOT EXISTS idx_templates_active ON templates(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_email_queue_scheduled ON email_queue(scheduled_time)",
                "CREATE INDEX IF NOT EXISTS idx_email_queue_status ON email_queue(status)"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            logger.info("All indexes created successfully")
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            return False
    
    def insert_default_config(self):
        """Insert default configuration values"""
        try:
            conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            cursor = conn.cursor()
            
            default_configs = [
                ('default_delay', '2'),
                ('smtp_server', 'smtp.gmail.com'),
                ('smtp_port', '587'),
                ('max_retry_attempts', '3'),
                ('database_version', '1.0'),
                ('app_version', '1.0.0'),
                ('batch_size', '100'),
                ('log_retention_days', '90')
            ]
            
            for key, value in default_configs:
                cursor.execute("""
                    INSERT INTO config (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key) DO NOTHING
                """, (key, value))
            
            logger.info("Default configuration inserted")
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error inserting default config: {e}")
            return False
    
    def setup_complete(self):
        """Run complete database setup"""
        logger.info("Starting database setup...")
        
        steps = [
            ("Creating database", self.create_database),
            ("Creating tables", self.create_tables),
            ("Creating indexes", self.create_indexes),
            ("Inserting default config", self.insert_default_config)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Failed at step: {step_name}")
                return False
        
        logger.info("Database setup completed successfully!")
        return True


def check_database_exists(config):
    """Check if database and tables exist"""
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
        cursor = conn.cursor()
        
        # Check if campaigns table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'campaigns'
            )
        """)
        exists = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        return exists
        
    except psycopg2.OperationalError:
        # Database doesn't exist
        return False
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False


if __name__ == "__main__":
    # Test database setup
    test_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'email_automation',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    setup = DatabaseSetup(test_config)
    success = setup.setup_complete()
    
    if success:
        print("✓ Database setup completed successfully!")
    else:
        print("✗ Database setup failed!")