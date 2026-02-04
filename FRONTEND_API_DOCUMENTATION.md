# UzbekHub API Documentation

> **Base URL**: `/api/`
> 
> **API Version**: v1.0

## Table of Contents

1. [Authentication](#authentication)
2. [Accounts API](#accounts-api)
3. [Posts API](#posts-api)
4. [Stories API](#stories-api)
5. [Chat API](#chat-api)
6. [Notifications API](#notifications-api)

---

## Authentication

UzbekHub uses **JWT (JSON Web Token)** authentication. Most endpoints require authentication.

### Authentication Header
```
Authorization: Bearer <access_token>
```

### Token Structure
After successful login, you'll receive:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## Accounts API

Base path: `/api/accounts/`

### Authentication Endpoints

#### 1. Sign Up
**POST** `/api/accounts/auth/signup/`

Ro'yxatdan o'tish jarayonini boshlaydi. Email ga tasdiqlash kodi yuboriladi.

- **Authentication**: ❌ Not required
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "confirm_password": "securePassword123"
}
```

- **Response** (201 Created):
```json
{
  "status": true,
  "user": "user@example.com"
}
```

- **Validation**:
  - Email must be unique and valid
  - Password minimum 8 characters
  - Passwords must match

---

#### 2. Email Verification
**POST** `/api/accounts/auth/email-verify/`

Email ga yuborilgan kodni tasdiqlash.

- **Authentication**: ❌ Not required
- **Throttling**: ✅ Rate limited (email_verify scope)
- **Request Body**:
```json
{
  "code": "12345"
}
```

- **Response** (200 OK):
```json
{
  "message": "User is successfully activated"
}
```

---

#### 3. Sign In
**POST** `/api/accounts/auth/signin/`

Tizimga kirish.

- **Authentication**: ❌ Not required
- **Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

- **Response** (200 OK):
```json
{
  "status": true,
  "email": "user@example.com",
  "token": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

#### 4. Google OAuth Login
**POST** `/api/accounts/auth/oauth2/google/`

Google orqali tizimga kirish.

- **Authentication**: ❌ Not required
- **Request Body**:
```json
{
  "token": "google_oauth_token_here"
}
```

- **Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

#### 5. Forgot Password
**POST** `/api/accounts/auth/forgot-password/`

Parolni tiklash uchun email ga link yuborish.

- **Authentication**: ❌ Not required
- **Throttling**: ✅ Rate limited (forget_password scope)
- **Request Body**:
```json
{
  "email": "user@example.com"
}
```

- **Response** (200 OK):
```json
{
  "message": "Password reset link has been sent to your email"
}
```

---

#### 6. Reset Password
**POST** `/api/accounts/auth/reset-password/<reset_link>/`

Yangi parol o'rnatish.

- **Authentication**: ❌ Not required
- **Throttling**: ✅ Rate limited (new_password scope)
- **URL Parameters**:
  - `reset_link` (string): Email orqali kelgan reset link
  
- **Request Body**:
```json
{
  "new_password": "newSecurePassword123",
  "confirm_password": "newSecurePassword123"
}
```

- **Response** (200 OK):
```json
{
  "message": "Your password has been successfully updated"
}
```

---

### Profile Management

#### 7. Get My Profile
**GET** `/api/accounts/account/profile/`

O'z profilini ko'rish.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "user@example.com",
  "username": "johndoe",
  "bio": "Software developer",
  "profile_picture": "http://example.com/media/profile_pictures/image.jpg",
  "phone": "+998901234567",
  "is_private": false,
  "is_active": true,
  "is_staff": false,
  "date_joined": "2024-01-01T10:00:00Z",
  "last_login": "2024-02-04T10:00:00Z",
  "last_online": "2024-02-04T11:00:00Z",
  "location": {
    "id": 1,
    "lat": "41.2995",
    "long": "69.2401",
    "country": "Uzbekistan",
    "city": "Tashkent",
    "county": "Yunusabad",
    "neighbourhood": "Chilonzor",
    "created_at": "2024-01-01T10:00:00Z",
    "update_at": "2024-02-04T10:00:00Z"
  },
  "status": {
    "id": 1,
    "content": "Busy working",
    "created_at": "2024-02-04T09:00:00Z",
    "updated_at": "2024-02-04T09:00:00Z"
  }
}
```

---

#### 8. Update My Profile
**PATCH** `/api/accounts/account/profile/`

Profilni yangilash.

- **Authentication**: ✅ Required
- **Content-Type**: `multipart/form-data`
- **Request Body** (all fields optional):
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "bio": "Software developer",
  "profile_picture": "<file>",
  "phone": "+998901234567",
  "is_private": false,
  "password": "newPassword123"
}
```

- **Response** (200 OK): Same as Get My Profile

---

#### 9. Check Username Availability
**GET** `/api/accounts/account/check/username/`

Username mavjudligini tekshirish.

- **Authentication**: ✅ Required
- **Query Parameters**:
  - `username` (string, required): Tekshiriladigan username
  
- **Example**: `/api/accounts/account/check/username/?username=johndoe`

- **Response** (200 OK):
```json
{
  "available": false
}
```

---

#### 10. Change Email - Request
**POST** `/api/accounts/account/change-email/`

Email o'zgartirish jarayonini boshlash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "new_email": "newemail@example.com",
  "password": "currentPassword123"
}
```

- **Response** (200 OK):
```json
{
  "message": "A verification code has been sent to your new email address to update your email."
}
```

---

#### 11. Change Email - Confirm
**POST** `/api/accounts/account/change-email/confirm/`

Email o'zgartirishni tasdiqlash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "code": "12345"
}
```

- **Response** (200 OK):
```json
{
  "message": "Email successfully updated"
}
```

---

#### 12. Delete Account - Request
**POST** `/api/accounts/account/delete/`

Akkauntni o'chirish jarayonini boshlash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "password": "currentPassword123"
}
```

- **Response** (200 OK):
```json
{
  "message": "Verification code sent to email"
}
```

---

#### 13. Delete Account - Confirm
**POST** `/api/accounts/account/delete/confirm/`

Akkauntni o'chirishni tasdiqlash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "code": "12345"
}
```

- **Response** (204 No Content)

---

### User Search & Discovery

#### 14. Search Users
**GET** `/api/accounts/account/search/<key>/`

Username, ism yoki familiya bo'yicha qidirish.

- **Authentication**: ✅ Required
- **Throttling**: ✅ Rate limited (profile_search scope)
- **URL Parameters**:
  - `key` (string): Qidiruv kaliti
  
- **Example**: `/api/accounts/account/search/john/`

- **Response** (200 OK):
```json
[
  {
    "id": 2,
    "first_name": "John",
    "last_name": "Smith",
    "username": "johnsmith",
    "bio": "Developer",
    "profile_picture": "http://example.com/media/profile_pictures/image.jpg",
    "phone": "+998901234567",
    "is_private": false,
    "is_active": true,
    "is_staff": false,
    "date_joined": "2024-01-01T10:00:00Z",
    "last_login": "2024-02-04T10:00:00Z",
    "last_online": "2024-02-04T11:00:00Z"
  }
]
```

> **Note**: Bloklagan foydalanuvchilar natijada ko'rinmaydi.

---

#### 15. Get User Profile by ID
**GET** `/api/accounts/account/user/<pk>/`

Foydalanuvchi profilini ID bo'yicha ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): User ID
  
- **Example**: `/api/accounts/account/user/2/`

- **Response** (200 OK): Same structure as Search Users response

---

#### 16. Get Public Profile by Username
**GET** `/api/accounts/account/profile/<username>/`

Username bo'yicha ochiq profilni ko'rish.

- **Authentication**: ❌ Not required
- **Throttling**: ✅ Rate limited (public_profile scope)
- **URL Parameters**:
  - `username` (string): Foydalanuvchi username
  
- **Example**: `/api/accounts/account/profile/johndoe/`

- **Response** (200 OK):
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "bio": "Software developer",
  "profile_picture": "http://example.com/media/profile_pictures/image.jpg",
  "is_private": false,
  "date_joined": "2024-01-01T10:00:00Z"
}
```

---

### Location Management

#### 17. Create Location
**POST** `/api/accounts/account/location/`

Joylashuvni qo'shish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "lat": "41.2995",
  "long": "69.2401"
}
```

- **Response** (201 Created):
```json
{
  "id": 1,
  "owner": 1,
  "lat": "41.2995",
  "long": "69.2401",
  "country": "Uzbekistan",
  "city": "Tashkent",
  "county": "Yunusabad",
  "neighbourhood": "Chilonzor",
  "created_at": "2024-02-04T10:00:00Z",
  "update_at": "2024-02-04T10:00:00Z"
}
```

> **Note**: Manzil avtomatik ravishda koordinatalar asosida aniqlanadi.

---

#### 18. Update Location
**PUT** `/api/accounts/account/location/`

Joylashuvni yangilash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "lat": "41.3111",
  "long": "69.2797"
}
```

- **Response** (200 OK): Same as Create Location

---

#### 19. Delete Location
**DELETE** `/api/accounts/account/location/`

Joylashuvni o'chirish.

- **Authentication**: ✅ Required
- **Response** (204 No Content)

---

#### 20. Search Users by Location
**GET** `/api/accounts/account/location/<distance>/`

Yaqin atrofdagi foydalanuvchilarni qidirish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `distance` (float): Masofa (km)
  
- **Example**: `/api/accounts/account/location/5.0/`

- **Response** (200 OK):
```json
[
  {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Doe",
    "username": "janedoe",
    "bio": "Designer",
    "profile_picture": "http://example.com/media/profile_pictures/image.jpg",
    "distance": 2.5
  }
]
```

---

### Block Management

#### 21. Get Blocked Users
**GET** `/api/accounts/account/block/`

Bloklangan foydalanuvchilar ro'yxati.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
[
  {
    "id": 1,
    "user": 1,
    "blocked_user": {
      "id": 3,
      "username": "blockeduser",
      "full_name": "Blocked User",
      "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
    },
    "created_at": "2024-02-04T10:00:00Z"
  }
]
```

---

#### 22. Block User
**POST** `/api/accounts/account/block/`

Foydalanuvchini bloklash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "blocked_user": 3
}
```

- **Response** (201 Created): Same as Get Blocked Users item

---

#### 23. Get Blocked User Detail
**GET** `/api/accounts/account/block/<pk>/`

Bloklangan foydalanuvchi ma'lumotlarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): Blocked user ID
  
- **Response** (200 OK): Same as Get Blocked Users item

---

#### 24. Unblock User
**DELETE** `/api/accounts/account/block/<pk>/`

Foydalanuvchini blokdan chiqarish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): Blocked user ID
  
- **Response** (204 No Content)

---

### Status Management

#### 25. Get My Status
**GET** `/api/accounts/account/status/`

O'z statusimni ko'rish.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
{
  "id": 1,
  "user": 1,
  "content": "Busy working",
  "created_at": "2024-02-04T09:00:00Z",
  "updated_at": "2024-02-04T09:00:00Z"
}
```

