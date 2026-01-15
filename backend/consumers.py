import json
from channels.generic.websocket import AsyncWebsocketConsumer


class WebSocket(AsyncWebsocketConsumer):
    async def connect(self):
        # user = self.scope["user"]
        # self.group_name = f"user_{user.id}"
        self.all_users = "all_users"
        # if user.is_authenticated:
        #     self.user = user
        # else:
        #     await self.close()
            
        # await self.channel_layer.group_add(
        #     self.group_name,
        #     self.channel_name
        # )
        await self.channel_layer.group_add(
            self.all_users,
            self.channel_name
        )                    
        await self.accept()

    async def disconnect(self, close_code):
        # await self.channel_layer.group_discard(
        #     self.group_name,
        #     self.channel_name
        # )
        await self.channel_layer.group_discard(
            self.all_users,
            self.channel_name
        )        

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['text']
        if text_data_json == "ping":
            await self.send(text_data=json.dumps({
                'message': "pong"
            })) 
        # await self.channel_layer.group_send(
        #     self.group_name,
        #     {
        #     'type': 'send_message',
        #     'message': message
        #     }
        # )
        
        await self.channel_layer.group_send(
            self.all_users,
            {
            'type': 'send_message',
            'message': message
            }
        )        
        
    async def send_message(self, event):
        message = event['message']
        # logger.info(f"Sending message to user_{self.user.id}")
        # logger.info(f"message: {message}")
        await self.send(text_data=json.dumps({
            'message': message
        }))