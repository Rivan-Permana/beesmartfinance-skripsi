# Audit regresi UI lokal — 18 Oktober 2026

Status: **Approve untuk cakupan yang diperiksa**, bukan persetujuan rilis. Implementasi modul berikutnya ditahan selama audit ini. Source frontend diperbaiki; tidak ada deployment, perubahan backend, migrasi, atau mutasi transaksi sekolah.

## Temuan dan perbaikan

| Tingkat | Lokasi | Sebelum | Sesudah dan dampaknya |
|---|---|---|---|
| Medium | `frontend/src/shared/components/SelectClearButton.vue`; 18 slot pada 12 komponen aplikasi/spesimen | SVG Phosphor menggantikan slot clear PrimeVue tanpa class dan callback. X tidak rata tengah dan klik membuka dropdown. | Satu tombol bersama menerima slot props, menjalankan callback hapus, menghentikan bubbling, memiliki target 44 px dan nama aksesibel. Mouse, Space dan Enter menghapus pilihan; fokus kembali ke combobox. |
| Medium | `frontend/src/assets/primevue-overrides.css:6` | Bagian bawah form Siswa tampak tertutup tombol; batas area gulir dengan footer tidak jelas. | Footer memiliki garis pembatas, padding dan wrapping; konten memiliki gutter scrollbar dan scroll padding. Alamat tidak hilang: kolomnya berada di area gulir dan dapat terlihat penuh di atas footer. |
| Medium | DatePicker Tagihan/Kegiatan/Jurnal/Absensi serta Select pada form/filter cakupan revamp | Overlay yang sudah terbuka tidak ikut tertutup ketika PrimeVue dinonaktifkan. Fieldset tidak mencakup popup yang diteleport ke body. | Enam DatePicker dan 23 Select pada cakupan revamp dipasang ulang saat status disabled berubah. Nilai tetap berasal dari model form; overlay lama dibuang. DatePicker pembayaran juga menerima disabled secara eksplisit. |

Enam tanggal meliputi mulai/selesai Kegiatan, Realisasi, Pembayaran Tagihan, Jurnal dan Absensi. Siswa menggunakan Select, bukan DatePicker. Pendaftaran sudah memiliki penguncian kalender sebelumnya; penguncian dropdown ditambahkan. Tidak menambah wrapper Select/DatePicker, dependency, atau mengubah kontrak payload/izin role.

## Bukti

- Skill yang dipakai: `ui-skills-root` dan `better-layout`. Playwright MCP menguji aplikasi localhost dalam browser terisolasi. Diagnosis memakai source PrimeVue yang terpasang dan komponen/caller aplikasi; referensi visual eksternal tidak dibutuhkan untuk bug ini.
- **81 tes terarah pada 19 file lulus**. Regresi mencakup clear pilihan/fokus, model dan kontak yang dipertahankan, kalender serta dropdown terbuka ketika saving, dan nilai yang tetap sama setelah recovery. Tes overlay mereproduksi kegagalan sebelum perbaikan. Seluruh suite repository tidak dijalankan.
- Build/typecheck lulus. Warning ukuran chunk existing di atas 500 kB masih ada.
- **9 pemeriksaan alur fixture, 265 pasangan layar/ukuran, nol page error**. Cakupan: empat role/home, Siswa, Tagihan/pembayaran/faktur, Kegiatan, Jurnal, kelima laporan, Absensi/Rekap, Katering/Jemputan, dan Pendaftaran. Semua request `/api/**` diintersep; mutasi hanya pada fixture memori.
- Ukuran layar: 1440×1000, 1024×768, 768×900, 390×844, 320×640 dan 720×450. Dialog Siswa juga ditampilkan pada 650×886 agar sebanding dengan screenshot laporan. Print Laporan diperiksa pada viewport A4 794×1123, terpisah dari ukuran layar.
- Pemeriksaan geometri meliputi overflow halaman/dialog, pusat dan ukuran target clear, batas dialog/footer, tombol footer, dan kolom terakhir yang dapat digulir di atas footer. Aksi keyboard clear Siswa diuji dengan Space/Enter; penguncian kalender/dropdown juga diuji pada alur Jurnal dan Absensi.
- Hasil terstruktur: [ui-audit-result-010.json](../../design-artifacts/bee-design-system/checks/ui-audit-result-010.json). Runner [layout-regression.js](../../design-artifacts/bee-design-system/checks/layout-regression.js) menerima `(page, name, check)` dan memakai ulang runner fixture existing, dengan menunggu transisi sebelum pengukuran. Tampilan print memakai ukuran kertas, bukan breakpoint telepon.
- Screenshot fixture yang diperiksa visual: [dialog Siswa](../../design-artifacts/bee-design-system/audit-ui-siswa-dialog.png), [Alamat setelah digulir](../../design-artifacts/bee-design-system/audit-ui-siswa-dialog-scroll.png), [Pembayaran mobile](../../design-artifacts/bee-design-system/audit-tagihan-payment-mobile-04.png). Screenshot menggunakan data fiktif.

Pembacaan overflow awal Kegiatan berasal dari menu yang sedang menjalankan animasi penutupan, bukan tabel yang kehilangan scroll. Setelah transisi selesai, pemeriksaan lulus tanpa perubahan CSS tabel. Pengukuran print pada lebar telepon juga dikeluarkan dari pemeriksaan layar; print menggunakan ukuran A4.

## Batas bukti dan kelanjutan

Belum diperiksa menyeluruh: modul pegawai/administrasi yang belum direvamp, seluruh 23 view/state, mutasi dengan database nyata, Safari/iPad, pembaca layar, zoom native 200%, RTL, perangkat sekolah, serta printer fisik. Viewport pendek bukan bukti pengujian zoom native. Hasil ini tidak menjamin tidak ada bug lain atau kesiapan produksi.

Lanjutkan rollout pegawai/administrasi sesuai inventaris setelah review lokal. Pertahankan pola slot clear bersama dan penutupan popup saat kontrol dikunci pada modul berikutnya; jangan menyalin SVG clear tanpa callback atau mengandalkan fieldset untuk menonaktifkan overlay di body.
