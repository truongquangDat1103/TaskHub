# TaskHub - FastAPI Backend Training Project

Hệ thống quản lý công việc và dự án phân tầng (TaskHub) xây dựng bằng FastAPI, SQLAlchemy 2.x async, PostgreSQL, Redis và Docker.

## 🌟 Tính năng theo lộ trình đào tạo (Day 1 - Day 8)

1. **Day 1: Core Setup & CRUD Task**
   - Kiến trúc phân tầng: Router (`api/v1`) → Service → Repository → Model/Schema.
   - Pydantic v2 schemas (`extra="forbid"`, `str_strip_whitespace=True`).
   - Xử lý triệt để validation null trên PATCH (chặn `{"title": null}` trả về 422 Unprocessable Entity thay vì 500).
   - Hệ thống Custom Exception (`AppException`, `NotFoundException`, `ConflictException`, `ForbiddenException`, `AuthenticationException`).
   - Chuẩn hóa constants và messages tập trung.

2. **Day 2: Database Models & Migrations**
   - Tích hợp PostgreSQL async với SQLAlchemy 2.x (`asyncpg`) và `async_sessionmaker`.
   - Thiết kế 8 bảng quan hệ: `users`, `workspaces`, `workspace_members`, `projects`, `tasks`, `labels`, `task_labels`, `comments`, cùng `refresh_tokens`.
   - Setup Alembic async migrations tự động.
   - Xây dựng `BaseRepository[T]` generic hỗ trợ CRUD async hoàn chỉnh.

3. **Day 3: Authentication & Security (RBAC)**
   - Hash mật khẩu an toàn với Argon2 & Bcrypt (giới hạn 72 bytes chuẩn Bcrypt).
   - JWT HS256: claims `sub`, `exp`, `iat`, `jti`, `type` ("access" vs "refresh").
   - Refresh Token Rotation nguyên tử (atomic inside transaction) và cơ chế phát hiện reuse token để vô hiệu hóa toàn bộ session.
   - Thu hồi (revoke) refresh tokens khi đổi mật khẩu và đăng xuất.
   - Xử lý lỗi 401 giữ nguyên header `WWW-Authenticate: Bearer`.
   - Bắt `IntegrityError` khi đăng ký trùng email trả về 409 Conflict.
   - Tích hợp Authorize Bearer token trên Swagger UI.

4. **Day 4: Workspaces Management**
   - CRUD Workspace, tự động gán creator làm `OWNER` trong cùng một transaction.
   - Quản lý thành viên Workspace (thêm / xóa).
   - Phân quyền RBAC (`ADMIN`, `OWNER`, `EDITOR`, `VIEWER`).
   - Đảm bảo tính toàn vẹn: không cho phép xóa OWNER cuối cùng, không cho admin tự xóa chính mình.

5. **Day 5: Tasks & Projects Management**
   - CRUD Projects theo Workspace.
   - CRUD Tasks theo Project (tiêu đề, mô tả, độ ưu tiên, trạng thái, hạn chót).
   - Kiểm tra `assignee_id`: người được gán bắt buộc phải là thành viên hợp lệ của Workspace.
   - Phân quyền: VIEWER chỉ có quyền đọc, EDITOR/OWNER/ADMIN có quyền tạo và chỉnh sửa.

6. **Day 6: Labels & Comments Management**
   - CRUD Labels theo Project; gán/gỡ label cho Task (đảm bảo tính idempotent).
   - Thêm và xóa bình luận (Comment) trên Task.
   - Kiểm soát quyền sở hữu (Resource Ownership): chỉ người tạo bình luận hoặc OWNER/ADMIN mới được xóa bình luận.

7. **Day 7: Searching, Filtering, Pagination & Redis Caching**
   - Lọc Task theo `status`, `priority`, `assignee_id`, tìm kiếm theo `q`.
   - Phân trang chuẩn với `page` và `limit`.
   - Tích hợp Redis Caching cho endpoint `GET /api/v1/projects/{id}/tasks` với TTL 300s.
   - Tự động Invalidate cache khi tạo, sửa, xóa Task hoặc thay đổi nhãn (Label).
   - Cơ chế Graceful Fallback: nếu Redis gặp sự cố, hệ thống tự động fallback về database mà không gây gián đoạn API.

8. **Day 8: Background Tasks, Swagger Documentation & Docker Setup**
   - FastAPI `BackgroundTasks`: tự động gửi email thông báo ngầm khi task được giao (assign) hoặc thay đổi người phụ trách mà không làm chậm API.
   - Tài liệu OpenAPI / Swagger UI & ReDoc đầy đủ với mô tả chi tiết các schema và mã lỗi (400, 401, 403, 404, 409, 422).
   - `Dockerfile` và `docker-compose.yml` khởi chạy trọn bộ stack (`app`, `db` PostgreSQL 16, `redis`).
   - Đạt 100% Ruff lint & format, 0 lỗi Mypy strict.

---

## 🚀 Hướng dẫn cài đặt và khởi chạy

### Cách 1: Khởi chạy bằng Docker Compose (Khuyến nghị)
```bash
docker compose up --build
```
API sẽ sẵn sàng tại `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`  
ReDoc: `http://localhost:8000/redoc`

### Cách 2: Khởi chạy môi trường Local
1. **Tạo môi trường ảo và cài đặt thư viện:**
   ```bash
   uv venv .venv
   .venv\Scripts\activate  # Trên Windows
   uv pip install -r requirements.txt
   ```
2. **Cấu hình biến môi trường:**
   ```bash
   cp .env.example .env
   # Điều chỉnh DATABASE_URL, REDIS_URL, JWT_SECRET_KEY nếu cần
   ```
3. **Chạy Migration:**
   ```bash
   alembic upgrade head
   ```
4. **Khởi động server:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

---

## 🧪 Kiểm thử và Đảm bảo chất lượng

- **Chạy toàn bộ 163+ Unit/Integration Tests:**
  ```bash
  pytest
  ```
- **Kiểm tra Linting & Định dạng với Ruff:**
  ```bash
  ruff check
  ruff format --check
  ```
- **Kiểm tra Static Typing với Mypy:**
  ```bash
  mypy app
  ```