---

#### 26. Create Status
**POST** `/api/accounts/account/status/`

Status yaratish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "content": "Busy working"
}
```

- **Response** (201 Created): Same as Get My Status

- **Validation**:
  - Content max 55 characters

---

#### 27. Update Status
**PUT** `/api/accounts/account/status/`

Statusni yangilash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "content": "Available now"
}
```

- **Response** (200 OK): Same as Get My Status

---

#### 28. Delete Status
**DELETE** `/api/accounts/account/status/`

Statusni o'chirish.

- **Authentication**: ✅ Required
- **Response** (204 No Content)

---

### Contact Management

#### 29. Get Contacts
**GET** `/api/accounts/account/contact/`

Kontaktlar ro'yxati.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
[
  {
    "id": 1,
    "owner": 1,
    "contact": 2,
    "nikname": "Best Friend",
    "created_at": "2024-01-01T10:00:00Z",
    "update_at": "2024-02-04T10:00:00Z"
  }
]
```

---

#### 30. Add Contact
**POST** `/api/accounts/account/contact/`

Kontakt qo'shish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "contact": 2,
  "nikname": "Best Friend"
}
```

- **Response** (201 Created): Same as Get Contacts item

---

#### 31. Get Contact Detail
**GET** `/api/accounts/account/contact/<pk>/`

