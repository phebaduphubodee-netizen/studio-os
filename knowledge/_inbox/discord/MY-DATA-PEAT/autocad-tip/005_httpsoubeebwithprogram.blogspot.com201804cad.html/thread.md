---
source: discord
server: MY DATA PEAT
channel: autocad-tip
thread: "https://oubeebwithprogram.blogspot.com/2018/04/cad.html"
thread_id: 1274183881825849354
tags: []
created: 2024-08-17
pulled: 2026-07-03T18:29Z
tier: REFERENCE
---

# https://oubeebwithprogram.blogspot.com/2018/04/cad.html

## [1] Peat — 2024-08-17 01:51
คำสั่งและโค้ดที่"เรา"ใช้บ่อย รวมไว้เพื่อให้กลับมาหาง่ายๆหากลืม
เสิร์ชหาเอานะ

Code CAD

%%189 = 1/2
%%188 = 1/4
%%p = +- (บวกลบ)
%%d = ํ (องศา)
%%c = o/ (เส้นผ่านศูนย์กลาง)

คำสั่ง CAD
TCASE = TEXTCASE = ใช้ออกคำสั่งกับอักษร เช่น ปรับทั้งหมดเป็น Capital
FIELD = บอกเลขพื้นที่ในกรอบที่กำหนด Update ได้หากกรอบขยับ *แต่ต้องกด REA
UCS = หมุนแกน
XCLIPFRAME = 0,1,... = การแสดงเส้นกรอบ Xclip
EDGEMODE = 0,1 = ใช้เวลา Extend/Trim ว่าเส้นต้องตัดกันจริงๆไหม
TCOUNT = รันเลข 1,2,3,4,... (เลขตั้งต้น,ระยะที่เพิ่ม/ลด) *มีประโยชน์มากถ้าทำคล่องๆ
DDA = ทำลายความสัมพันธ์ Dimension
BO = BOUNDARY
PSLTSCALE = 0 (เส้นใน Model กับ Paper Relateกัน), 1 (ไม่Relateกัน)
DWGCONVERT = ปรับรุ่น AutoCAD Version ต่างๆ (ได้ทั้งปรับขึ้นและลง)

อื่นๆ
- เพิ่ม .ctb
Home(เครื่องหมายCADมุมซ้ายบน) > Print > Manage Plotters
(หรือเข้าทาง Control Panel > Autodesk Plot Style Manager)
- แบ่งหน้าทำงาน
View > Viewports
(บางทีใช้วิธีกด Alt+V 2ครั้ง)
