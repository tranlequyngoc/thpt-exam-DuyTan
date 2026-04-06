# -*- coding: utf-8 -*-
import sys, os, hashlib, json
sys.path.insert(0, r"C:\Users\LENOVO\Desktop\XExam - Copy")
os.chdir(r"C:\Users\LENOVO\Desktop\XExam - Copy")
import app
app.init_db()
c = app.get_db()
admin = c.execute("SELECT id FROM users WHERE username='admin'").fetchone()
admin_id = admin['id'] if admin else 1

def mk(content, a='', b='', cc='', d='', ans='', t='mc'):
    return {'c': content, 'a': a, 'b': b, 'cc': cc, 'd': d, 'ans': ans, 't': t}

# ============================================================
# HOA HOC 12 - DIEN PHAN + KIM LOAI (4 de x 20 cau = 80 cau)
# ============================================================
hoa1 = [
mk('Dien phan la qua trinh oxi hoa-khu xay ra tren be mat dien cuc khi co dong dien nao di qua?','1 chieu','2 chieu','Xoay chieu','Khong can dong dien','A'),
mk('Trong dien phan nong chay, anion di chuyen ve:','Anode, bi oxi hoa','Anode, bi khu','Cathode, bi khu','Cathode, bi oxi hoa','A'),
mk('Trong dien phan nong chay, cation di chuyen ve:','Anode, bi khu','Anode, bi oxi hoa','Cathode, bi khu','Cathode, bi oxi hoa','C'),
mk('Khi dien phan NaCl nong chay, o anode xay ra:','Oxi hoa ion Cl-','Oxi hoa ion Na+','Khu ion Cl-','Khu ion Na+','A'),
mk('San pham dien phan nong chay MgCl2:','MgO + HCl','Mg + H2 + Cl2','MgCl2 + H2O','Mg + Cl2','D'),
mk('Dien phan NaCl nong chay va dd NaCl deu thu duoc o anode:','O2','Na','Cl2','H2','C'),
mk('Dien phan CaCl2 nong chay, o cathode xay ra:','OxH Ca2+','Khu Ca2+','OxH Cl-','Khu Cl-','B'),
mk('Dien phan NaOH nong chay, o anode xay ra:','Na+ + e -> Na','4OH- -> O2 + 2H2O + 4e','2OH- -> H2 + O2 + 2e','2O2- -> O2 + 4e','B'),
mk('Thu tu dien phan ion KL o cathode:','The dien cuc am hon DP truoc','The dien cuc duong hon DP truoc','The dien cuc duong hon DP truoc o anode','The dien cuc am hon DP truoc o anode','B'),
mk('Dien phan dd CuSO4 dien cuc tro, o anode:','Cu2+ + 2e -> Cu','2H2O -> 4H+ + O2 + 4e','Cu -> Cu2+ + 2e','2H2O + 2e -> H2 + 2OH-','B'),
mk('Dien phan dd NaCl co mang ngan, o anode va cathode:','Cl2 va NaOH+H2','Na va Cl2','Cl2 va Na','NaOH va H2','A'),
mk('Dien phan dd CuSO4, ion DP dau tien o cathode:','Cu2+','H+ cua nuoc','SO42-','OH- cua nuoc','A'),
mk('Dien phan dd NaCl, o cathode xay ra:','OxH Na+','OxH H2O','Khu H2O','Khu Na+','C'),
mk('Dien phan dd Cu(NO3)2 dien cuc tro, o anode:','H2O -> O2 + 2H+ + 2e','2H2O + 2e -> H2 + 2OH-','Cu -> Cu2+ + 2e','Cu2+ + 2e -> Cu','A'),
mk('Ion KL nao bi dien phan trong dd (dien cuc graphite)?','Na+','Cu2+','Ca2+','K+','B'),
mk('Dien phan dd AgNO3, o cathode:','2H2O -> O2 + 4H+','Ag+ + e -> Ag','Ag -> Ag+ + e','2H2O + 2e -> H2 + 2OH-','B','es'),
mk('Khi DP dd CuSO4, mau xanh nhat dan vi:','H2 khu mau','DD pha loang','Cu2+ bi khu thanh Cu','Cu2+ tang','C','es'),
mk('Phan ung o cathode khi DP Al2O3 nong chay:','Al3+ + 3e -> Al','2O2- -> O2 + 4e','Al -> Al3+ + 3e','2O2- + 4e -> O2','A','es'),
mk('Khi DP dd NaCl+NaBr, o anode OxH dau tien:','2H2O -> O2 + 4H+ + 4e','2Cl- -> Cl2 + 2e','2Br- -> Br2 + 2e','Na -> Na+ + e','C','es'),
mk('Thu tu DP o cathode dd Fe2+,Fe3+,Cu2+,Cl-:','Fe2+,Fe3+,Cu2+','Fe3+,Cu2+,Fe2+','Fe2+,Cu2+,Fe3+','Cu2+,Fe3+,Fe2+','B','es'),
]