Kontakt ma'lumotlarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): Contact ID
  
- **Response** (200 OK): Same as Get Contacts item

---

#### 32. Update Contact (Full)
**PUT** `/api/accounts/account/contact/<pk>/`

Kontaktni to'liq yangilash.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): Contact ID
  
- **Request Body**:
```json
{
  "contact": 2,
  "nikname": "Updated Nickname"
}
```

- **Response** (200 OK): Same as Get Contacts item

---

#### 33. Update Contact (Partial)
**PATCH** `/api/accounts/account/contact/<pk>/`

Kontaktni qisman yangilash.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): Contact ID
  
- **Request Body**:
```json
{
  "nikname": "Updated Nickname"
}
```

- **Response** (200 OK): Same as Get Contacts item

---

#### 34. Delete Contact
**DELETE** `/api/accounts/account/contact/<pk>/`

Kontaktni o'chirish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `pk` (integer): Contact ID
  
- **Response** (204 No Content)

---

### Admin Endpoints

#### 35. Admin - List Users
**GET** `/api/accounts/admin/user/`

Barcha foydalanuvchilar ro'yxati (faqat adminlar uchun).

- **Authentication**: ✅ Required (Admin only)
- **Response** (200 OK): Array of user objects

---

#### 36. Admin - Get User
**GET** `/api/accounts/admin/user/<pk>/`

Foydalanuvchi ma'lumotlarini ko'rish (faqat adminlar uchun).

- **Authentication**: ✅ Required (Admin only)
- **URL Parameters**:
  - `pk` (integer): User ID

---

#### 37. Admin - Delete User
**DELETE** `/api/accounts/admin/user/<pk>/`

Foydalanuvchini o'chirish (faqat adminlar uchun).

- **Authentication**: ✅ Required (Admin only)
- **URL Parameters**:
  - `pk` (integer): User ID
  
- **Response** (204 No Content)

---

## Posts API

Base path: `/api/posts/`

### Post Management

