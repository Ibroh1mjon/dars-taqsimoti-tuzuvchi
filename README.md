# dars-taqsimoti-tuzuvchi

Dars taqsimoti tuzuvchi dastur (Python + tkinter).

## Imkoniyatlar

- XLSX fayldan o'qituvchi, fan va sinf taqsimotini yuklash
- Haftaning to'liq jadvalini sinflar va kunlar bo'yicha ko'rsatish
- Har bir sinf-kun katagida 6 ta dars, fan nomi va kichik yozuvda o'qituvchi nomini ko'rsatish
- Matematika (Algebra/Geometriya) va Ingliz tili uchun ketma-ket 2 soatlik bloklarni ustuvor joylashtirish
- Ushbu ustuvor fanlarni imkon qadar ertaroq (kun boshida) joylashtirish
- "Qaytadan yaratish" bilan yangi (oldingisidan farqli) variant hosil qilish
- Faqat `.xlsx` fayllar qabul qilinadi

## Ishga tushirish

```bash
python app.py
```

## XLSX formati

Birinchi jadval qatorida `O'qituvchi`, `Fan` (yoki `Fan\Sinf`) va sinf ustunlari
(`1A`, `1B`, `1`, ...) bo'lishi kerak. Har bir keyingi qatorda sinf katagidagi
son shu fan uchun haftalik dars soatlarini bildiradi.

## Test

```bash
python -m unittest discover -s tests -p "test_*.py"
```