hoa2 = [
mk('Cau hinh e Mg (Z=12) lop ngoai cung:','3s1','3s2p1','3s2','3p1','C'),
mk('Nguyen to nao co so e lop ngoai cung it nhat: C,Li,O,F?','C (Z=6)','Li (Z=3)','O (Z=8)','F (Z=9)','B'),
mk('Nguyen to nao co 3e lop ngoai cung: Na,Al,Ca,Fe?','11Na','13Al','20Ca','26Fe','B'),
mk('Thanh phan KHONG co trong mang tinh the KL:','Ion KL','Electron','Nguyen tu KL','Anion goc acid','D'),
mk('Kim loai co nhiet do nong chay thap nhat:','Au','Cu','Na','Hg','D'),
mk('Kim loai co do cung lon nhat:','Cr','Al','Mg','Na','A'),
mk('Kim loai co nhiet do nong chay cao nhat:','Na','Pb','Hg','W','D'),
mk('Kim loai co khoi luong rieng nho nhat:','Na','Li','Fe','Al','B'),
mk('Electron tu do trong mang tinh the KL chuyen dong:','Theo quy dao XD','Xung quanh vi tri XD','Tu do trong toan mang','Trong khu vuc nhat dinh','C'),
mk('Lien ket trong mang tinh the KL la:','Ion','Cong hoa tri','Van der Waals','Kim loai','D'),
mk('Kim loai Au duoc dat mong, keo soi vi co:','Tinh deo cao','Tinh dan dien','Do cung cao','Nhiet do nc cao','A'),
mk('Kim loai o trang thai long o dieu kien thuong:','Na','Hg','Al','Fe','B'),
mk('Cu, Al lam day dan dien vi co:','Nhiet do nc cao','Tinh dan nhiet','Tinh dan dien','Anh kim','C'),
mk('W lam day toc bong den vi co:','Nhiet do nc cao','Dan dien tot','Tinh deo','Do cung','A'),
mk('Tinh chat VL chung cua KL:','Deo,dan dien,nc cao','Deo,dan dien nhiet,anh kim','Dan dien nhiet,KLR lon,anh kim','Deo,anh kim,rat cung','B'),
mk('Thu tu dan dien giam dan cua KL?','Au>Ag>Cu>Fe','Ag>Cu>Au>Fe','Au>Ag>Cu>Al','Cu>Au>Ag>Al','B','es'),
mk('Nguyen tac dieu che KL la gi?','Cho hop chat + chat khu','OxH ion KL','Khu ion KL thanh nguyen tu','Hop chat + chat OxH','C','es'),
mk('Day KL dieu che bang DP hop chat nong chay:','Na,Ca,Al','Na,Ca,Zn','Na,Cu,Al','Fe,Ca,Al','A','es'),
mk('Oxide bi H2 khu o nhiet do cao tao KL:','CaO','Al2O3','K2O','CuO','D','es'),
mk('Phuong phap thich hop dieu che Mg tu MgCl2:','K khu trong dd','DP MgCl2 nong chay','DP dd MgCl2','Nhiet phan','B','es'),
]

