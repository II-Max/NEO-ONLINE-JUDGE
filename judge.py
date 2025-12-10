import firebase_admin
from firebase_admin import credentials, db
import subprocess
import os
import sys

# --- CẤU HÌNH ---
KEY_PATH = "service-account.json"
DATABASE_URL = "https://khkt2025-2026-default-rtdb.firebaseio.com/"

if not os.path.exists(KEY_PATH):
    print(f"LỖI: Thiếu file '{KEY_PATH}'")
    sys.exit(1)

if not firebase_admin._apps:
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred, {'databaseURL': DATABASE_URL})

print(f">>> MÁY CHẤM ĐA NGÔN NGỮ (PYTHON + C++) ĐANG CHẠY...")
print(f">>> Sẵn sàng tại: {DATABASE_URL}")

# --- HÀM CHẠY PYTHON ---
def run_python(code, input_str):
    filename = "temp.py"
    with open(filename, "w", encoding="utf-8") as f: f.write(code)
    try:
        process = subprocess.run([sys.executable, filename], input=input_str, text=True, capture_output=True, timeout=2)
        if process.stderr: return None, f"Runtime Error: {process.stderr}"
        return process.stdout.strip(), None
    except subprocess.TimeoutExpired: return None, "Time Limit Exceeded"
    except Exception as e: return None, str(e)

# --- HÀM CHẠY C++ (MỚI) ---
def run_cpp(code, input_str):
    src_file = "temp.cpp"
    exe_file = "temp.exe"
    
    # 1. Ghi file source
    with open(src_file, "w", encoding="utf-8") as f: f.write(code)
    
    # 2. Biên dịch (Compile)
    # Lệnh: g++ temp.cpp -o temp.exe
    compile_res = subprocess.run(["g++", src_file, "-o", exe_file], capture_output=True, text=True)
    
    if compile_res.returncode != 0:
        return None, f"Compile Error (Lỗi biên dịch):\n{compile_res.stderr}"
    
    # 3. Chạy file exe
    try:
        process = subprocess.run([exe_file], input=input_str, text=True, capture_output=True, timeout=2)
        if process.returncode != 0: return None, "Runtime Error (Lỗi khi chạy)"
        return process.stdout.strip(), None
    except subprocess.TimeoutExpired: return None, "Time Limit Exceeded"
    except Exception as e: return None, str(e)

# --- XỬ LÝ CHÍNH ---
def cham_bai(sid, data):
    print(f"\n[NEW] {data.get('language', 'python').upper()} | User: {data.get('name')} | Bài: {data.get('problem_id')}")
    
    prob_id = data.get('problem_id')
    lang = data.get('language', 'python') # Mặc định là python nếu không có
    
    prob_info = db.reference(f'problems/{prob_id}').get()
    if not prob_info: return print(" -> Lỗi: Không thấy đề bài!")

    testcases = prob_info.get('testcases', [])
    passed = 0
    details = []

    for i, test in enumerate(testcases):
        print(f" -> Test {i+1}...", end="")
        
        # CHỌN TRÌNH CHẤM DỰA VÀO NGÔN NGỮ
        if lang == 'cpp':
            actual, err = run_cpp(data['code'], test['input'])
        else:
            actual, err = run_python(data['code'], test['input'])

        if err:
            print(" ERROR")
            details.append(f"Test {i+1}: {err}")
            continue
            
        if actual == test['output'].strip():
            print(" PASS")
            passed += 1
        else:
            print(" FAIL")
            details.append(f"Test {i+1}: Sai kết quả")

    score = int((passed / len(testcases)) * 100) if testcases else 0
    msg = f"Đúng {passed}/{len(testcases)} test."
    if score < 100 and details: msg += f" ({details[0]})"

    print(f"[KẾT QUẢ] {score} điểm. Đẩy lên server...")
    db.reference(f'submissions/{sid}').update({
        'status': 'completed', 'score': score, 'message': msg
    })

def listener(event):
    if not event.data: return
    if event.path == "/":
        data = event.data
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict) and v.get('status') == 'pending': cham_bai(k, v)
    else:
        sid = event.path.strip("/")
        if not sid: return
        curr = db.reference(f'submissions/{sid}').get()
        if curr and curr.get('status') == 'pending': cham_bai(sid, curr)

try:
    db.reference('submissions').listen(listener)
except Exception as e: print(e)