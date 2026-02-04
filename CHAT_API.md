# Chat Application API Documentation

This document provides a comprehensive guide for the frontend team to integrate the Chat application features, including REST API endpoints and WebSocket events.

## 1. Authentication

### REST API
All REST endpoints require a valid JWT token in the header.
```http
Authorization: Bearer <access_token>
```

### WebSockets
The WebSocket connection requires the token as a query parameter.
```
ws://<domain>/ws/chat/?token=<access_token>
```

---

## 2. REST API Endpoints

### 2.1. Chat Rooms (`/chat/rooms/`)

- **GET `/chat/rooms/`**: List all rooms the current user is a member of.
- **POST `/chat/rooms/`**: Create a new chat room.
    - **Private Room**:
      ```json
      {
        "room_type": "private",
        "members": [user_id_1, user_id_2]
      }
      ```
      *Note: Exactly 2 members required.*
    - **Group Room**:
      ```json
      {
        "room_type": "group",
        "username": "group_username",
        "name": "Group Name",
        "description": "Optional description",
        "members": [user_id_1, user_id_2, ...]
      }
      ```
- **GET `/chat/rooms/{uuid}/`**: Retrieve room details.
- **PATCH/PUT `/chat/rooms/{uuid}/`**: Update room details (Group only, Admin/Owner only).
- **DELETE `/chat/rooms/{uuid}/`**: Delete a room (Group Owner only, or any member for Private).
- **DELETE `/chat/rooms/{uuid}/clear_messages/`**: Clear all messages in the room (Group Admin/Owner only).

### 2.2. Room Members (`/chat/members/`)

- **GET `/chat/members/{room_id}/members/`**: List all members of a specific room.
- **POST `/chat/members/{room_id}/join/`**: Join a group chat.
- **POST `/chat/members/{room_id}/leave/`**: Leave a group chat.
- **POST `/chat/members/{room_id}/add_member/`**: Add a user to the group.
    - Body: `{"user_id": "uuid"}`
- **POST `/chat/members/{room_id}/remove_member/`**: Remove a user from the group.
    - Body: `{"user_id": "uuid"}`
- **POST `/chat/members/{room_id}/set_admin/`**: Promote a member to Admin.
    - Body: `{"user_id": "uuid"}`
- **POST `/chat/members/{room_id}/remove_admin/`**: Demote an Admin to Member.
    - Body: `{"user_id": "uuid"}`
- **POST `/chat/members/{room_id}/transfer_owner/`**: Transfer room ownership to another member.
    - Body: `{"user_id": "uuid"}`

### 2.3. Messages (`/chat/message/`)

- **GET `/chat/message/`**: List messages. Supports pagination and filtering.
    - Query Params: `?room_id={uuid}`
- **GET `/chat/message/room/{room_id}/`**: Get all messages for a specific room.

### 2.4. Files (`/chat/files/`)

- **GET `/chat/files/`**: List files owned by the user.
- **POST `/chat/files/`**: Upload a file (MultiPart Form).
    - Fields: `file` (File), `file_type` (image/video/voice/document/other).
    - Returns: `{"id": "file_uuid", ...}`. Use this ID when sending a message via WebSocket.

---

## 3. WebSocket API

### 3.1. Connection & Initial Setup
1. Connect to `ws://<domain>/ws/chat/?token=<token>`.
2. Send `join_rooms` to start receiving messages for your rooms.
   ```json
   {
     "type": "join_rooms",
     "rooms": ["room_uuid_1", "room_uuid_2"]
   }
   ```
3. The server will respond with:
   ```json
   {
     "action": "join_rooms",
     "status": "ok",
     "joined_rooms": ["room_uuid_1", "room_uuid_2"]
   }
   ```
   Followed by up to 100 **undelivered messages** (messages sent while you were offline).

### 3.2. Heartbeat
Send a ping every ~30-50 seconds to keep the connection alive and remain "Online".
- **Client sends**: `{"type": "ping"}`
- **Server responds**: `{"type": "pong"}`

### 3.3. Sending Events

#### Send Message
```json
{
  "type": "message",
  "room_id": "uuid",
  "text": "Hello world",
  "reply_to": "message_uuid",
  "file_id": "file_uuid"
}
```

#### Edit Message
```json
{
  "type": "edit_message",
  "message_id": "uuid",
  "text": "Updated text"
}
```

#### Delete Message
```json
{
  "type": "delete_message",
  "message_id": "uuid"
}
```

#### Mark as Read
```json
{
  "type": "read",
  "message_id": "uuid"
}
```

#### Add Reaction/Action
```json
{
  "type": "action",
  "message_id": "uuid",
  "value": "❤️"
}
```

#### Typing Indicator
```json
{
  "type": "typing",
  "room_id": "uuid",
  "is_typing": true
}
```

### 3.4. Receiving Events (Server -> Client)

#### New Message
```json
{
  "type": "message",
  "room_id": "uuid",
  "message_id": "uuid",
  "text": "...",
  "sender": "username",
  "reply_to": "uuid/null",
  "file_id": "uuid/null",
  "created_at": "ISO-Timestamp"
}
```

#### Message Edited
```json
{
  "type": "edit_message",
  "message_id": "uuid",
  "text": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

#### Message Deleted
```json
{
  "type": "delete_message",
  "message_id": "uuid"
}
```

#### Message Read
```json
{
  "type": "read",
  "message_id": "uuid",
  "user": "username",
  "read_at": "..."
}
```

#### Reaction/Action Added
```json
{
  "type": "action",
  "message_id": "uuid",
  "value": "...",
  "user": "user_id",
  "created_at": "..."
}
```

#### Typing Indicator
```json
{
  "type": "typing",
  "user": "user_id",
  "is_typing": true/false
}
```

#### Room Cleared
```json
{
  "type": "cleared",
  "room_id": "uuid",
  "cleared_by": "user_id"
}
```

#### Room Deleted
```json
{
  "type": "chat_deleted",
  "room_id": "uuid",
  "deleted_by": "user_id"
}
```