hoa3 = [
mk('Cau hinh e Cu (Z=29) o trang thai co ban:','[Ar]3d9 4s2','[Ar]3d10 4s1','[Ar]4s2 3d9','[Ar]3d8 4s2','B'),
mk('Cau hinh e ion Fe2+ (Z=26):','[Ar]3d5','[Ar]3d6','[Ar]3d4 4s2','[Ar]3d6 4s2','B'),
mk('Thu tu tang dan ban kinh KL kiem:','Li<Na<K<Rb<Cs','Cs<Rb<K<Na<Li','Li<K<Na<Rb<Cs','Li<Na<K<Cs<Rb','A'),
mk('Kieu mang tinh the do dac khit nho nhat:','Lap phuong tam khoi','Lap phuong tam mat','Luc phuong','LP tam khoi + tam mat','A'),
mk('Nguyen tu Al co so e lop ngoai cung:','1','2','3','5','C'),
mk('Kim loai deo nhat:','Gold','Silver','Copper','Aluminium','A'),
mk('Nguyen to Z=24 o vi tri BTH:','CK4 nhom IA','CK4 nhom IB','CK4 nhom VB','CK4 nhom VIB','D'),
mk('Electron tu do phan xa tia sang tao nen:','Tinh dan dien','Tinh deo','Tinh dan nhiet','Anh kim','D'),
mk('Day cau hinh e cua nguyen tu KL la 3,4,7. So cau hinh KL:','5','3','2','4','B'),
mk('Thu tu giam nhuong e:','Na>Mg>Al>K','Na>Mg>K>Al','K>Na>Al>Mg','K>Na>Mg>Al','D'),
mk('So sanh voi phi kim cung chu ky, KL thuong co:','Nhieu e ngoai cung hon','Ban kinh lon hon','Do am dien lon hon','De nhan e hon','B'),
mk('2 KL dieu che bang PP thuy luyen:','Al va Mg','Cu va Ag','Na va Fe','Mg va Zn','B'),
mk('Day KL dieu che bang DP dd muoi:','Fe,Cu,Ag','Al,Fe,Cu','Li,Ag,Sn','Al,Fe,Cr','A'),
mk('Kim loai o dang don chat trong tu nhien:','Dong','Kem','Vang','Bac','C'),
mk('Chat khong khu duoc Fe2O3 o nhiet do cao:','Cu','CO','H2','Al','A'),
mk('Thanh phan chinh quang hematite:','Iron(II) oxide','Iron(III) oxide','Iron','Iron(II) sulfide','B','es'),
mk('Hai KL co the DP dung dich la:','Al va Mg','Cu va Ag','Na va Fe','Ca va K','B','es'),
mk('Phan ung nao KHONG dieu che Cu:','Fe + CuSO4','Na + CuSO4','DP dd CuSO4','H2 + CuO','B','es'),
mk('Oxide KL bi khu boi CO o nhiet do cao:','Al2O3','CaO','K2O','CuO','D','es'),
mk('O nhiet do cao, H2 khu duoc oxide:','CaO','Al2O3','K2O','Fe2O3','D','es'),
]

# ============================================================
# LICH SU 12 - DOI NGOAI VN + HO CHI MINH (3 de x 20 cau = 60)
# ============================================================
ls1 = [
mk('Muc dich doi ngoai VN dau TK XX la:','Tranh thu su ung ho quoc te cho CMVN','Mo rong lanh tho','Phat trien kinh te','Hop tac quan su','A'),
mk('Nguyen Ai Quoc sang Phap nam:','1911','1920','1930','1945','A'),
mk('NAQ tham gia sang lap to chuc nao o Phap?','Dang CS Phap','Dang XH Phap','Quoc te CS','Hoi VNCMTN','A'),
mk('Hoat dong doi ngoai VN giai doan 1945-1954 huong toi:','Tranh thu cong nhan doc lap','Mo rong lanh tho','Hop tac kinh te','Gia nhap LHQ','A'),
mk('Hiep dinh Geneve 1954 cong nhan:','Doc lap chu quyen VN','VN thong nhat','VN la thuoc dia Phap','My rut quan','A'),
mk('Doi ngoai VN thoi ky chong My huong toi:','Tranh thu ung ho XHCN va hoa binh TG','Hop tac voi My','Gia nhap NATO','Trung lap','A'),
mk('VN gia nhap ASEAN nam:','1967','1975','1995','2000','C'),
mk('VN gia nhap LHQ nam:','1945','1975','1977','1986','C'),
mk('Duong loi doi ngoai VN tu 1986:','Da phuong hoa, da dang hoa','Chi hop tac XHCN','Dong cua kinh te','Chi hop tac voi My','A'),
mk('VN gia nhap WTO nam:','2000','2004','2007','2010','C'),
mk('Que huong Ho Chi Minh la:','Ha Tinh','Nghe An','Thanh Hoa','Hue','B'),
mk('Nam sinh cua HCM:','1880','1890','1895','1900','B'),
mk('HCM ra di tim duong cuu nuoc nam:','1905','1911','1920','1930','B'),
mk('HCM doc Tuyen ngon doc lap ngay:','19/8/1945','2/9/1945','22/12/1946','7/5/1954','B'),
mk('HCM sang lap Dang CSVN ngay:','3/2/1930','19/5/1930','2/9/1945','22/12/1944','A'),
mk('Con duong cuu nuoc HCM lua chon la:','CM vo san','CM tu san','Cai cach','Bao luc','A','es'),
mk('Y nghia thanh lap DCSVN 1930? (Ngan gon)','','','','','Cham dut khung hoang ve duong loi va giai cap lanh dao CM VN','es'),
mk('Vai tro HCM trong CM thang 8/1945?','','','','','Lanh dao toan dan tong khoi nghia gianh chinh quyen','es'),
mk('Tuyen ngon doc lap khang dinh quyen gi?','','','','','Quyen doc lap tu do cua dan toc VN','es'),
mk('Bai hoc tu cuoc doi HCM cho ban than?','','','','','Can hoc tap suot doi, yeu nuoc va phuc vu nhan dan','es'),
]

