# 🌱 Web Tư Vấn Tâm Lý Dành Cho Tuổi Dậy Thì (sử dụng Gemini)

Một ứng dụng web đơn giản giúp người dùng, đặc biệt là tuổi dậy thì, trò chuyện với AI để nhận được lời khuyên tâm lý nhẹ nhàng, thân thiện, và phù hợp. Dữ liệu và người dùng được quản lý qua hệ thống tài khoản, có phân quyền người dùng và quản trị viên.

---

## 🚀 Tính năng chính

- 💬 Trò chuyện với AI (Gemini 2.0 Flash) bằng tiếng Việt.
- 👥 Đăng ký / đăng nhập / đăng xuất người dùng.
- 📊 Trang quản trị: thống kê người dùng, lượt nhắn tin, phân tích cảm xúc,...
- 🧠 Lưu lịch sử trò chuyện theo từng phiên.
- 🔒 Bảo vệ quyền truy cập theo phân quyền người dùng / admin.
- 📁 Lưu trữ bằng SQLite, tự động tạo cơ sở dữ liệu.

---

## 📦 Yêu cầu hệ thống

- Python 3.8+
- API Key của [Google Gemini](https://ai.google.dev/)

---

## 🛠️ Cài đặt

### 1. Clone dự án
```bash
git clone https://github.com/DTA-Child/WebTuVanTamLyBangGemini.git
cd WebTuVanTamLyBangGemini


### Cấu hình ứng dụng

Ứng dụng sẽ tự động tạo cơ sở dữ liệu SQLite khi chạy lần đầu. Nếu muốn thay đổi cấu hình, bạn có thể chỉnh sửa trong các tệp sau:

- **config.py**: Cấu hình kết nối và các tham số ứng dụng. Cần đưa api key vào đây.
- **database.py**: Cấu hình và thao tác với cơ sở dữ liệu.

### Chạy ứng dụng

Sau khi cài đặt xong, bạn có thể chạy ứng dụng bằng lệnh sau:

```bash
python ./app