#### 1. List Posts
**GET** `/api/posts/post/`

Barcha postlar ro'yxati.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
[
  {
    "id": "uuid-string",
    "content": "This is my first post!",
    "owner": {
      "id": 1,
      "username": "johndoe",
      "full_name": "John Doe",
      "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
    },
    "images": [
      {
        "id": "uuid-string",
        "image": "http://example.com/media/posts/images/image1.jpg",
        "created_at": "2024-02-04T10:00:00Z"
      }
    ],
    "is_active": true,
    "is_edited": false,
    "like_count": 15,
    "comment_count": 3,
    "view_count": 50,
    "created_at": "2024-02-04T10:00:00Z",
    "updated_at": null
  }
]
```

---

#### 2. Create Post
**POST** `/api/posts/post/`

Post yaratish.

- **Authentication**: ✅ Required
- **Content-Type**: `multipart/form-data`
- **Request Body**:
```json
{
  "content": "This is my new post!",
  "images": ["<file1>", "<file2>"]
}
```

- **Response** (201 Created): Same as List Posts item

> **Note**: `images` ixtiyoriy. Bir nechta rasm yuklash mumkin.

---

#### 3. Get Post Detail
**GET** `/api/posts/post/<id>/`

Post ma'lumotlarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `id` (string): Post UUID
  
- **Response** (200 OK): Same as List Posts item

---

#### 4. Update Post
**PATCH** `/api/posts/post/<id>/`

Postni yangilash.

- **Authentication**: ✅ Required (Owner only)
- **Content-Type**: `multipart/form-data`
- **URL Parameters**:
  - `id` (string): Post UUID
  
- **Request Body**:
```json
{
  "content": "Updated post content",
  "images": ["<new_file>"]
}
```

- **Response** (200 OK): Same as List Posts item

> **Note**: Yangilangandan keyin `is_edited` = `true` bo'ladi.

---

#### 5. Delete Post
**DELETE** `/api/posts/post/<id>/`

Postni o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (string): Post UUID
  
- **Response** (204 No Content)

---

### Post Likes

#### 6. Like Post
**POST** `/api/posts/like/`

Postga like bosish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "post": "post-uuid"
}
```

- **Response** (201 Created):
```json
{
  "id": "like-uuid",
  "owner": {
    "id": 1,
    "username": "johndoe",
    "full_name": "John Doe",
    "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
  },
  "post": "post-uuid",
  "created_at": "2024-02-04T10:00:00Z"
}
```

> **Validation**: Bir postga bir marta like bosish mumkin.

---

#### 7. Unlike Post
**DELETE** `/api/posts/like/<id>/`

Like ni bekor qilish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (string): Like UUID
  
- **Response** (204 No Content)

---

#### 8. Get Post Likes
**GET** `/api/posts/<post_id>/likes/`

Post likelarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `post_id` (string): Post UUID
  
- **Response** (200 OK):
```json
[
  {
    "id": "like-uuid",
    "owner": {
      "id": 1,
      "username": "johndoe",
      "full_name": "John Doe",
      "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
    },
    "post": "post-uuid",
    "created_at": "2024-02-04T10:00:00Z"
  }
]
```

---

### Post Comments

#### 9. Create Comment
**POST** `/api/posts/comment/`

Izoh qoldirish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "post": "post-uuid",
  "comment": "Great post!",
  "reply_to": null
}
```

- **Response** (201 Created):
```json
{
  "id": "comment-uuid",
  "owner": {
    "id": 1,
    "username": "johndoe",
    "full_name": "John Doe",
    "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
  },
  "post": "post-uuid",
  "comment": "Great post!",
  "reply_to": null,
  "is_edited": false,
  "created_at": "2024-02-04T10:00:00Z",
  "updated_at": null
}
```

> **Note**: `reply_to` - boshqa izohga javob berish uchun ishlatiladi (comment UUID).

---

#### 10. Update Comment
**PATCH** `/api/posts/comment/<id>/`

Izohni yangilash.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (string): Comment UUID
  
- **Request Body**:
```json
{
  "comment": "Updated comment text"
}
```

- **Response** (200 OK): Same as Create Comment

> **Note**: Yangilangandan keyin `is_edited` = `true` bo'ladi.

---

#### 11. Delete Comment
**DELETE** `/api/posts/comment/<id>/`

Izohni o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (string): Comment UUID
  
- **Response** (204 No Content)

---

#### 12. Get Post Comments
**GET** `/api/posts/<post_id>/comments/`

Post izohlarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `post_id` (string): Post UUID
  
- **Response** (200 OK): Array of comments (same structure as Create Comment)

---

### Post Views

#### 13. Record Post View
**POST** `/api/posts/views/`

Post ko'rilganligini qayd qilish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "post": "post-uuid"
}
```

