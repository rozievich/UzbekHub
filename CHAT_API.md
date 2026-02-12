# Chat Application API Documentation

This documentation provides a comprehensive guide for the frontend team to integrate the Chat application features. It includes details on Authentication, REST API endpoints, and WebSocket real-time events.

## Base URL
`https://<your-domain>/api/` (adjust based on your actual Nginx/server config)

## Authentication
All API requests and WebSocket connections require a **JWT Access Token**.

### REST API
Include the token in the `Authorization` header:
```http
Authorization: Bearer <your_access_token>
```

### WebSockets
Include the token as a query parameter in the URL:
```
ws://<your-domain>/ws/chat/?token=<your_access_token>
```

---

## 1. Files API
Use this API to upload media (images, videos, voice notes, files) *before* sending a message.

### 1.1. Upload File
**Endpoint**: `POST /chat/files/`
**Content-Type**: `multipart/form-data`

**Request Body**:
| Field | Type | Required | Description |
|---|---|---|---|
| `file` | File | Yes | The file functionality to be uploaded. |
| `file_type` | String | No | `image`, `video`, `voice`, `document`, `other`. Default: `other`. |

**Response (201 Created)**:
```json
{
    "id": "e0847250-1234-5678-9012-345678901234",
    "file": "https://domain.com/media/chat_files/image.png",
    "file_type": "image",
    "file_size": 102400,
    "unique_id": "sha256_hash...",
    "uploaded_at": "2023-10-27T10:00:00Z"
}
```
> **Note**: Store the `id` from the response to use it in the `send_message` WebSocket event.

---

## 2. Chat Rooms API

### 2.1. List Rooms
Get a list of all chat rooms (Private and Group) the user is part of.

**Endpoint**: `GET /chat/rooms/`

**Response (200 OK)**:
```json
[
    {
        "id": "room_uuid",
        "room_type": "private", // or "group"
        "name": null, // Group name if group
        "username": null, // Group username if group
        "description": null,
        "profile_pic": null,
        "created_at": "...",
        "room_members": [
            {
                "id": 1,
                "user": 101, // user_id
                "role": "member",
                "joined_at": "..."
            }
        ]
    },
    ...
]
```

### 2.2. Create Room
Create a new private or group chat.

**Endpoint**: `POST /chat/rooms/`

**Request Body (Private)**:
```json
{
    "room_type": "private",
    "members": [102] // ID of the other user. (You don't need to send your own ID, backend adds it)
}
```

**Request Body (Group)**:
```json
{
    "room_type": "group",
    "username": "dev_team",
    "name": "Development Team",
    "description": "Official chat for devs",
    "members": [102, 103, 104] // IDs of initial members
}
```

**Response (201 Created)**: Returns the created room object (same structure as List Rooms).

### 2.3. Get Room Details
**Endpoint**: `GET /chat/rooms/{id}/`

### 2.4. Update Room (Group Only)
**Endpoint**: `PATCH /chat/rooms/{id}/`
**Permissions**: Owner or Admin only.

**Request Body**:
```json
{
    "name": "New Group Name",
    "description": "Updated description",
    "profile_pic": (file)
}
```

### 2.5. Delete Room
**Endpoint**: `DELETE /chat/rooms/{id}/`
*   **Private**: Deletes the chat for both users.
*   **Group**: Only the **Owner** can delete the group.

### 2.6. Clear History
**Endpoint**: `DELETE /chat/rooms/{id}/clear_messages/`
**Permissions**: Owner or Admin only (for Groups).
Clears all messages in the room.

---

## 3. Options for Room Members (Group Only)

### 3.1. List Members
**Endpoint**: `GET /chat/members/{room_id}/members/`

### 3.2. Join Group
**Endpoint**: `POST /chat/members/{room_id}/join/`

### 3.3. Leave Group
**Endpoint**: `POST /chat/members/{room_id}/leave/`

