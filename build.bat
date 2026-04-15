pyinstaller --noconfirm --clean --windowed --onefile ^
--name "Quick meet link" ^
--icon "img\logo-app.png" ^
--add-data "img;img" ^
--add-data "tesseract;tesseract" ^
--hidden-import=pytesseract ^
--hidden-import=PIL ^
--hidden-import=PIL._tkinter_finder ^
app.py