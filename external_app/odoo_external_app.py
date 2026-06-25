#!/usr/bin/env python3
"""Ung dung ben ngoai demo ket noi Odoo qua XML-RPC.

Chay:
    python3 external_app/odoo_external_app.py
Mo trinh duyet:
    http://localhost:8070
"""

import json
import os
import time
import xmlrpc.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HOST = os.getenv("EXTERNAL_APP_HOST", "0.0.0.0")
PORT = int(os.getenv("EXTERNAL_APP_PORT", "8070"))
SESSION = {
    "url": os.getenv("ODOO_URL", "http://localhost:8069"),
    "db": os.getenv("ODOO_DB", "admin"),
    "username": os.getenv("ODOO_USERNAME", ""),
    "password": os.getenv("ODOO_PASSWORD", ""),
    "uid": None,
}

INDEX_HTML = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>External App - QLKH & QLVB</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#f4f7fb;color:#1f2937}header{background:#172a3a;color:#fff;padding:18px 28px;display:flex;justify-content:space-between;align-items:center}header h1{font-size:20px;margin:0}header span{color:#b8c7d9;font-size:13px}main{padding:24px;max-width:1180px;margin:0 auto}section{background:#fff;border:1px solid #d9e2ef;border-radius:8px;padding:18px;margin-bottom:18px;box-shadow:0 8px 18px rgba(15,23,42,.05)}h2{margin:0 0 14px;font-size:17px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}label{font-size:12px;color:#667085;display:block;margin-bottom:5px}input,select,textarea{width:100%;border:1px solid #cbd5e1;border-radius:6px;padding:9px 10px;font-size:14px;background:#fff}textarea{min-height:76px;resize:vertical}button{border:0;border-radius:6px;padding:10px 14px;background:#2563eb;color:#fff;cursor:pointer;font-weight:600}button.secondary{background:#475569}button.success{background:#047857}.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}.status{padding:10px 12px;border-radius:6px;background:#eff6ff;color:#1d4ed8;margin-top:12px;white-space:pre-wrap}.status.error{background:#fef2f2;color:#b91c1c}.status.ok{background:#ecfdf5;color:#047857}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:9px 8px;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top}th{color:#475569;background:#f8fafc}.split{display:grid;grid-template-columns:1fr 1fr;gap:18px}.pill{display:inline-block;padding:3px 8px;border-radius:999px;background:#e0f2fe;color:#0369a1;font-size:12px}@media(max-width:860px){.grid,.split{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div><h1>Ứng dụng bên ngoài - Quản lý khách hàng & văn bản</h1><span>kết nối Odoo bằng XML-RPC External API</span></div><span id="connectionBadge">Chưa kết nối</span></header>
<main>
<section><h2>Kết nối Odoo</h2><div class="grid"><div><label>Odoo URL</label><input id="url" value="http://localhost:8069"></div><div><label>Database</label><input id="db" value="admin"></div><div><label>User</label><input id="username" placeholder="Nhập user Odoo"></div><div><label>Mật khẩu</label><input id="password" type="password" placeholder="Nhập mật khẩu Odoo"></div></div><div class="actions"><button onclick="connect()">Kết nối</button><button class="secondary" onclick="loadAll()">Tải dữ liệu</button></div><div id="status" class="status">Nhập thông tin Odoo rồi bấm Kết nối. Có thể đặt ODOO_USERNAME/ODOO_PASSWORD bằng biến môi trường để không ghi vào mã nguồn.</div></section>
<section><h2>Tạo khách hàng từ ứng dụng bên ngoài</h2><div class="grid"><div><label>Tên khách hàng</label><input id="newName" value="Công ty Demo App Ngoài"></div><div><label>Số điện thoại</label><input id="newPhone" value="0900000000"></div><div><label>Email</label><input id="newEmail" value="external-demo@example.com"></div><div><label>Mức ưu tiên</label><select id="newPriority"><option value="cao">Cao</option><option value="trung_binh">Trung bình</option><option value="thap">Thấp</option></select></div></div><div style="margin-top:12px"><label>Ghi chú</label><textarea id="newNote">Khách hàng được tạo từ ứng dụng bên ngoài qua External API.</textarea></div><div class="actions"><button class="success" onclick="createCustomer()">Tạo khách hàng trong Odoo</button></div></section>
<div class="split"><section><h2>Khách hàng trong Odoo</h2><div id="customers"></div></section><section><h2>Văn bản trong Odoo</h2><div id="documents"></div></section></div>
</main>
<script>
async function api(path, options={}){const res=await fetch(path,{headers:{'Content-Type':'application/json'},...options});const data=await res.json();if(!res.ok||data.error)throw new Error(data.error||'Lỗi gọi API');return data}
function setStatus(message,kind=''){const el=document.getElementById('status');el.textContent=message;el.className='status '+kind}
async function connect(){try{const data=await api('/api/connect',{method:'POST',body:JSON.stringify({url:document.getElementById('url').value,db:document.getElementById('db').value,username:document.getElementById('username').value,password:document.getElementById('password').value})});document.getElementById('connectionBadge').textContent='Đã kết nối UID '+data.uid;setStatus('Kết nối thành công tới Odoo. Bây giờ có thể tải dữ liệu hoặc tạo khách hàng.','ok');await loadAll()}catch(err){setStatus(err.message,'error')}}
async function loadAll(){await Promise.all([loadCustomers(),loadDocuments()])}
async function loadCustomers(){try{const data=await api('/api/customers');const rows=data.customers.map(c=>`<tr><td>${c.ma_khach_hang||''}</td><td>${c.name||''}</td><td>${c.phone||''}</td><td>${c.email||''}</td><td><span class="pill">${c.tong_so_van_ban||0} văn bản</span></td></tr>`).join('');document.getElementById('customers').innerHTML=`<table><thead><tr><th>Mã</th><th>Tên</th><th>SĐT</th><th>Email</th><th>Hồ sơ</th></tr></thead><tbody>${rows||'<tr><td colspan="5">Chưa có dữ liệu</td></tr>'}</tbody></table>`}catch(err){document.getElementById('customers').innerHTML='<div class="status error">'+err.message+'</div>'}}
async function loadDocuments(){try{const data=await api('/api/documents');const rows=data.documents.map(d=>`<tr><td>${d.direction}</td><td>${d.so||''}</td><td>${d.ten||''}</td><td>${d.nhom||''}</td><td>${d.ai||''}</td></tr>`).join('');document.getElementById('documents').innerHTML=`<table><thead><tr><th>Loại</th><th>Số</th><th>Tên văn bản</th><th>Nhóm</th><th>AI đề xuất</th></tr></thead><tbody>${rows||'<tr><td colspan="5">Chưa có dữ liệu</td></tr>'}</tbody></table>`}catch(err){document.getElementById('documents').innerHTML='<div class="status error">'+err.message+'</div>'}}
async function createCustomer(){try{const data=await api('/api/customers',{method:'POST',body:JSON.stringify({name:document.getElementById('newName').value,phone:document.getElementById('newPhone').value,email:document.getElementById('newEmail').value,priority:document.getElementById('newPriority').value,note:document.getElementById('newNote').value})});setStatus('Đã tạo khách hàng trong Odoo: ID '+data.id+' - '+data.name,'ok');await loadCustomers()}catch(err){setStatus(err.message,'error')}}
</script>
</body></html>"""


def _common():
    return xmlrpc.client.ServerProxy(SESSION["url"].rstrip("/") + "/xmlrpc/2/common", allow_none=True)


def _models():
    return xmlrpc.client.ServerProxy(SESSION["url"].rstrip("/") + "/xmlrpc/2/object", allow_none=True)


def _authenticate():
    uid = _common().authenticate(SESSION["db"], SESSION["username"], SESSION["password"], {})
    if not uid:
        raise RuntimeError("Không đăng nhập được. Kiểm tra URL, database, user hoặc mật khẩu.")
    SESSION["uid"] = uid
    return uid


def _external_customer_code():
    return "EXT%s" % time.time_ns()


def _execute(model, method, args=None, kwargs=None):
    if not SESSION.get("uid"):
        _authenticate()
    return _models().execute_kw(SESSION["db"], SESSION["uid"], SESSION["password"], model, method, args or [], kwargs or {})


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self):
        body = INDEX_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == "/":
                self.send_html()
            elif path == "/api/status":
                self.send_json({"connected": bool(SESSION.get("uid")), "uid": SESSION.get("uid")})
            elif path == "/api/customers":
                self.send_json({"customers": self.get_customers()})
            elif path == "/api/documents":
                self.send_json({"documents": self.get_documents()})
            else:
                self.send_json({"error": "Không tìm thấy endpoint"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_json()
            if path == "/api/connect":
                SESSION.update({"url": payload.get("url") or SESSION["url"], "db": payload.get("db") or SESSION["db"], "username": payload.get("username") or SESSION["username"], "password": payload.get("password") or SESSION["password"], "uid": None})
                uid = _authenticate()
                self.send_json({"uid": uid, "username": SESSION["username"]})
            elif path == "/api/customers":
                self.create_customer(payload)
            else:
                self.send_json({"error": "Không tìm thấy endpoint"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def get_customers(self):
        return _execute("res.partner", "search_read", [[["is_khach_hang", "=", True]]], {"fields": ["ma_khach_hang", "name", "phone", "email", "muc_do_uu_tien", "trang_thai_cham_soc", "tong_so_van_ban"], "limit": 20, "order": "id desc"})

    def get_documents(self):
        docs = []
        den = _execute("van_ban_den", "search_read", [[]], {"fields": ["so_van_ban_den", "ten_van_ban", "nhom_van_ban", "ai_ket_qua_nhanh"], "limit": 10, "order": "id desc"})
        for item in den:
            docs.append({"direction": "Đến", "so": item.get("so_van_ban_den"), "ten": item.get("ten_van_ban"), "nhom": item.get("nhom_van_ban"), "ai": item.get("ai_ket_qua_nhanh")})
        di = _execute("van_ban_di", "search_read", [[]], {"fields": ["so_van_ban_di", "ten_van_ban", "nhom_van_ban", "ai_ket_qua_nhanh"], "limit": 10, "order": "id desc"})
        for item in di:
            docs.append({"direction": "Đi", "so": item.get("so_van_ban_di"), "ten": item.get("ten_van_ban"), "nhom": item.get("nhom_van_ban"), "ai": item.get("ai_ket_qua_nhanh")})
        return docs[:20]

    def create_customer(self, payload):
        name = (payload.get("name") or "").strip()
        if not name:
            raise RuntimeError("Tên khách hàng không được để trống.")
        customer_id = _execute("res.partner", "create", [{"name": name, "ma_khach_hang": _external_customer_code(), "is_khach_hang": True, "phone": payload.get("phone") or "", "email": payload.get("email") or "", "muc_do_uu_tien": payload.get("priority") or "trung_binh", "trang_thai_cham_soc": "moi", "nguon_khach_hang": "Ứng dụng bên ngoài", "ghi_chu_ho_so": payload.get("note") or "Tạo từ ứng dụng bên ngoài qua XML-RPC."}])
        if isinstance(customer_id, list):
            customer_id = customer_id[0]
        data = _execute("res.partner", "read", [[customer_id]], {"fields": ["name", "ma_khach_hang"]})[0]
        self.send_json({"id": customer_id, "name": data.get("name"), "code": data.get("ma_khach_hang")})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (time.strftime("%H:%M:%S"), fmt % args))


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print("External app đang chạy tại http://localhost:%s" % PORT)
    print("Dùng Ctrl+C để tắt.")
    server.serve_forever()

