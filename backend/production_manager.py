#!/usr/bin/env python3
"""
Pavitra Trading - Production Service Manager
Manages all microservices in production mode
"""

import subprocess
import time
import signal
import sys
import logging
from typing import List, Dict
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Service configurations
SERVICES = {
    'auth_service': {
        'port': 8001,
        'command': ['uvicorn', 'auth_service.simple_db_service:app', '--host', '0.0.0.0', '--port', '8001', '--workers', '2']
    },
    'product_service': {
        'port': 8002, 
        'command': ['uvicorn', 'product_service.main:app', '--host', '0.0.0.0', '--port', '8002', '--workers', '2']
    },
    'order_service': {
        'port': 8003,
        'command': ['uvicorn', 'order_service.main:app', '--host', '0.0.0.0', '--port', '8003', '--workers', '2']
    },
    'user_service': {
        'port': 8004,
        'command': ['uvicorn', 'user_service.main:app', '--host', '0.0.0.0', '--port', '8004', '--workers', '2']
    },
    'payment_service': {
        'port': 8005,
        'command': ['uvicorn', 'payment_service.main:app', '--host', '0.0.0.0', '--port', '8005', '--workers', '2']
    },
    'notification_service': {
        'port': 8006,
        'command': ['uvicorn', 'notification_service.main:app', '--host', '0.0.0.0', '--port', '8006', '--workers', '2']
    }
}

class ProductionManager:
    def __init__(self):
        self.processes = {}
        
    def start_services(self):
        """Start all microservices"""
        logger.info("Starting all microservices in production mode...")
        
        for service_name, config in SERVICES.items():
            try:
                logger.info(f"Starting {service_name} on port {config['port']}...")
                
                # Start service with output redirected to log file
                log_file = open(f'logs/{service_name}/production.log', 'w')
                process = subprocess.Popen(
                    config['command'],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                self.processes[service_name] = {
                    'process': process,
                    'log_file': log_file,
                    'port': config['port']
                }
                
                logger.info(f"✅ {service_name} started (PID: {process.pid})")
                
            except Exception as e:
                logger.error(f"❌ Failed to start {service_name}: {e}")
        
        # Wait for services to start
        logger.info("Waiting for services to initialize...")
        time.sleep(10)
        
        # Health check
        self.health_check()
    
    def health_check(self):
        """Check health of all services"""
        logger.info("Performing health checks...")
        
        healthy_count = 0
        for service_name, info in self.processes.items():
            port = info['port']
            try:
                response = requests.get(f'http://localhost:{port}/health', timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ {service_name} (port {port}): HEALTHY")
                    healthy_count += 1
                else:
                    logger.warning(f"⚠️ {service_name} (port {port}): HTTP {response.status_code}")
            except Exception as e:
                logger.error(f"❌ {service_name} (port {port}): UNHEALTHY - {e}")
        
        logger.info(f"Health Summary: {healthy_count}/{len(SERVICES)} services healthy")
        
        if healthy_count == len(SERVICES):
            logger.info("🎉 All services are running successfully!")
            self.print_service_info()
        else:
            logger.warning("Some services may need attention. Check logs for details.")
    
    def print_service_info(self):
        """Print service information"""
        print("\n" + "="*50)
        print("🚀 PAVITRA TRADING - PRODUCTION SERVICES")
        print("="*50)
        for service_name, info in self.processes.items():
            print(f"📍 {service_name.replace('_', ' ').title():20} http://localhost:{info['port']}")
        print("\n📊 Health Check: curl http://localhost:8001/health")
        print("👤 Test Auth:    curl http://localhost:8001/users") 
        print("🛍️ Test Products: curl http://localhost:8002/products")
        print("\n🛑 To stop:     pkill -f uvicorn")
        print("📋 View logs:   tail -f logs/*/production.log")
        print("="*50)
    
    def stop_services(self):
        """Stop all services gracefully"""
        logger.info("Stopping all services...")
        
        for service_name, info in self.processes.items():
            try:
                process = info['process']
                log_file = info['log_file']
                
                # Send SIGTERM
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    logger.info(f"✅ {service_name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if not responding
                    process.kill()
                    logger.warning(f"⚠️ {service_name} force stopped")
                
                # Close log file
                log_file.close()
                
            except Exception as e:
                logger.error(f"Error stopping {service_name}: {e}")
        
        self.processes.clear()
        logger.info("All services stopped.")
    
    def monitor_services(self):
        """Monitor services (run until interrupted)"""
        try:
            logger.info("Production services running. Press Ctrl+C to stop.")
            while True:
                time.sleep(60)  # Check every minute
                # Optional: Add periodic health checks here
                
        except KeyboardInterrupt:
            logger.info("Shutdown signal received...")
            self.stop_services()

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == 'stop':
        manager = ProductionManager()
        # Find and stop all uvicorn processes
        subprocess.run(['pkill', '-f', 'uvicorn'])
        logger.info("All services stopped.")
        return
    
    manager = ProductionManager()
    
    try:
        # Start services
        manager.start_services()
        
        # Monitor until interrupted
        manager.monitor_services()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        manager.stop_services()
        sys.exit(1)

if __name__ == "__main__":
    main()
