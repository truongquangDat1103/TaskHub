# TaskHub - Enterprise Project & Task Management Backend

Hệ thống quản lý công việc và dự án phân tầng (TaskHub) được xây dựng dựa trên FastAPI hiện đại, kiến trúc phân tầng (Layered Architecture), cơ sở dữ liệu quan hệ PostgreSQL (asyncpg), bộ nhớ đệm Redis, xử lý tác vụ ngầm và đóng gói toàn diện với Docker.

---

## ✨ Tính Năng Nổi Bật (Core Features)

### 1. Quản Trị Hệ Thống & Xác Thực An Toàn (Authentication & Security)
- **Cơ chế xác thực JWT:** Cấp phát Access Token và Refresh Token chuẩn HS256 với các claim kiểm soát chặt chẽ (`sub`, `exp`, `iat`, `jti`, `type`).
- **Refresh Token Rotation & Reuse Detection:** Tự động xoay vòng token nguyên tử (atomic transaction) trong cơ sở dữ liệu. Khi phát hiện token cũ bị tái sử dụng, hệ thống lập tức thu hồi toàn bộ token family của tài khoản để chống tấn công đánh cắp phiên.
- **Bảo mật mật khẩu:** Hash mật khẩu an toàn với thuật toán Bcrypt / Argon2, giới hạn độ dài chuẩn 72 bytes chống tấn công DoS, bảo toàn ký tự khoảng trắng người dùng nhập.
- **Vô hiệu hóa Token tức thì (`token_version`):** Thu hồi hiệu lực của toàn bộ Access Token đang lưu hành ngay khi người dùng đổi mật khẩu hoặc đăng xuất mà không cần chờ token hết hạn.
- **Kiểm soát truy cập dựa trên vai trò (RBAC):** Phân quyền người dùng ở mức hệ thống (`ADMIN`, `MEMBER`).

### 2. Quản Lý Không Gian Làm Việc (Workspace Management)
- **Quản lý Workspace:** Tạo mới, cập nhật thông tin và quản lý vòng đời không gian làm việc. Tự động thiết lập người tạo làm `OWNER` trong cùng một transaction.
- **Quản lý thành viên linh hoạt:** Thêm, xóa thành viên và phân bổ vai trò nội bộ (`OWNER`, `EDITOR`, `VIEWER`).
- **Bảo vệ toàn vẹn & Chống tấn công dò quét:**
  - Chặn gán quyền `OWNER` trực tiếp từ request body qua Pydantic schema validation.
  - Nghiêm cấm xóa hoặc giáng cấp thành viên giữ vai trò `OWNER` duy nhất.
  - Bảo vệ chống dò quét ID tài nguyên (ID Enumeration): Trả về `404 Not Found` thay vì `403 Forbidden` đối với người ngoài workspace.

### 3. Quản Lý Dự Án & Công Việc (Project & Task Management)
- **Mô hình phân cấp:** Quản lý dự án thuộc từng Workspace, và quản lý công việc (Task) theo từng Project.
- **Quản lý vòng đời Task:** Cập nhật trạng thái trực quan (`TODO` → `IN_PROGRESS` → `DONE`), thiết lập mức độ ưu tiên (`LOW`, `MEDIUM`, `HIGH`, `URGENT`), ngày đến hạn (`due_date` kiểm tra thời gian tương lai và serialize chuẩn ISO 8601 UTC đuôi `'Z'`).
- **Ràng buộc thành viên nghiêm ngặt:** Xác thực `assignee_id` bắt buộc phải là thành viên hợp lệ thuộc Workspace chứa dự án đó.
- **Phân quyền thao tác:** Thành viên vai trò `VIEWER` chỉ có quyền xem; vai trò `EDITOR`, `OWNER` hoặc `ADMIN` có toàn quyền tạo và chỉnh sửa.

