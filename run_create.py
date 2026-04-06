import sys, os, json, hashlib
sys.path.insert(0, r"C:\Users\LENOVO\Desktop\XExam - Copy")
os.chdir(r"C:\Users\LENOVO\Desktop\XExam - Copy")
exec(open('create_all_exams.py','r',encoding='utf-8').read().replace('\n    ','\n'))
