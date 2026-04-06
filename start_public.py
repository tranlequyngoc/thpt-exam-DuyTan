# -*- coding: utf-8 -*-
"""
X-EXAM - Khoi dong server + mo public voi ngrok
Chay: python start_public.py
"""
import os, sys, threading, time, webbrowser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def start_server():
    import app as xapp
    xapp.init_db()
    print("[SERVER] Khoi dong Flask tren port 5000...")
    xapp.app.run(debug=False, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)

def start_ngrok():
    time.sleep(3)
    try:
        from pyngrok import ngrok
        print("[NGROK] Dang tao tunnel cong khai...")

        tunnel = ngrok.connect(5000, proto="http")
        public_url = tunnel.public_url

        print()
        print("=" * 60)
        print("  [OK] X-EXAM DA ONLINE! CHIA SE LINK NAY:")
        print()
        print("   >>> " + str(public_url) + " <<<")
        print()
        print("  Bat ky ai co link tren deu truy cap duoc!")
        print()
        print("  Tren may tinh nay: http://localhost:5000")
        print("=" * 60)
        print()
        print("  [!] Giu cua so nay mo de server chay lien tuc.")
        print("  [!] Dong cua so = tat server = link het hieu luc.")
        print()

        webbrowser.open('http://localhost:5000')

        ngrok_process = ngrok.get_ngrok_process()
        try:
            ngrok_process.proc.wait()
        except KeyboardInterrupt:
            print("\n[*] Dang tat server...")
            ngrok.kill()

    except ImportError:
        print("[LOI] Chua cai pyngrok! Chay: pip install pyngrok")
        webbrowser.open('http://localhost:5000')

    except Exception as e:
        err = str(e)
        print("\n[NGROK LOI] " + err + "\n")

        if "authtoken" in err.lower() or "ERR_NGROK_105" in err or "authentication" in err.lower() or "401" in err:
            print("=" * 60)
            print("  CHUA CO AUTHTOKEN NGROK - Lam theo cac buoc sau:")
            print()
            print("  Buoc 1: Mo trinh duyet, vao dia chi:")
            print("          https://dashboard.ngrok.com/signup")
            print("          (Dang ky tai khoan MIEN PHI)")
            print()
            print("  Buoc 2: Sau khi dang nhap, vao:")
            print("          https://dashboard.ngrok.com/get-started/your-authtoken")
            print()
            print("  Buoc 3: Copy token, mo CMD va chay lenh:")
            print("          ngrok config add-authtoken <DAN_TOKEN_VAO_DAY>")
            print()
            print("  Buoc 4: Chay lai file start_public.py")
            print("=" * 60)
        else:
            print("[TIP] Thu chay lai hoac kiem tra ket noi mang.")

        print("\n[LOCAL] Van dung duoc tren may nay: http://localhost:5000")
        webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    print()
    print("=" * 60)
    print("  X-EXAM v5.0 - He thong luyen thi THPT")
    print("  TK demo: admin / admin123")
    print("           hocsinh / 123456")
    print("=" * 60)
    print()

    t = threading.Thread(target=start_ngrok, daemon=True)
    t.start()
    start_server()