### 3.4. Add Member
**Endpoint**: `POST /chat/members/{room_id}/add_member/`
**Body**: `{"user_id": 105}`
**Permissions**: Owner/Admin only.

### 3.5. Remove Member
**Endpoint**: `POST /chat/members/{room_id}/remove_member/`
**Body**: `{"user_id": 105}`
**Permissions**: Owner/Admin only.

### 3.6. Manage Roles (Owner Only)
*   **Promote to Admin**: `POST /chat/members/{room_id}/set_admin/` -> `{"user_id": 105}`
*   **Demote Admin**: `POST /chat/members/{room_id}/remove_admin/` -> `{"user_id": 105}`
*   **Transfer Ownership**: `POST /chat/members/{room_id}/transfer_owner/` -> `{"user_id": 105}`

---

## 4. Messages API (REST)
Mainly used for fetching history. Real-time messaging happens via WebSockets.

### 4.1. Get Message History
**Endpoint**: `GET /chat/message/room/{room_id}/`
**Pagination**: `?limit=20&offset=0`

**Response (200 OK)**:
```json
{
    "count": 142,
    "next": "...",
    "previous": null,
    "results": [
        {
            "id": "msg_uuid",
            "text": "Hello world",
            "sender": 101,
            "room": "room_uuid",
            "reply_to": null,
            "is_edited": false,
            "created_at": "...",
            "attachments": [ ... ], // Array of file objects
            "statuses": [ ... ], // Read/Delivered statuses
            "actions": [ ... ] // Reactions
        }
    ]
}
```

---

## 5. WebSocket API (Real-time)
**URL**: `ws://<domain>/ws/chat/?token=<token>`

### 5.1. Connection Workflow
1.  **Connect**: Establish WS connection.
2.  **Join Rooms**: Immediately send `join_rooms` event to subscribe to your chats.
    ```json
    {
      "type": "join_rooms",
      "rooms": ["room_uuid_1", "room_uuid_2"] // Send all known room IDs locally
    }
    ```
3.  **Receive Undelivered**: Server sends `undelivered_messages` if you missed any while offline.
4.  **Heartbeat**: Send `{"type": "ping"}` every ~30s.

### 5.2. Client -> Server Events

#### Send Message
```json
{
  "type": "message",
  "room_id": "room_uuid",
  "text": "Hello!",
  "reply_to": "parent_message_uuid", // Optional
  "file_id": "file_uuid_from_upload_api" // Optional
}
```

#### Edit Message
```json
{
  "type": "edit_message",
  "message_id": "message_uuid",
  "text": "Corrected text"
}
```

#### Delete Message
```json
{
  "type": "delete_message",
  "message_id": "message_uuid"
}
```

#### Mark as Read
```json
{
  "type": "read",
  "message_id": "message_uuid"
}
```

#### Reaction (Like/Emotion)
```json
{
  "type": "action",
  "message_id": "message_uuid",
  "value": "👍" // Any string/emoji
}
```

#### Typing Indicator
```json
{
  "type": "typing",
  "room_id": "room_uuid",
  "is_typing": true
}
```

### 5.3. Server -> Client Events

#### Message Received
```json
{
  "type": "message",
  "room_id": "...",
  "message_id": "...",
  "text": "...",
  "sender": "username",
  "reply_to": "...",
  "file_id": "...",
  "created_at": "..."
}
```

#### Message Edited
```json
{
  "type": "edit_message",
  "message_id": "...",
  "text": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

#### Message Deleted
```json
{
  "type": "delete_message",
  "message_id": "..."
}
```

#### Read Receipt Update
```json
{
  "type": "read",
  "message_id": "...",
  "user": "username",
  "read_at": "..."
}
```

#### Reaction Update
```json
{
  "type": "action",
  "message_id": "...",
  "value": "👍",
  "user": 101,
  "created_at": "..."
}
```

#### Typing Indicator
```json
{
  "type": "typing",
  "user": 101,
  "is_typing": true
}
```
