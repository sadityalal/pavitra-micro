import pika
import json
import logging
import uuid
from datetime import datetime
import time
from typing import Dict, Any, Callable
from shared import config, get_logger

logger = get_logger(__name__)


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.connected = False
        self._connection_lock = False  # FIX: Prevent simultaneous reconnection attempts

    def _get_connection_parameters(self):
        try:
            config.refresh_cache()
            credentials = pika.PlainCredentials(config.rabbitmq_user, config.rabbitmq_password)
            parameters = pika.ConnectionParameters(
                host=config.rabbitmq_host,
                port=config.rabbitmq_port,
                credentials=credentials,
                heartbeat=600,  # FIX: Add heartbeat to detect dead connections
                blocked_connection_timeout=300,  # FIX: Timeout for blocked connections
                connection_attempts=3,  # FIX: Retry connection attempts
                retry_delay=5,  # FIX: Delay between retries
                socket_timeout=10  # FIX: Socket operation timeout
            )
            logger.info(
                f"Connecting to RabbitMQ at {config.rabbitmq_host}:{config.rabbitmq_port} as user {config.rabbitmq_user}")
            return parameters
        except Exception as e:
            logger.error(f"Error constructing RabbitMQ connection parameters: {e}")
            raise

    def connect(self):
        if self._connection_lock:
            logger.info("Connection attempt already in progress, waiting...")
            time.sleep(1)
            return self.connected

        self._connection_lock = True
        try:
            if self.connected and self.connection and not self.connection.is_closed:
                return True
            parameters = self._get_connection_parameters()
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.connection = pika.BlockingConnection(parameters)
                    self.channel = self.connection.channel()
                    self.channel.confirm_delivery()  # Enable delivery confirmations
                    self.channel.exchange_declare(
                        exchange='notification_events',
                        exchange_type='topic',
                        durable=True
                    )
                    queues = [
                        ('notification_queue', True),
                        ('product_events_queue', True),
                        ('user_events_queue', True)
                    ]
                    for queue_name, durable in queues:
                        self.channel.queue_declare(
                            queue=queue_name,
                            durable=durable,
                            arguments={
                                'x-message-ttl': 86400000  # 24 hours TTL
                            }
                        )
                    bindings = [
                        ('notification_events', 'notification_queue', 'user.*'),
                        ('notification_events', 'notification_queue', 'order.*'),
                        ('notification_events', 'notification_queue', 'payment.*'),
                        ('notification_events', 'product_events_queue', 'product.*'),
                        ('notification_events', 'user_events_queue', 'user.*')
                    ]

                    for exchange, queue, routing_key in bindings:
                        self.channel.queue_bind(
                            exchange=exchange,
                            queue=queue,
                            routing_key=routing_key
                        )

                    self.connected = True
                    logger.info("✅ Successfully connected to RabbitMQ")
                    return True

                except pika.exceptions.AMQPConnectionError as e:
                    logger.error(f"❌ RabbitMQ connection error (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        self.connected = False
                        return False
                except Exception as e:
                    logger.error(
                        f"❌ Unexpected error during RabbitMQ connection (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    else:
                        self.connected = False
                        return False

            return False

        finally:
            self._connection_lock = False

    def ensure_connection(self):
        try:
            if not self.connected or self.connection is None or self.connection.is_closed:
                logger.warning("RabbitMQ connection lost, attempting to reconnect...")
                return self.connect()
            try:
                self.channel.connection.process_data_events()
                return True
            except (pika.exceptions.ConnectionClosed, pika.exceptions.ChannelClosed):
                logger.warning("RabbitMQ channel/connection closed, reconnecting...")
                self.connected = False
                return self.connect()

        except Exception as e:
            logger.error(f"Error ensuring RabbitMQ connection: {e}")
            self.connected = False
            return False

    def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any]):
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    logger.error(
                        f"Attempt {attempt + 1}/{max_retries}: Cannot publish message - not connected to RabbitMQ")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    continue
                serializable_message = self._make_serializable(message)
                message_body = json.dumps(serializable_message)
                properties = pika.BasicProperties(
                    delivery_mode=2,  # Persistent message
                    content_type='application/json',
                    timestamp=int(time.time()),
                    message_id=str(uuid.uuid4()),  # FIX: Add unique message ID
                    app_id=config.app_name
                )
                self.channel.basic_publish(
                    exchange=exchange,
                    routing_key=routing_key,
                    body=message_body,
                    properties=properties,
                    mandatory=True  # FIX: Return undeliverable messages
                )
                logger.info(
                    f"📤 Message published to {exchange} with routing key {routing_key}, message_id: {properties.message_id}")
                return True

            except pika.exceptions.AMQPConnectionError as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: RabbitMQ connection error during publish: {e}")
                self.connected = False
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except pika.exceptions.UnroutableError as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Message could not be routed: {e}")
                return False
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries}: Failed to publish message to RabbitMQ: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        logger.error(f"Failed to publish message after {max_retries} attempts")
        return False

    def _make_serializable(self, obj: Any) -> Any:
        """Recursively make object JSON serializable"""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        else:
            return str(obj)

    def consume_messages(self, queue: str, callback: Callable, auto_ack: bool = False):
        try:
            if not self.ensure_connection():
                logger.error("Cannot consume messages - not connected to RabbitMQ")
                return

            def wrapped_callback(ch, method, properties, body):
                try:
                    message = json.loads(body.decode('utf-8'))
                    logger.info(
                        f"📥 Received message from queue {queue}, routing key: {method.routing_key}, message_id: {properties.message_id}")

                    # Process the message
                    callback(message)

                    # Acknowledge only after successful processing
                    if not auto_ack:
                        ch.basic_ack(delivery_tag=method.delivery_tag)

                    logger.info(f"✅ Message processed successfully: {method.routing_key}")

                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to decode JSON message: {e}")
                    if not auto_ack:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    if not auto_ack:
                        # FIX: Requeue message for retry
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            # FIX: Configure quality of service
            self.channel.basic_qos(prefetch_count=1)

            self.channel.basic_consume(
                queue=queue,
                on_message_callback=wrapped_callback,
                auto_ack=auto_ack
            )

            logger.info(f"🔄 Starting to consume messages from queue {queue}")
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
            self.connected = False
            raise

    def close(self):
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self.connected = False
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")


# FIX: Add missing import
import uuid
from datetime import datetime

rabbitmq_client = RabbitMQClient()