- **Response** (201 Created):
```json
{
  "id": "view-uuid",
  "owner": {
    "id": 1,
    "username": "johndoe",
    "full_name": "John Doe",
    "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
  },
  "post": "post-uuid",
  "created_at": "2024-02-04T10:00:00Z"
}
```

> **Validation**: Bir postga bir marta view qayd qilinadi.

---

#### 14. Get Post Views
**GET** `/api/posts/<post_id>/views/`

Post ko'rishlar sonini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `post_id` (string): Post UUID
  
- **Response** (200 OK): Array of views (same structure as Record Post View)

---

## Stories API

Base path: `/api/stories/`

### Active Stories

#### 1. List My Active Stories
**GET** `/api/stories/active/`

O'z aktiv hikoyalarimni ko'rish.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
[
  {
    "id": 1,
    "owner": {
      "id": 1,
      "username": "johndoe",
      "full_name": "John Doe",
      "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
    },
    "media": "http://example.com/media/stories/story1.jpg",
    "caption": "Beautiful sunset!",
    "marked": [2, 3],
    "is_active": true,
    "audience": "public",
    "created_at": "2024-02-04T10:00:00Z",
    "updated_at": "2024-02-04T10:00:00Z"
  }
]
```

---

#### 2. Create Story
**POST** `/api/stories/active/`

Hikoya yaratish.

- **Authentication**: ✅ Required
- **Content-Type**: `multipart/form-data`
- **Request Body**:
```json
{
  "media": "<file>",
  "caption": "Beautiful sunset!",
  "audience": "public",
  "marked": [2, 3]
}
```

- **Response** (201 Created): Same as List My Active Stories item

- **Audience Options**:
  - `public` - Hamma ko'radi
  - `contact` - Faqat kontaktlar ko'radi
  - `marked` - Faqat belgilangan foydalanuvchilar ko'radi

---

#### 3. Get Story Detail
**GET** `/api/stories/active/<id>/`

Hikoya ma'lumotlarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `id` (integer): Story ID
  
- **Response** (200 OK): Same as List My Active Stories item

> **Note**: Audience qoidalariga ko'ra faqat ruxsat berilgan foydalanuvchilar ko'rishi mumkin.

---

#### 4. Update Story
**PATCH** `/api/stories/active/<id>/`

Hikoyani yangilash.

- **Authentication**: ✅ Required (Owner only)
- **Content-Type**: `multipart/form-data`
- **URL Parameters**:
  - `id` (integer): Story ID
  
- **Request Body**:
```json
{
  "caption": "Updated caption",
  "audience": "contact"
}
```

- **Response** (200 OK): Same as List My Active Stories item

---

#### 5. Delete Story
**DELETE** `/api/stories/active/<id>/`

Hikoyani o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (integer): Story ID
  
- **Response** (204 No Content)

---

#### 6. Get User Stories
**GET** `/api/stories/active/<user_id>/stories/`

Boshqa foydalanuvchi hikoyalarini ko'rish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `user_id` (integer): User ID
  
- **Response** (200 OK): Array of stories (same structure as List My Active Stories)

> **Note**: Faqat audience qoidalariga mos keladigan hikoyalar qaytariladi.

---

### Archive Stories

#### 7. List Archive Stories
**GET** `/api/stories/archive/`

Arxivlangan hikoyalar ro'yxati.

- **Authentication**: ✅ Required
- **Response** (200 OK): Array of stories (same structure as active stories but `is_active` = `false`)

---

#### 8. Get Archive Story Detail
**GET** `/api/stories/archive/<pk>/`

Arxivlangan hikoya ma'lumotlarini ko'rish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `pk` (integer): Story ID
  
- **Response** (200 OK): Same as archive story item

---

#### 9. Delete Archive Story
**DELETE** `/api/stories/archive/<pk>/`

Arxivlangan hikoyani butunlay o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `pk` (integer): Story ID
  
- **Response** (204 No Content)

---

### Story Reactions

#### 10. React to Story
**POST** `/api/stories/reaction/`

Hikoyaga reaktsiya qoldirish.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "story": 1,
  "reaction": "❤️"
}
```

- **Response** (201 Created):
```json
{
  "id": 1,
  "story": 1,
  "user": 1,
  "reaction": "❤️",
  "reacted_at": "2024-02-04T10:00:00Z"
}
```

> **Validation**: Bir hikoyaga bir marta reaktsiya qoldirish mumkin.

---

#### 11. Update Reaction
**PATCH** `/api/stories/reaction/<id>/`

Reaktsiyani o'zgartirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (integer): Reaction ID
  
- **Request Body**:
```json
{
  "reaction": "👍"
}
```

- **Response** (200 OK): Same as React to Story

---

#### 12. Delete Reaction
**DELETE** `/api/stories/reaction/<id>/`

Reaktsiyani o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (integer): Reaction ID
  
- **Response** (204 No Content)

