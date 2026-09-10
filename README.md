## 1. Install

```bash
pip uninstall redis
pip install "redis<8.0"
pip install channels channels-redis daphne
```

## 2. settings.py

```python
INSTALLED_APPS = [
    "daphne",  # must be above django.contrib.staticfiles
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    # your apps
]

ASGI_APPLICATION = "myproject.asgi.application"

CHANNEL_LAYERS = {
    # "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}

    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

## 3. asgi.py

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import myapp.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(myapp.routing.websocket_urlpatterns)
    ),
})
```

## 4. myapp/routing.py

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]
```

## 5. myapp/consumers.py

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "message": message},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"]}))
```

## 6. Run

```bash
daphne myproject.asgi:application -b HOST -p PORT
```

(runserver ham ASGI bilan ishlaydi, lekin prod uchun daphne yoki uvicorn tavsiya qilinadi)

## 7. Frontend  (plain JS)

```jsx
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<title>WebSocket Chat</title>
<style>
    body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 0 15px; }
    #chat-log {
        border: 1px solid #ccc; border-radius: 8px; height: 350px;
        overflow-y: auto; padding: 10px; margin-bottom: 10px; background: #fafafa;
    }
    #chat-log div { margin-bottom: 6px; padding: 6px 10px; border-radius: 6px; background: #e8f0fe; }
    .form-row { display: flex; gap: 8px; }
    #chat-message-input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
    #chat-message-submit { padding: 8px 16px; border: none; border-radius: 6px; background: #1a73e8; color: #fff; cursor: pointer; }
    #chat-message-submit:hover { background: #155cb0; }
    #chat-message-submit:disabled, #join-btn:disabled { background: #aaa; cursor: not-allowed; }
    #status { font-size: 13px; color: #666; margin-bottom: 8px; }
    #room-row { display: flex; gap: 8px; margin-bottom: 15px; }
    #room-name-input { flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 6px; }
    #join-btn { padding: 8px 16px; border: none; border-radius: 6px; background: #34a853; color: #fff; cursor: pointer; }
    #join-btn:hover { background: #2c8c46; }
</style>
</head>
<body>

<h2>WebSocket Chat</h2>

<div id="room-row">
    <input id="room-name-input" type="text" placeholder="Xona nomini kiriting (masalan: p39)" autocomplete="off">
    <button id="join-btn">Kirish</button>
</div>

<div id="status">Xonaga kirish uchun nom yozing va "Kirish" tugmasini bosing</div>
<div id="chat-log"></div>

<div class="form-row">
    <input id="chat-message-input" type="text" placeholder="Xabar yozing..." autocomplete="off" disabled>
    <button id="chat-message-submit" disabled>Yuborish</button>
</div>

<script>
    let chatSocket = null;

    const statusEl = document.getElementById('status');
    const chatLog = document.getElementById('chat-log');
    const roomInput = document.getElementById('room-name-input');
    const joinBtn = document.getElementById('join-btn');
    const input = document.getElementById('chat-message-input');
    const button = document.getElementById('chat-message-submit');

    function setChatEnabled(enabled) {
        input.disabled = !enabled;
        button.disabled = !enabled;
    }

    function connectToRoom(roomName) {
        // Avvalgi ulanish bo'lsa, uzib qo'yamiz
        if (chatSocket) {
            chatSocket.close();
        }

        chatLog.innerHTML = '';
        setChatEnabled(false);
        statusEl.innerText = "Ulanmoqda: " + roomName + " ...";

        chatSocket = new WebSocket(
            'ws://10.40.10.61:8000/ws/chat/' + roomName + '/'
        );

        chatSocket.onopen = function(e) {
            statusEl.innerText = "Ulandi ✅ (xona: " + roomName + ")";
            setChatEnabled(true);
        };

        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            const msgDiv = document.createElement('div');
            msgDiv.textContent = data.message;
            chatLog.appendChild(msgDiv);
            chatLog.scrollTop = chatLog.scrollHeight;
        };

        chatSocket.onclose = function(e) {
            statusEl.innerText = "Ulanish uzildi ❌";
            setChatEnabled(false);
        };

        chatSocket.onerror = function(e) {
            statusEl.innerText = "Xatolik yuz berdi ⚠️";
        };
    }

    function joinRoom() {
        // Faqat \w+ (harf, raqam, pastki chiziq) ga ruxsat beramiz - regex bilan mos kelishi uchun
        const roomName = roomInput.value.trim();
        if (!/^\w+$/.test(roomName)) {
            alert("Xona nomi faqat harflar, raqamlar va pastki chiziqdan (_) iborat bo'lishi kerak!");
            return;
        }
        connectToRoom(roomName);
    }

    joinBtn.onclick = joinRoom;
    roomInput.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            joinRoom();
        }
    });

    function sendMessage() {
        const message = input.value.trim();
        if (message === '' || !chatSocket || chatSocket.readyState !== WebSocket.OPEN) return;
        chatSocket.send(JSON.stringify({
            'message': message
        }));
        input.value = '';
    }

    button.onclick = sendMessage;
    input.addEventListener('keyup', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
</script>

</body>
</html>
```

---