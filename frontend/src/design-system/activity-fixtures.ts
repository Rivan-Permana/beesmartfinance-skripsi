import type { Coa, Kegiatan, LaporanKegiatan, Pegawai, PeriodeAkuntansi } from "@/types/api"
export const activityPeriods:PeriodeAkuntansi[]=[{id:1,kode:"2026/2027",tgl_mulai:"2026-07-01",tgl_selesai:"2027-06-30",status:"OPEN"},{id:2,kode:"2025/2026",tgl_mulai:"2025-07-01",tgl_selesai:"2026-06-30",status:"CLOSED"}]
export const activityAccounts:Coa[]=[{kode_akun:"5101",nama_akun:"Beban kegiatan sekolah",sub_golongan:null,posisi_normal:"D",is_active:true,saldo_awal:"0.00",tanggal_saldo_awal:null}]
export const activityStaff:Pegawai[]=[{id:1,nip:null,nama:"Guru Contoh",jabatan:"Guru PIC",nomor_hp:null,alamat:null,status:"aktif",status_aktif:true,tanggal_mulai_kerja:null,tanggal_selesai_kerja:null,user:null}]
export const activitySamples:Kegiatan[]=[
  {id:1,nama:"Pekan membaca",akun_beban:"5101",pagu:"7000000.00",realisasi:"1200000.00",sisa_pagu:"5800000.00",rasio_utilisasi:1200000/7000000,penanggung_jawab:1,periode:1,periode_kode:"2026/2027",tanggal_mulai:"2026-10-01",tanggal_selesai:"2026-10-31",status:"BERJALAN"},
  {id:2,nama:"Kunjungan edukasi",akun_beban:"5101",pagu:"5000000.00",realisasi:"0.00",sisa_pagu:"5000000.00",rasio_utilisasi:0,penanggung_jawab:1,periode:1,periode_kode:"2026/2027",tanggal_mulai:"2026-11-01",tanggal_selesai:"2026-11-30",status:"RENCANA"},
  {id:3,nama:"Pentas akhir tahun",akun_beban:"5101",pagu:"3000000.00",realisasi:"3000000.00",sisa_pagu:"0.00",rasio_utilisasi:1,penanggung_jawab:1,periode:2,periode_kode:"2025/2026",tanggal_mulai:"2026-06-01",tanggal_selesai:"2026-06-30",status:"SELESAI"},
]
export const activityDetails:Record<number,LaporanKegiatan["rincian"]>={1:[{tanggal:"2026-10-06",deskripsi:"Pembelian buku contoh",nominal:"1200000.00"}],2:[],3:[{tanggal:"2026-06-10",deskripsi:"Penyelenggaraan pentas contoh",nominal:"3000000.00"}]}