---

### Story Views

#### 13. Mark Story as Viewed
**POST** `/api/stories/viewed/`

Hikoyani ko'rilgan deb belgilash.

- **Authentication**: ✅ Required
- **Request Body**:
```json
{
  "story": 1,
  "viewer": 1
}
```

- **Response** (201 Created):
```json
{
  "id": 1,
  "story": 1,
  "viewer": 1,
  "viewed_at": "2024-02-04T10:00:00Z"
}
```

---

## Chat API

Base path: `/api/chat/`

### Chat Rooms

#### 1. List Chat Rooms
**GET** `/api/chat/rooms/`

Barcha chat xonalar ro'yxati.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
[
  {
    "id": "uuid-string",
    "room_type": "private",
    "name": null,
    "username": null,
    "description": null,
    "profile_pic": null,
    "members": [
      {
        "id": 1,
        "username": "johndoe",
        "full_name": "John Doe",
        "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
      }
    ],
    "created_at": "2024-02-04T10:00:00Z"
  },
  {
    "id": "uuid-string",
    "room_type": "group",
    "name": "Project Team",
    "username": "project_team",
    "description": "Team discussion",
    "profile_pic": "http://example.com/media/room_pictures/image.jpg",
    "members": [
      {
        "id": 1,
        "username": "johndoe",
        "full_name": "John Doe",
        "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
      },
      {
        "id": 2,
        "username": "janedoe",
        "full_name": "Jane Doe",
        "profile_picture": "http://example.com/media/profile_pictures/image2.jpg"
      }
    ],
    "created_at": "2024-02-04T10:00:00Z"
  }
]
```

---

#### 2. Create Chat Room
**POST** `/api/chat/rooms/`

Chat xona yaratish.

- **Authentication**: ✅ Required
- **Request Body (Private Chat)**:
```json
{
  "room_type": "private",
  "members": [1, 2]
}
```

- **Request Body (Group Chat)**:
```json
{
  "room_type": "group",
  "name": "Project Team",
  "username": "project_team",
  "description": "Team discussion",
  "profile_pic": "<file>",
  "members": [1, 2, 3]
}
```

- **Response** (201 Created): Same as List Chat Rooms item

> **Validation**:
> - Private chat: `name`, `username`, `description`, `profile_pic` bo'sh bo'lishi kerak
> - Group chat: `name` majburiy

---

#### 3. Get Chat Room Detail
**GET** `/api/chat/rooms/<id>/`

Chat xona ma'lumotlarini ko'rish.

- **Authentication**: ✅ Required (Member only)
- **URL Parameters**:
  - `id` (string): Room UUID
  
- **Response** (200 OK): Same as List Chat Rooms item

---

#### 4. Update Chat Room
**PATCH** `/api/chat/rooms/<id>/`

Chat xonani yangilash (faqat group uchun).

- **Authentication**: ✅ Required (Admin/Owner only)
- **URL Parameters**:
  - `id` (string): Room UUID
  
- **Request Body**:
```json
{
  "name": "Updated Team Name",
  "description": "Updated description"
}
```

- **Response** (200 OK): Same as List Chat Rooms item

---

#### 5. Delete Chat Room
**DELETE** `/api/chat/rooms/<id>/`

Chat xonani o'chirish.

- **Authentication**: ✅ Required (Owner only for group, any member for private)
- **URL Parameters**:
  - `id` (string): Room UUID
  
- **Response** (204 No Content)

---

#### 6. Clear Room Messages
**POST** `/api/chat/rooms/<pk>/clear_messages/`

Chat xonadagi barcha xabarlarni o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `pk` (string): Room UUID
  
- **Response** (200 OK):
```json
{
  "message": "All messages cleared successfully"
}
```

---

### Room Members

#### 7. List Room Members
**GET** `/api/chat/members/<room_id>/list_members/`

Chat xona a'zolari ro'yxati.

- **Authentication**: ✅ Required (Member only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Response** (200 OK):
```json
[
  {
    "id": 1,
    "room": "room-uuid",
    "user": {
      "id": 1,
      "username": "johndoe",
      "full_name": "John Doe",
      "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
    },
    "role": "owner",
    "joined_at": "2024-02-04T10:00:00Z"
  }
]
```

- **Roles**:
  - `owner` - Xona egasi
  - `admin` - Administrator
  - `member` - Oddiy a'zo

---

#### 8. Join Room
**POST** `/api/chat/members/<room_id>/join/`

Chat xonaga qo'shilish.

- **Authentication**: ✅ Required
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Response** (201 Created):
```json
{
  "message": "Successfully joined the room"
}
```

---

#### 9. Leave Room
**POST** `/api/chat/members/<room_id>/leave/`

Chat xonadan chiqish.

- **Authentication**: ✅ Required (Member only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Response** (200 OK):
```json
{
  "message": "Successfully left the room"
}
```

---

#### 10. Set Admin
**POST** `/api/chat/members/<room_id>/set_admin/`

A'zoni admin qilish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Request Body**:
```json
{
  "user_id": 2
}
```

- **Response** (200 OK):
```json
{
  "message": "User promoted to admin"
}
```

---

#### 11. Remove Admin
**POST** `/api/chat/members/<room_id>/remove_admin/`

Adminlikni olib tashlash.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Request Body**:
```json
{
  "user_id": 2
}
```

- **Response** (200 OK):
```json
{
  "message": "Admin role removed"
}
```

---

#### 12. Transfer Ownership
**POST** `/api/chat/members/<room_id>/transfer_owner/`

Xona egasini o'zgartirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Request Body**:
```json
{
  "user_id": 2
}
```

- **Response** (200 OK):
```json
{
  "message": "Ownership transferred successfully"
}
```

---

#### 13. Add Member
**POST** `/api/chat/members/<room_id>/add_member/`

Yangi a'zo qo'shish.

- **Authentication**: ✅ Required (Admin/Owner only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Request Body**:
```json
{
  "user_id": 3
}
```

- **Response** (200 OK):
```json
{
  "message": "Member added successfully"
}
```

---

#### 14. Remove Member
**POST** `/api/chat/members/<room_id>/remove_member/`

A'zoni o'chirish.

- **Authentication**: ✅ Required (Admin/Owner only)
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Request Body**:
```json
{
  "user_id": 3
}
```

- **Response** (200 OK):
```json
{
  "message": "Member removed successfully"
}
```

---

### Messages

#### 15. List Messages by Room
**GET** `/api/chat/message/<room_id>/list_by_room/`

Chat xonadagi xabarlar ro'yxati.

- **Authentication**: ✅ Required (Member only)
- **Pagination**: ✅ Limit/Offset pagination
- **URL Parameters**:
  - `room_id` (string): Room UUID
  
- **Query Parameters**:
  - `limit` (integer, optional): Sahifadagi elementlar soni (default: 50)
  - `offset` (integer, optional): Boshlang'ich pozitsiya (default: 0)
  
- **Example**: `/api/chat/message/room-uuid/list_by_room/?limit=20&offset=0`

- **Response** (200 OK):
```json
{
  "count": 100,
  "next": "http://example.com/api/chat/message/room-uuid/list_by_room/?limit=20&offset=20",
  "previous": null,
  "results": [
    {
      "id": "message-uuid",
      "room": "room-uuid",
      "sender": {
        "id": 1,
        "username": "johndoe",
        "full_name": "John Doe",
        "profile_picture": "http://example.com/media/profile_pictures/image.jpg"
      },
      "text": "Hello everyone!",
      "reply_to": null,
      "attachments": [],
      "is_edited": false,
      "created_at": "2024-02-04T10:00:00Z",
      "update_at": "2024-02-04T10:00:00Z"
    }
  ]
}
```

> **Note**: Xabarlar WebSocket orqali yuboriladi. Bu endpoint faqat tarixni olish uchun.

---

#### 16. Delete Message
**DELETE** `/api/chat/message/<id>/`

Xabarni o'chirish.

- **Authentication**: ✅ Required (Sender only)
- **URL Parameters**:
  - `id` (string): Message UUID
  
- **Response** (204 No Content)

---

### Files

#### 17. List Files
**GET** `/api/chat/files/`

Yuklangan fayllar ro'yxati.

- **Authentication**: ✅ Required
- **Response** (200 OK):
```json
[
  {
    "id": 1,
    "unique_id": "hash-string",
    "file": "http://example.com/media/chat_files/file.pdf",
    "file_type": "document",
    "file_size": 1024000,
    "is_temporary": false,
    "uploaded_at": "2024-02-04T10:00:00Z"
  }
]
```

- **File Types**:
  - `image` - Rasm
  - `video` - Video
  - `voice` - Ovozli xabar
  - `document` - Hujjat
  - `other` - Boshqa

---

#### 18. Upload File
**POST** `/api/chat/files/`

Fayl yuklash.

- **Authentication**: ✅ Required
- **Content-Type**: `multipart/form-data`
- **Request Body**:
```json
{
  "file": "<file>",
  "file_type": "document"
}
```

- **Response** (201 Created): Same as List Files item

> **Note**: Bir xil fayllar hash asosida aniqlanadi va qayta yuklanmaydi.

---

#### 19. Delete File
**DELETE** `/api/chat/files/<id>/`

Faylni o'chirish.

- **Authentication**: ✅ Required (Owner only)
- **URL Parameters**:
  - `id` (integer): File ID
  
- **Response** (204 No Content)

---

## Notifications API

Base path: `/api/comments/`

> **Note**: Bu app asosiy bildirishnomalar uchun emas, balki umumiy izohlar uchun ishlatiladi.

### Comments

#### 1. List Comments
**GET** `/api/comments/comment`

Barcha izohlar ro'yxati.

- **Authentication**: ❌ Not required (AllowAny)
- **Response** (200 OK):
```json
[
  {
    "id": 1,
    "content": "This is a comment",
    "created_at": "2024-02-04T10:00:00Z"
  }
]
```

---

#### 2. Create Comment
**POST** `/api/comments/comment`

Izoh yaratish.

- **Authentication**: ❌ Not required (AllowAny)
- **Request Body**:
```json
{
  "content": "This is a new comment"
}
```

- **Response** (201 Created): Same as List Comments item

---

## WebSocket Connections

### Chat WebSocket

Chat xabarlari real-time yuborish va qabul qilish uchun WebSocket ishlatiladi.

**WebSocket URL**: `ws://your-domain/ws/chat/<room_id>/`

