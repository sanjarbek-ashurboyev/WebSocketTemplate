from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.consumers import StudentScoreConsumer
from apps.models import Category, Ball
from apps.serializers import CategorySerializer


@receiver(post_save, sender=Category)
def order_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    categories = Category.objects.all()
    data = CategorySerializer(instance=categories , many=True).data
    async_to_sync(channel_layer.group_send)(
        "notifications",
        {
            "type": "notify_message",  # -> maps to notify_message() in consumer
            "message": data,
        },
    )


@receiver(post_save, sender=Ball)
@receiver(post_delete, sender=Ball)
def ball_changed(sender, instance, **kwargs):
    total = Ball.objects.filter(student_id=instance.student_id).aggregate(
        total=Sum("coin", default=0)
    )["total"]

    async_to_sync(get_channel_layer().group_send)(
        StudentScoreConsumer.group_name,
        {
            "type": "ball.update",
            "student_id": instance.student_id,
            "ball": total,
        },
    )
