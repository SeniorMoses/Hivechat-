from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import SECRET_KEY, ALGORITHM
from database import get_db
from models import Message
from websocket import manager

import jwt


router = APIRouter()


async def authenticate_websocket(
    token: str,
) -> int:

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError()

        return int(user_id)

    except Exception:
        raise ValueError("Invalid token")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):

    token = websocket.query_params.get("token")

    if not token:
        await websocket.close(code=1008)
        return

    try:
        user_id = await authenticate_websocket(token)

    except ValueError:
        await websocket.close(code=1008)
        return

    await manager.connect(
        user_id,
        websocket,
    )

    try:

        # --------------------------------
        # Retrieve offline messages
        # --------------------------------

        result = await db.execute(
            select(Message)
            .where(
                Message.receiver_id == user_id,
                Message.delivered == False,
            )
            .order_by(Message.created_at)
        )

        pending_messages = result.scalars().all()

        for message in pending_messages:

            sent = await manager.send_to_user(
                user_id,
                {
                    "type": "message",
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "content": message.content,
                    "delivered": True,
                },
            )

            if sent:
                message.delivered = True

        await db.commit()

        # --------------------------------
        # Receive messages
        # --------------------------------

        while True:

            data = await websocket.receive_json()

            receiver_id = data.get("receiver_id")
            content = data.get("content")

            if not receiver_id or not content:
                await websocket.send_json({
                    "type": "error",
                    "message": "receiver_id and content are required",
                })
                continue

            content = content.strip()

            if not content:
                continue

            # --------------------------------
            # Store message FIRST
            # --------------------------------

            message = Message(
                sender_id=user_id,
                receiver_id=int(receiver_id),
                content=content,
                delivered=False,
                read=False,
            )

            db.add(message)

            await db.commit()
            await db.refresh(message)

            # --------------------------------
            # Try immediate delivery
            # --------------------------------

            delivered = await manager.send_to_user(
                int(receiver_id),
                {
                    "type": "message",
                    "id": message.id,
                    "sender_id": user_id,
                    "receiver_id": int(receiver_id),
                    "content": content,
                    "delivered": True,
                },
            )

            # --------------------------------
            # Update delivery status
            # --------------------------------

            if delivered:
                message.delivered = True

                await db.commit()

            # --------------------------------
            # Tell sender what happened
            # --------------------------------

            await websocket.send_json({
                "type": "message_sent",
                "id": message.id,
                "receiver_id": int(receiver_id),
                "content": content,
                "delivered": delivered,
            })

    except WebSocketDisconnect:

        manager.disconnect(user_id) 