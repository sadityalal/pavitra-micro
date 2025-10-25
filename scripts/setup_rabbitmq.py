#!/usr/bin/env python3
import pika
import os
import time
from shared.config import config

def setup_rabbitmq():
    print("Setting up RabbitMQ queues and exchanges...")
    
    # Wait for RabbitMQ to be ready
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            credentials = pika.PlainCredentials(config.rabbitmq_user, config.rabbitmq_password)
            parameters = pika.ConnectionParameters(
                host=config.rabbitmq_host,
                port=config.rabbitmq_port,
                credentials=credentials
            )
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            print("Connected to RabbitMQ successfully!")
            break
        except Exception as e:
            retry_count += 1
            print(f"Waiting for RabbitMQ... ({retry_count}/{max_retries})")
            time.sleep(2)
            if retry_count >= max_retries:
                print("Failed to connect to RabbitMQ after multiple attempts")
                return
    
    try:
        # Declare exchanges
        channel.exchange_declare(exchange='order_events', exchange_type='topic', durable=True)
        channel.exchange_declare(exchange='notification_events', exchange_type='topic', durable=True)
        channel.exchange_declare(exchange='payment_events', exchange_type='topic', durable=True)
        
        # Declare queues
        queues = [
            'order_created_queue',
            'order_updated_queue', 
            'notification_queue',
            'payment_queue',
            'email_queue',
            'sms_queue',
            'push_queue'
        ]
        
        for queue in queues:
            channel.queue_declare(queue=queue, durable=True)
        
        # Bind queues to exchanges
        channel.queue_bind(exchange='order_events', queue='order_created_queue', routing_key='order.created')
        channel.queue_bind(exchange='order_events', queue='order_updated_queue', routing_key='order.updated')
        channel.queue_bind(exchange='notification_events', queue='notification_queue', routing_key='notification.*')
        channel.queue_bind(exchange='payment_events', queue='payment_queue', routing_key='payment.*')
        channel.queue_bind(exchange='notification_events', queue='email_queue', routing_key='notification.email')
        channel.queue_bind(exchange='notification_events', queue='sms_queue', routing_key='notification.sms')
        channel.queue_bind(exchange='notification_events', queue='push_queue', routing_key='notification.push')
        
        print("RabbitMQ setup completed successfully!")
        
    except Exception as e:
        print(f"Error during RabbitMQ setup: {e}")
    finally:
        if connection and not connection.is_closed:
            connection.close()

if __name__ == "__main__":
    setup_rabbitmq()
