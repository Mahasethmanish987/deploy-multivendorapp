
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import models

from .models import OrderedFood


class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.room_group_name = f"order_{self.order_id}"

        # Authorization check
        if await self.validate_access():
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # async def receive(self, text_data):
    #     data = json.loads(text_data)
    #     action = data.get("action")

    #     if action == "update_status":
    #         food_item_id = data["food_item_id"]
    #         new_status = data["status"]
    #         if await self.update_food_status(food_item_id, new_status):
    #             await self.channel_layer.group_send(
    #                 self.room_group_name,
    #                 {
    #                     "type": "order_update",
    #                     "food_item_id": food_item_id,
    #                     "status": new_status,
    #                     "sender": self.scope["user"].id,
    #                 },
    #             )

    async def order_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def validate_access(self):
        order = (
            OrderedFood.objects.filter(
                id=self.order_id,
            )
            .filter(
                models.Q(user=self.scope["user"])
                | models.Q(fooditem__vendor__user=self.scope["user"])
            )
            .first()
        )
        return order is not None

    # @database_sync_to_async
    # def update_food_status(self, food_item_id, status):
    #     try:
    #         food = OrderedFood.objects.get(id=food_item_id)
    #         food.status = status
    #         food.save()
    #         return True
    #     except OrderedFood.DoesNotExist:
    #         return False
