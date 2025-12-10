import firebase_admin
from firebase_admin import credentials, db
import json
import os
import sys

# ==============================================================================
# CẤU HÌNH (SỬA LINK DATABASE CỦA BẠN VÀO ĐÂY)
# ==============================================================================
KEY_PATH = "service-account.json"
DATABASE_URL = "https://khkt2025-2026-default-rtdb.firebaseio.com/"

# CẤU HÌNH CÁC FILE CẦN ĐẨY (Tên file : Tên nhánh trên Firebase)
# Bạn có thể thêm bớt tùy ý tại đây
FILES_CONFIG = {
    "baitap.json": "problems",   # Nội dung file baitap.json sẽ vào nhánh 'problems'
    "tailieu.json": "documents", # Nội dung file tailieu.json sẽ vào nhánh 'documents'
    "video.json": "videos"       # Nội dung file video.json sẽ vào nhánh 'videos'
}
# ==============================================================================

def init_firebase():
    if not os.path.exists(KEY_PATH):
        print(f"❌ LỖI: Thiếu file '{KEY_PATH}'. Hãy tải từ Firebase Console về!")
        sys.exit(1)
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(KEY_PATH)
        firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})
        print("✅ Đã kết nối tới Firebase.")

def upload_file(filename, node_name):
    if not os.path.exists(filename):
        print(f"⚠️ Bỏ qua: Không tìm thấy file '{filename}' (Sẽ không cập nhật nhánh '{node_name}')")
        return

    try:
        print(f"⏳ Đang đọc file '{filename}'...")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"🚀 Đang đẩy dữ liệu lên nhánh '/{node_name}'...")
        # Lệnh .set() chỉ thay đổi nhánh này, không ảnh hưởng nhánh khác
        db.reference(node_name).set(data) 
        print(f"✅ THÀNH CÔNG: Đã cập nhật '{node_name}'!")
        
    except json.JSONDecodeError:
        print(f"❌ LỖI: File '{filename}' bị lỗi cú pháp JSON. Hãy kiểm tra lại dấu phẩy/ngoặc.")
    except Exception as e:
        print(f"❌ LỖI HỆ THỐNG: {str(e)}")

# --- CHƯƠNG TRÌNH CHÍNH ---
if __name__ == "__main__":
    print("="*50)
    print("TOOL QUẢN LÝ DỮ LIỆU KHKT 2026")
    print("="*50)
    
    init_firebase()
    
    print("\n--- BẮT ĐẦU XỬ LÝ ---")
    for file_name, db_node in FILES_CONFIG.items():
        upload_file(file_name, db_node)
        print("-" * 30)
    
    print("\n🎉 HOÀN TẤT QUÁ TRÌNH.")