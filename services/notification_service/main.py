import json
import logging

import pika
from fastapi import BackgroundTasks

from shared.app_factory import create_app
from shared.config import get_settings


logger = logging.getLogger("notification-service")
settings = get_settings()
app = create_app("notification-service")


def process_message(body: bytes) -> None:
	try:
		event = json.loads(body.decode("utf-8"))
	except Exception as exc:
		logger.error("Invalid event payload: %s", exc)
		return

	event_type = event.get("event_type", "Unknown")
	payload = event.get("payload", {})
	logger.info("Notification event=%s payload=%s", event_type, payload)


def consume_once() -> int:
	try:
		connection = pika.BlockingConnection(
			pika.ConnectionParameters(host=settings.rabbitmq_host, port=settings.rabbitmq_port)
		)
		channel = connection.channel()
		channel.queue_declare(queue=settings.rabbitmq_queue, durable=False)
		method_frame, _, body = channel.basic_get(queue=settings.rabbitmq_queue, auto_ack=False)
		if method_frame:
			process_message(body)
			channel.basic_ack(method_frame.delivery_tag)
			connection.close()
			return 1
		connection.close()
		return 0
	except Exception as exc:  # pragma: no cover - infrastructure dependent
		logger.error("RabbitMQ consume failed: %s", exc)
		return 0


@app.post("/notifications/poll")
def poll_notifications(background_tasks: BackgroundTasks) -> dict[str, str]:
	background_tasks.add_task(consume_once)
	return {"status": "accepted"}


@app.get("/notifications/poll-now")
def poll_now() -> dict[str, int]:
	return {"processed": consume_once()}

