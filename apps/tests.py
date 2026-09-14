from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings

from apps.models import Ball, Student
from apps.routing import websocket_urlpatterns

application = URLRouter(websocket_urlpatterns)


@override_settings(
    CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
)
class StudentScoreConsumerTests(TransactionTestCase):
    async def connect(self):
        communicator = WebsocketCommunicator(application, "/ws/dashboard/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        return communicator

    async def test_init_sends_students_ordered_by_ball(self):
        low = await sync_to_async(Student.objects.create)(
            fullname="Low Scorer", photo="students/a.jpeg"
        )
        high = await sync_to_async(Student.objects.create)(
            fullname="High Scorer", photo="students/b.jpeg"
        )
        await sync_to_async(Ball.objects.create)(student=low, coin=5)
        await sync_to_async(Ball.objects.create)(student=high, coin=30)

        communicator = await self.connect()
        message = await communicator.receive_json_from()

        self.assertEqual(message["type"], "init")
        self.assertEqual(
            [(s["fullname"], s["ball"]) for s in message["students"]],
            [("High Scorer", 30), ("Low Scorer", 5)],
        )
        await communicator.disconnect()

    async def test_student_without_balls_gets_zero(self):
        await sync_to_async(Student.objects.create)(
            fullname="No Balls", photo="students/a.jpeg"
        )

        communicator = await self.connect()
        message = await communicator.receive_json_from()

        self.assertEqual(message["students"][0]["ball"], 0)
        await communicator.disconnect()

    async def test_saving_ball_broadcasts_new_total(self):
        student = await sync_to_async(Student.objects.create)(
            fullname="Alex", photo="students/a.jpeg"
        )
        await sync_to_async(Ball.objects.create)(student=student, coin=5)

        communicator = await self.connect()
        await communicator.receive_json_from()  # init

        await sync_to_async(Ball.objects.create)(student=student, coin=10)
        message = await communicator.receive_json_from()

        self.assertEqual(
            message,
            {"type": "ball_update", "student_id": student.id, "ball": 15},
        )
        await communicator.disconnect()

    async def test_deleting_ball_broadcasts_new_total(self):
        student = await sync_to_async(Student.objects.create)(
            fullname="Alex", photo="students/a.jpeg"
        )
        ball = await sync_to_async(Ball.objects.create)(student=student, coin=5)
        await sync_to_async(Ball.objects.create)(student=student, coin=10)

        communicator = await self.connect()
        await communicator.receive_json_from()  # init

        await sync_to_async(ball.delete)()
        message = await communicator.receive_json_from()

        self.assertEqual(message["ball"], 10)
        await communicator.disconnect()

    async def test_every_client_receives_the_update(self):
        student = await sync_to_async(Student.objects.create)(
            fullname="Alex", photo="students/a.jpeg"
        )

        first = await self.connect()
        second = await self.connect()
        await first.receive_json_from()
        await second.receive_json_from()

        await sync_to_async(Ball.objects.create)(student=student, coin=7)

        for communicator in (first, second):
            message = await communicator.receive_json_from()
            self.assertEqual(message["ball"], 7)
            await communicator.disconnect()