ls2 = [
mk('HCM gui Den Versailles yeu cau gi (1919)?','Cac quyen tu do cho nhan dan VN','Doc lap hoan toan','Lien bang Dong Duong','Rut quan Phap','A'),
mk('HCM doc Luan cuong Lenin nam:','1917','1920','1925','1930','B'),
mk('Hoi VNCMTN do HCM sang lap nam:','1920','1925','1930','1941','B'),
mk('HCM viet Tuyen ngon doc lap dua tren:','Tuyen ngon NQ My + NQ Phap','Hien phap Phap','Luat quoc te','Hiep uoc Versailles','A'),
mk('HCM la Chu tich nuoc VNDCCH tu nam:','1930','1941','1945','1946','C'),
mk('Duong loi khang chien chong Phap do HCM de ra:','Toan dan, toan dien, lau dai, tu luc canh sinh','Danh nhanh thang nhanh','Chi dua vao vien tro','Hoa binh thuong luong','A'),
mk('HCM gui thu cho HS nhan ngay khai truong 9/1945 noi:','Non song VN co tro nen ve vang hay khong...','Hoc de lam viec','Hoc de thi','Hoc de kinh doanh','A'),
mk('HCM mat nam:','1965','1968','1969','1975','C'),
mk('Di chuc HCM noi ve:','Doan ket trong Dang va nhan dan','Chien tranh','Kinh te','Ngoai giao','A'),
mk('UNESCO vinh danh HCM la:','Anh hung GPDT, nha van hoa kiet xuat','Nha khoa hoc','Nha kinh te','Nha quan su','A'),
mk('HCM thanh lap Mat tran Viet Minh nam:','1930','1936','1941','1945','C'),
mk('Duong loi KC chong My cua HCM:','Danh cho My rut, danh cho Nguy nhao','Hoa binh','Thuong luong','Chi dua vao LX','A'),
mk('HCM viet "Ban an che do thuc dan Phap" nam:','1920','1925','1930','1935','B'),
mk('Noi dung co ban con duong cuu nuoc HCM:','Doc lap DT gan voi CNXH','Doc lap DT','Chi CNXH','Chi doc lap','A'),
mk('Vai tro HCM trong viec thanh lap DCSVN:','Trieu tap hoi nghi hop nhat 3 to chuc CS','Chi dao tu xa','Khong truc tiep tham gia','Lanh dao tu nuoc ngoai','A'),
mk('Phan tich diem noi bat duong loi KC chong Phap?','','','','','Toan dan, toan dien, truong ky, tu luc canh sinh','es'),
mk('Vai tro HCM doi voi su nghiep GPDT?','','','','','Tim ra con duong cuu nuoc dung dan, lanh dao CM thanh cong','es'),
mk('Tai sao HCM chon con duong CM vo san?','','','','','Vi chi co CM vo san moi giai phong triet de cac DT bi ap buc','es'),
mk('Y nghia cua viec HCM doc Tuyen ngon doc lap?','','','','','Khai sinh nuoc VNDCCH, khang dinh quyen doc lap tu do','es'),
mk('Bai hoc tu HCM ve tinh than tu hoc?','','','','','Can tu hoc suot doi, hoc o moi noi moi luc','es'),
]

