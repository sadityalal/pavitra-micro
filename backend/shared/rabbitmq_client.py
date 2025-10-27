import pika
import json
import logging
import time
from typing import Dict, Any, Callable
from shared import config, get_logger

logger = get_logger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connected = False
        
    def _get_connection_parameters(self):
        """Get connection parameters from config"""
        try:
            # Refresh config to get latest settings
            config.refresh_cache()
            
            # Construct AMQP URL from configuration
            amqp_url = f"amqp://{config.rabbitmq_user}:{config.rabbitmq_password}@{config.rabbitmq_host}:{config.rabbitmq_port}/"
            
            logger.info(f"Connecting to RabbitMQ at {config.rabbitmq_host}:{config.rabbitmq_port} as user {config.rabbitmq_user}")
            
            return pika.URLParameters(amqp_url)
        except Exception as e:
            logger.error(f"Error constructing RabbitMQ connection parameters: {e}")
            raise

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            if self.connected and self.connection and not self.connection.is_closed:
                return True
                
            parameters = self._get_connection_parameters()
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.connected = True
            
            # Declare the exchange
            self.channel.exchange_declare(
                exchange='notification_events',
                exchange_type='topic',
                durable=True
            )
            
            # Declare the queue
            self.channel.queue_declare(
                queue='notification_queue',
                durable=True
            )
            
            # Bind queue to exchange
            self.channel.queue_bind(
                exchange='notification_events',
                queue='notification_queue',
                routing_key='user.*'
            )
            
            # Bind other routing keys
            bindings = [
                'order.*',
                'payment.*',
                'refund.*',
                'stock.*'
            ]
            
            for routing_key in bindings:
                self.channel.queue_bind(
                    exchange='notification_events',
                    queue='notification_queue',
                    routing_key=routing_key
                )
            
            logger.info("✅ Successfully connected to RabbitMQ")
            return True
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"❌ RabbitMQ connection error: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            self.connected = False
            return False

    def ensure_connection(self):
        """Ensure we have a valid connection"""
        try:
            if not self.connected or self.connection is None or self.connection.is_closed:
                return self.connect()
            return True
        except Exception as e:
            logger.error(f"Error ensuring RabbitMQ connection: {e}")
            return False

    def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any]):
        """Publish message to RabbitMQ exchange"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    logger.error(f"Attempt {attempt + 1}/{max_retries}: Cannot publish message - not connected to RabbitMQ")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    continue
                    
                self.channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # make message persistent
                        content_type='application/json',
                        timestamp=int(time.time())
                    )
                )
                logger.info(f"📤 Message published to {exchange} with routing key {routing_key}")
                return True
                
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: RabbitMQ connection error during publish: {e}")
                self.connected = False
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Failed to publish message to RabbitMQ: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        logger.error(f"Failed to publish message after {max_retries} attempts")
        return False

    def consume_messages(self, queue: str, callback: Callable):
        """Consume messages from RabbitMQ queue"""
        try:
            if not self.ensure_connection():
                logger.error("Cannot consume messages - not connected to RabbitMQ")
                return
                
            def wrapped_callback(ch, method, properties, body):
                try:
                    message = json.loads(body.decode('utf-8'))
                    logger.info(f"📥 Received message from queue {queue}, routing key: {method.routing_key}")
                    callback(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    logger.info(f"✅ Message processed successfully: {method.routing_key}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to decode JSON message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    # Don't ack the message so it goes back to queue for retry
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # Set QoS to prefetch one message at a time
            self.channel.basic_qos(prefetch_count=1)
            
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=wrapped_callback,
                auto_ack=False
            )
            
            logger.info(f"🔄 Starting to consume messages from queue {queue}")
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
            self.connected = False
            raise

    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.connected = False
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

# Global instance
rabbitmq_client = RabbitMQClient()