### 4. Hệ Thống Nhãn Dán & Bình Luận (Labels & Comments)
- **Quản lý Label theo Project:** Tạo nhãn với mã màu tùy biến, đảm bảo tính duy nhất của tên nhãn không phân biệt hoa thường (`case-insensitive`). Hỗ trợ gán và gỡ nhãn cho Task an toàn và idempotent.
- **Bình luận & Thảo luận (Comments):** Hỗ trợ tương tác trao đổi trực tiếp trên từng Task.
- **Kiểm soát quyền sở hữu (Resource Ownership):** Cung cấp endpoint `PATCH /comments/{id}` cho tác giả chỉnh sửa nội dung; chỉ cho phép tác giả, Workspace `OWNER` hoặc hệ thống `ADMIN` có quyền xóa bình luận.

### 5. Tìm Kiếm Nâng Cao, Phân Trang & Bộ Nhớ Đệm (Caching & Performance)
- **Bộ lọc đa tiêu chí:** Lọc danh sách công việc theo trạng thái, mức độ ưu tiên, người phụ trách và tìm kiếm từ khóa (`q`).
- **Phân trang chuẩn hóa:** Schema generic `Page[T]` cung cấp thông tin phân trang chuẩn mực (`page`, `limit`, `total_items`, `total_pages`).
- **Redis Caching tốc độ cao:** Tích hợp bộ nhớ đệm Redis cho endpoint truy vấn danh sách công việc (`GET /api/v1/projects/{id}/tasks`) với TTL 300 giây.
- **Tự động xóa cache (Auto-Invalidation):** Tự động phát hiện và dọn dẹp cache tương ứng ngay khi có thao tác tạo, sửa, xóa Task hoặc thay đổi nhãn gán.
- **Cơ chế dự phòng (Graceful Fallback):** Tự động fallback về cơ sở dữ liệu nếu dịch vụ Redis tạm thời mất kết nối, đảm bảo API hoạt động liên tục không gián đoạn.

### 6. Xử Lý Tác Vụ Ngầm (Background Tasks & Notifications)
- **Thông báo email bất đồng bộ:** Tích hợp `FastAPI BackgroundTasks` tự động gửi email thông báo khi task được phân công hoặc thay đổi người phụ trách mà không làm tăng độ trễ (latency) của API response.

### 7. Kiến Trúc Hệ Thống & Hạ Tầng Triển Khai (Architecture & DevOps)
- **Kiến trúc phân tầng (Layered Architecture):** Tách biệt rõ ràng trách nhiệm giữa `Router (API)` → `Service (Business Logic)` → `Repository (Data Access)` → `Schema / Model`.
- **Validation & Custom Exceptions:** Sử dụng Pydantic v2 với cấu hình chặt chẽ (`extra="forbid"`, `str_strip_whitespace=True`), chuẩn hóa response lỗi 422 dạng danh sách `{"detail": [{"field": "...", "message": "..."}]}`, và quản lý ngoại lệ tập trung với `AppException`.
- **Database & Migration:** PostgreSQL 16 Async với SQLAlchemy 2.x (`asyncpg`), connection pooling và Alembic migration quản lý lược đồ dữ liệu.
- **Containerization:** Đóng gói toàn bộ dịch vụ (FastAPI App, PostgreSQL, Redis) với `Dockerfile` đa tầng và `docker-compose.yml` sẵn sàng khởi chạy bằng một lệnh duy nhất.
- **Chất Lượng Code & Kiểm Thử:** Đạt 100% tuân thủ `ruff check`, `ruff format` và `mypy` strict type-checking, cùng bộ hơn **175 unit/integration tests** tự động.

---

## 🚀 Hướng dẫn cài đặt và khởi chạy

### Cách 1: Khởi chạy bằng Docker Compose (Khuyến nghị)
```bash
docker compose up --build
```
- API Endpoint: `http://localhost:8000`  
- Swagger UI (Tài liệu tương tác): `http://localhost:8000/docs`  
- ReDoc: `http://localhost:8000/redoc`

### Cách 2: Khởi chạy môi trường Local
1. **Tạo môi trường ảo và cài đặt thư viện:**
   ```bash
   uv venv .venv
   .venv\Scripts\activate  # Trên Windows (Linux/macOS: source .venv/bin/activate)
   uv pip install -r requirements.txt -r requirements-dev.txt
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

- **Chạy toàn bộ 175+ Unit/Integration Tests:**
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
