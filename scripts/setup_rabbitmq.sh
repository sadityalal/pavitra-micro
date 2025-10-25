#!/bin/bash

# RabbitMQ connection details from environment or defaults
RABBITMQ_HOST=${RABBITMQ_HOST:-localhost}
RABBITMQ_PORT=${RABBITMQ_PORT:-5672}
RABBITMQ_USER=${RABBITMQ_USER:-admin}
RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD:-admin123}

echo "Setting up RabbitMQ queues and exchanges..."

# Wait for RabbitMQ to be ready
echo "Waiting for RabbitMQ to be ready..."
until nc -z $RABBITMQ_HOST $RABBITMQ_PORT; do
    sleep 2
done

# Create exchanges and queues using rabbitmqadmin (comes with RabbitMQ management plugin)
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare exchange name=order_events type=topic durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare exchange name=notification_events type=topic durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare exchange name=payment_events type=topic durable=true

# Create queues
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=order_created_queue durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=order_updated_queue durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=notification_queue durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=payment_queue durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=email_queue durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=sms_queue durable=true
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare queue name=push_queue durable=true

# Bind queues to exchanges
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=order_events destination=order_created_queue routing_key=order.created
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=order_events destination=order_updated_queue routing_key=order.updated
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=notification_events destination=notification_queue routing_key=notification.*
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=payment_events destination=payment_queue routing_key=payment.*
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=notification_events destination=email_queue routing_key=notification.email
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=notification_events destination=sms_queue routing_key=notification.sms
rabbitmqadmin -H $RABBITMQ_HOST -u $RABBITMQ_USER -p $RABBITMQ_password declare binding source=notification_events destination=push_queue routing_key=notification.push

echo "RabbitMQ setup completed!"