# ============================================================
# TIN HOC 12 - HOI THAO + KET NOI + TRANG WEB (3 de x 20 = 60)
# ============================================================
tin1 = [
mk('Muc tieu chinh hoi thao huong nghiep:','Gioi thieu CN moi','Giup HS chon nghe phu hop','Giai tri','The thao','B'),
mk('Yeu to quan trong nhat khi lap KH hoi thao:','Chon ngay gio','Dia diem','Xac dinh doi tuong tham gia','Moi dien gia','C'),
mk('Yeu to quan trong nhat khi XD bai trinh bay:','Hinh anh sinh dong','Noi dung ro rang de hieu','Thoi luong','Phong chu bat mat','B'),
mk('Dieu can xac dinh dau tien khi lap KH hoi thao:','Chu de hoi thao','Danh sach dien gia','Chi phi','So luong nguoi','A'),
mk('Nguoi dieu phoi hoi thao nen:','Gioi thieu dien gia','Dieu khien TG va lich trinh','Tuong tac voi khan gia','Tao khong khi thoai mai','B'),
mk('PP danh gia ket qua hoi thao hieu qua nhat:','Khao sat phan hoi','So luong nguoi','Thoi luong','So cau hoi','A'),
mk('Cong ket noi thiet bi hien thi voi may tinh:','USB','HDMI','Bluetooth','Ethernet','B'),
mk('De ket noi BT may tinh-dien thoai, can:','Ghep doi','Bat BT ca hai','Xac nhan ket noi','Truyen file','B'),
mk('Nha thong minh dieu khien qua:','Cap tin hieu','Wi-Fi','Bluetooth va Wi-Fi','Chi cap','C'),
mk('Ket noi BT thuong dung de:','Ket noi khoang cach xa','Chia se du lieu khoang cach ngan','Ket noi Internet','Chi may in','B'),
mk('Ket noi BT thuoc loai:','Co day','Ket noi xa','Ket noi gan','Cap tin hieu','C'),
mk('Dac diem nha thong minh:','Hoan toan thu cong','Tu dong hoa va kiem soat tu xa','Khong can Internet','Chi dung HDMI','B'),
mk('Cap Ethernet thuong dung de:','Ket noi man hinh','Truyen du lieu qua mang LAN','Ket noi luu tru','Truyen am thanh','B'),
mk('Phan nao chua thong tin ban quyen, mang xa hoi:','Dau trang','Than trang','Chan trang','Thong bao','C'),
mk('Phan nao cua trang web nhu trang bia sach:','Than trang','Dau trang','Chan trang','Thong bao','B'),
mk('Buoc dau tien xay dung trang web:','Thiet ke giao dien','Dinh hinh y tuong','Chon phan mem','Chuan bi tu lieu','B','es'),
mk('Chon bang mau trang web can chu y:','Tuong phan manh','1 mau duy nhat','Tuong phan nhe nhang hai hoa','Mau ngau nhien','C','es'),
mk('Moi trang web day du gom may phan chinh?','2','3','4','5','B','es'),
mk('Favicon la gi?','Bieu tuong dai dien trang web tren tab','Logo chinh','Hinh nen','Menu','A','es'),
mk('Phan mem Google ho tro lam trang web:','Google Travel','Google Drive','Google Sites','Google Jamboard','C','es'),
]

