import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Sum

from apps.models import Student
from apps.serializers import StudentSerializer

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
#         self.room_group_name = f"chat_{self.room_name}"
#
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)
#         await self.accept()
#
#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
#
#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             message = data["message"]
#         except (json.JSONDecodeError, KeyError):
#             await self.send(text_data=json.dumps({"error": "Invalid message format"}))
#             return
#
#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {"type": "chat_message", "message": message},
#         )
#
#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({"message": event["message"]}))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "notifications"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # This method name must match the "type" sent from the signal
    async def notify_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
        }))



class StudentScoreConsumer(AsyncWebsocketConsumer):
    group_name = "dashboard"

    async def connect(self):
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        students = await self.get_students()
        await self.send(text_data=json.dumps({
            "type": "init",
            "students": students,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Called by the channel layer for {"type": "ball.update", ...}
    async def ball_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "ball_update",
            "student_id": event["student_id"],
            "ball": event["ball"],
        }))

    @sync_to_async
    def get_students(self):
        qs = Student.objects.annotate(
            ball=Sum("balls__coin", default=0)
        ).order_by("-ball", "id")
        return StudentSerializer(qs, many=True).data
