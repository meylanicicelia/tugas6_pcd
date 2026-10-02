# Analisis

## 1. Perbandingan metode thresholding
Hasil pada ROI Dekan, tiap kolom adalah jumlah piksel foreground setelah morphology (lihat tabel di README dan `results/summary.csv`).

- **Global (T=128)**: satu nilai untuk semua citra. Tinta tanda tangan pada ijazah ini berintensitas sekitar 100-200, sehingga sebagian besar berada di atas 128 dan hilang (0-294 piksel, kecuali `faded` 1005 piksel karena seluruh citra lebih gelap). Metode ini tidak memakai informasi kecerahan citra.
- **Otsu**: T dipilih otomatis dari histogram, nilainya 141 pada `faded` dan 222 pada `lowcontrast`. Karena itu hasilnya stabil (2632-3037 piksel). Kelemahannya, Otsu selalu membagi histogram menjadi dua kelas walaupun ROI hanya berisi noise. Karena itu ditambahkan pemeriksaan kontras (`MIN_CONTRAST=15`): jika median latar dikurangi rata-rata foreground lebih kecil dari 15, foreground dianggap kosong. Pada ROI kosong selisihnya 0-2, pada tanda tangan paling pudar 31.
- **Adaptive (Gaussian, blok 31, C=8)**: ambang dihitung per lingkungan lokal, cocok untuk pencahayaan tidak merata. Hasilnya mirip Otsu (1125-3330 piksel) dan sedikit lebih rendah pada citra pudar (`faded`: 2183 piksel pada ROI Dekan) karena kontras lokal kecil.

Kesimpulan: Otsu dan Adaptive cocok untuk dokumen dengan kecerahan berubah-ubah, sedangkan Global bergantung pada pemilihan T secara manual.

## 2. Peran morphology
- **Opening** (erosi lalu dilasi, elemen elips 3x3) menghapus bintik kecil akibat noise dan artefak JPEG.
- **Closing** (dilasi lalu erosi, elemen elips 5x5) menyambung goresan tipis yang terputus oleh threshold.
- Komponen terhubung di bawah 40 piksel dibuang agar sisa bintik tidak dihitung sebagai tanda tangan.

## 3. Mengapa thresholding diperlukan sebelum analisis keberadaan tanda tangan?
Pertanyaan yang dijawab sistem bersifat biner: ada tinta tanda tangan atau tidak. Citra grayscale punya 256 level intensitas dan masih bercampur dengan kertas, bayangan, dan noise. Thresholding memisahkan tinta (foreground) dari kertas (background) menjadi citra biner. Dari citra biner itu kita bisa menghitung piksel foreground, mengukur bounding box, dan menghitung komponen terhubung. Tanpa langkah ini, rata-rata intensitas ROI akan lebih ditentukan oleh warna dan kecerahan kertas daripada oleh ada tidaknya tanda tangan. Hasil binarisasi juga membuat satu aturan sederhana (piksel dan ukuran) bisa dipakai pada citra dengan kondisi berbeda.

## 4. Masalah jika threshold terlalu tinggi atau terlalu rendah
Gambar acuan: `results/threshold_sweep.png` (ROI Dekan, citra highquality).

| T | Piksel foreground | Kondisi |
|---|---|---|
| 40 | 0 | terlalu rendah: tanda tangan hilang total |
| 100 | 19 | terlalu rendah: hanya bintik |
| 160 | 555 | goresan putus-putus |
| 200 | 2088 | mendekati bentuk tanda tangan |
| 235 | 4582 | terlalu tinggi: goresan menebal, teks sekitar ikut masuk |

- **Terlalu tinggi**: piksel kertas, noise, bayangan, dan teks cetak di tepi ROI ikut menjadi foreground. Goresan menebal dan saling menempel, jumlah piksel membengkak, dan area kosong bisa dianggap bertanda tangan (**false positive**).
- **Terlalu rendah**: hanya piksel yang sangat gelap yang lolos. Tinta tipis atau pudar hilang, goresan terputus, dan tanda tangan asli bisa dianggap tidak ada (**false negative**). Ini terjadi pada metode Global: 17 dari 18 kasus bertanda tangan terlewat.

Karena kecerahan citra berbeda-beda (T Otsu berkisar 141-222), threshold otomatis seperti Otsu dan adaptive lebih aman daripada satu nilai tetap.