#### Connection
```javascript
const socket = new WebSocket('ws://your-domain/ws/chat/room-uuid/');

socket.onopen = function(e) {
  console.log('Connected to chat');
};

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Message received:', data);
};

socket.onclose = function(event) {
  console.log('Disconnected from chat');
};

socket.onerror = function(error) {
  console.log('WebSocket error:', error);
};
```

#### Send Message
```javascript
socket.send(JSON.stringify({
  'type': 'chat_message',
  'message': 'Hello!',
  'reply_to': null,
  'files': []
}));
```

#### Message Events
- `chat_message` - Yangi xabar
- `message_edited` - Xabar tahrirlandi
- `message_deleted` - Xabar o'chirildi
- `user_typing` - Foydalanuvchi yozmoqda
- `message_read` - Xabar o'qildi

---

## Error Responses

Barcha API endpointlar quyidagi error formatlarini qaytaradi:

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": {
    "field_name": ["Error message"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "message": "Request was throttled",
  "wait_seconds": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error occurred"
}
```

---

## Rate Limiting

Ba'zi endpointlar rate limiting (throttling) ga ega:

| Scope | Limit |
|-------|-------|
| `email_verify` | Cheklangan |
| `forget_password` | Cheklangan |
| `new_password` | Cheklangan |
| `profile_search` | Cheklangan |
| `public_profile` | Cheklangan |

> **Note**: Aniq limitlar server konfiguratsiyasida belgilangan.

---

## Pagination

List endpointlar pagination qo'llab-quvvatlaydi:

### Default Pagination
```json
{
  "count": 100,
  "next": "http://example.com/api/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### Limit/Offset Pagination (Chat Messages)
```json
{
  "count": 100,
  "next": "http://example.com/api/endpoint/?limit=20&offset=20",
  "previous": null,
  "results": [...]
}
```

**Query Parameters**:
- `limit` - Sahifadagi elementlar soni
- `offset` - Boshlang'ich pozitsiya

---

## File Upload

File yuklash uchun `multipart/form-data` Content-Type ishlatiladi.

### Supported File Fields
- `profile_picture` - Profil rasmi
- `images` - Post rasmlari (bir nechta)
- `media` - Story media (rasm/video)
- `profile_pic` - Guruh rasmi
- `file` - Chat fayli

### Example (JavaScript)
```javascript
const formData = new FormData();
formData.append('content', 'My post');
formData.append('images', file1);
formData.append('images', file2);

fetch('/api/posts/post/', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer ' + accessToken
  },
  body: formData
});
```

---

## Best Practices

1. **Token Management**
   - Access token ni localStorage yoki secure cookie da saqlang
   - Refresh token ni faqat secure cookie da saqlang
   - Token expired bo'lganda refresh token orqali yangilang

2. **Error Handling**
   - Barcha API so'rovlarida error handling qo'shing
   - 401 error da foydalanuvchini login sahifasiga yo'naltiring
   - Network errorlarni to'g'ri handle qiling

3. **Performance**
   - Pagination dan foydalaning
   - Kerakli ma'lumotlarni cache qiling
   - Debounce/throttle qidirish so'rovlarini

4. **Security**
   - HTTPS dan foydalaning
   - Token ni URL da yubormang
   - Sensitive ma'lumotlarni console.log qilmang

5. **WebSocket**
   - Reconnection logic qo'shing
   - Heartbeat/ping-pong implement qiling
   - Connection state ni track qiling

---

## Swagger Documentation

Interactive API documentation Swagger orqali mavjud:

- **Swagger UI**: `http://your-domain/swdoc/`
- **ReDoc**: `http://your-domain/redoc/`

Bu yerda barcha endpointlarni to'g'ridan-to'g'ri test qilishingiz mumkin.

---

## Support

Savollar yoki muammolar bo'lsa:
- Email: oybekrozievich@gmail.com
- GitHub: https://github.com/rozievich/UzbekHub
