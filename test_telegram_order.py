import pika
import json

test_message = {
    'event_type': 'order_created',
    'data': {
        'id': 1002,
        'user_id': 1,  # Admin user ID
        'order_number': 'ORDER-TELEGRAM-TEST',
        'total_amount': 1999.00,
        'item_count': 2,
        'created_at': '2024-01-15 18:00:00'
    }
}

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    channel.basic_publish(
        exchange='',
        routing_key='notification_queue',
        body=json.dumps(test_message),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    
    print("✅ Test order message sent to RabbitMQ")
    print("This should trigger Telegram notification to @saurabh_aditya")
    connection.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