tin2 = [
mk('De dinh hinh y tuong trang web can:','Xay dung kien truc ND','Lam logo','Chon phan mem','Xac dinh muc dich va doi tuong','D'),
mk('Thiet ke my thuat trang web gom:','Chi chon mau','Chon bang mau phong chu bieu tuong','Chi lam logo','Chi chon anh','B'),
mk('Phan than trang web chua:','Noi dung chinh','Chi logo','Chi menu','Chi lien ket','A'),
mk('Thanh dieu huong (menu) thuong o:','Chan trang','Than trang','Dau trang','Khong co','C'),
mk('Khi thiet ke header, dieu quan trong:','Dat toan bo ND vao dau trang','Sap xep ro rang de su dung','Them nhieu hieu ung','Chi dung 1 mau','B'),
mk('Thanh tim kiem trang web thuong o:','Chan trang','Than trang','Dau trang','Khong can','C'),
mk('Viec chuan bi tu lieu cho trang web:','Chi lam 1 lan','Keo dai suot du an','Khong can thiet','Chi o cuoi','B'),
mk('Kieu chu dam thuong dung de:','Trang tri','Phan biet tu ngu cau chu','Lam dep','Khong co y nghia','B'),
mk('Nhà thong minh su dung thiet bi:','Chi co day','Ket noi voi nhau qua mang','Hoan toan doc lap','Khong can dien','B'),
mk('HDMI thuong dung truyen:','Du lieu mang','Tin hieu hinh anh va am thanh','Tin hieu Bluetooth','File van ban','B'),
mk('Wifi la phuong thuc ket noi:','Co day','Khong day','Chi noi bo','Chi ngoai troi','B'),
mk('Khi chieu PPT tu laptop len TV, day bi hong, dung:','HDMI','USB','Wi-Fi (Miracast/Chromecast)','Ethernet','C'),
mk('He thong den thong minh DK bang DT khi khong o nha, dung:','Bluetooth','Wi-Fi + Internet','Cap USB','Cap Ethernet','B'),
mk('IPv4 dung bao nhieu bit:','16','32','64','128','B'),
mk('1 Byte bang bao nhieu Bit:','4','8','16','32','B'),
mk('Website hoc tap nen uu tien:','Sao chep bo cuc trang khac','Thiet ke phu hop doi tuong hoc','Them nhieu hieu ung','Chi dung hinh anh','B','es'),
mk('Danh gia rui ro trang web nen thuc hien khi nao:','Chi o cuoi','Ngay tu dau','Khong can','Sau khi xong','B','es'),
mk('Lien ket hover giup:','Tang tinh truc quan va trai nghiem','Giam toc do','Tang dung luong','Khong co tac dung','A','es'),
mk('Khi XD trang web ca nhan, hinh anh nen:','Theo so thich','Can nhac muc tieu truyen tai','Dung anh bat ky','Khong can hinh','B','es'),
mk('Menu dropdown la gi:','Menu co dinh','Menu tha xuong khi hover/click','Menu an','Menu doc','B','es'),
]

all_data = [
('De on CK2 - Hoa 12: Dien phan (De 1)', 'Hoa hoc', 50, hoa1),
('De on CK2 - Hoa 12: Kim loai (De 2)', 'Hoa hoc', 50, hoa2),
('De on CK2 - Hoa 12: Tong hop (De 3)', 'Hoa hoc', 50, hoa3),
('De on CK2 - Lich su 12: Doi ngoai + HCM (De 1)', 'Lich su', 50, ls1),
('De on CK2 - Lich su 12: HCM anh hung GPDT (De 2)', 'Lich su', 50, ls2),
('De on CK2 - Tin hoc 12: Hoi thao + Web (De 1)', 'Tin hoc', 45, tin1),
('De on CK2 - Tin hoc 12: KN thiet bi + Web (De 2)', 'Tin hoc', 45, tin2),
]

created = 0
total_q = 0
for title, subject, time_limit, questions in all_data:
    existing = c.execute("SELECT id FROM exams WHERE title=?", (title,)).fetchone()
    if existing:
        print("SKIP: " + title)
        continue
    cur = c.execute("INSERT INTO exams(title,subject,description,time_limit,total_score,created_by,is_open,max_attempts,shuffle_questions,teacher_approved) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (title, subject, "De on tap CK2 lop 12 - Truong THPT Duy Tan - Co dap an", time_limit, 10, admin_id, 1, 999, 1, 1))
    eid = cur.lastrowid
    for i, q in enumerate(questions, 1):
        qtype = 'multiple_choice' if q['t'] == 'mc' else 'essay'
        score = 0.5 if qtype == 'multiple_choice' else 1.0
        c.execute("INSERT INTO questions(exam_id,question_number,type,content,option_a,option_b,option_c,option_d,correct_answer,score) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (eid, i, qtype, q['c'], q.get('a',''), q.get('b',''), q.get('cc',''), q.get('d',''), q.get('ans',''), score))
    created += 1
    total_q += len(questions)
    print("OK: " + title + " (" + str(len(questions)) + " cau) ID=" + str(eid))

c.commit()
c.close()
print("\nTONG: " + str(created) + " de thi, " + str(total_q) + " cau hoi!")
