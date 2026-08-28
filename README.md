# dars-taqsimoti-tuzuvchi

Dars taqsimoti tuzuvchi dastur (Python + tkinter).

## Imkoniyatlar

- CSV fayldan fanlar va soatlarni yuklash (`Fan nomi,Soat`)
- 5 kunlik (Dushanba-Juma), har kuni maksimal 6 soatlik jadval tuzish
- Matematika (Algebra/Geometriya) va Ingliz tili uchun ketma-ket 2 soatlik bloklarni ustuvor joylashtirish
- Ushbu ustuvor fanlarni imkon qadar ertaroq (kun boshida) joylashtirish
- "Qaytadan yaratish" bilan yangi (oldingisidan farqli) variant hosil qilish
- Jadvalni CSV yoki PDF formatida yuklab olish

## Ishga tushirish

```bash
python app.py
```

## CSV namunasi

```csv
Matematika (Algebra),4
Matematika (Geometriya),4
Ingliz tili,3
Fizika,3
Kimyo,2
Tarix,2
```

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```
