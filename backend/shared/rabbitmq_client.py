import pika
import json
import logging
from typing import Any, Dict, Callable
from .config import config

logger = logging.getLogger(__name__)

class RabbitMQClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RabbitMQClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.connection = None
        self.channel = None
        self.connected = False
        self._connect()

    def _connect(self):
        try:
            # --- Build AMQP URL dynamically ---
            amqp_url = (
                f"amqp://{config.rabbitmq_user}:{config.rabbitmq_password}"
                f"@{config.rabbitmq_host}:{config.rabbitmq_port}/"
            )
            logger.info(f"🐇 AMQP URL used: {amqp_url}")
            parameters = pika.URLParameters(amqp_url)
            parameters.heartbeat = 600
            parameters.blocked_connection_timeout = 300

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # --- Declare exchanges ---
            for exchange in ["order_events", "notification_events", "payment_events"]:
                self.channel.exchange_declare(
                    exchange=exchange,
                    exchange_type="topic",
                    durable=True
                )

            # --- Declare queues and bind them ---
            queues = [
                ("order_created_queue", "order_events", "order.created"),
                ("order_updated_queue", "order_events", "order.updated"),
                ("notification_queue", "notification_events", "notification.*"),
                ("payment_queue", "payment_events", "payment.*"),
                ("email_queue", "notification_events", "notification.email"),
                ("sms_queue", "notification_events", "notification.sms"),
                ("push_queue", "notification_events", "notification.push"),
            ]

            for queue_name, exchange, routing_key in queues:
                self.channel.queue_declare(queue=queue_name, durable=True)
                self.channel.queue_bind(
                    exchange=exchange,
                    queue=queue_name,
                    routing_key=routing_key
                )

            self.connected = True
            logger.info(f"✅ RabbitMQ connected using {amqp_url}")

        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            self.connected = False

    def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any]):
        if not self.connected:
            self._connect()
            if not self.connected:
                logger.error("Cannot publish message - RabbitMQ not connected")
                return False

        try:
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # persistent
            )
            logger.info(f"📤 Published to {exchange} ({routing_key}): {message}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to publish message: {e}")
            self.connected = False
            return False

    def consume_messages(self, queue_name: str, callback: Callable):
        if not self.connected:
            self._connect()
            if not self.connected:
                logger.error("Cannot consume messages - RabbitMQ not connected")
                return

        try:
            def wrapped_callback(ch, method, properties, body):
                try:
                    message = json.loads(body)
                    callback(message)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            self.channel.basic_consume(queue=queue_name, on_message_callback=wrapped_callback)
            logger.info(f"▶️ Consuming messages from {queue_name}")
            self.channel.start_consuming()

        except Exception as e:
            logger.error(f"❌ Failed to consume messages: {e}")
            self.connected = False

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            self.connected = False
            logger.info("🔌 RabbitMQ connection closed")

# Singleton instance
rabbitmq_client = RabbitMQClient()
