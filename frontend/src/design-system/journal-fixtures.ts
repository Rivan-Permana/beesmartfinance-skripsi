import type { Coa, Jurnal } from "@/types/api"
export const journalAccounts: Coa[] = [
  {kode_akun:"111",nama_akun:"Kas sekolah",posisi_normal:"D",is_active:true,sub_golongan:null,saldo_awal:"0.00",tanggal_saldo_awal:null},
  {kode_akun:"411",nama_akun:"Pendapatan SPP",posisi_normal:"K",is_active:true,sub_golongan:null,saldo_awal:"0.00",tanggal_saldo_awal:null},
  {kode_akun:"511",nama_akun:"Bahan pembelajaran",posisi_normal:"D",is_active:true,sub_golongan:null,saldo_awal:"0.00",tanggal_saldo_awal:null},
  {kode_akun:"512",nama_akun:"Beban kegiatan",posisi_normal:"D",is_active:true,sub_golongan:null,saldo_awal:"0.00",tanggal_saldo_awal:null},
  {kode_akun:"599",nama_akun:"Akun lama",posisi_normal:"D",is_active:false,sub_golongan:null,saldo_awal:"0.00",tanggal_saldo_awal:null},
]
function journal(id:string,rest:Partial<Jurnal>):Jurnal{
  return {id,no_bukti:`CONTOH-${id}`,tanggal:"2026-10-16",keterangan:"Pembelian bahan pembelajaran",tipe_sumber:"MANUAL",status:"DRAFT",created_by:1,approved_by:null,posted_at:null,is_deleted:false,can_finance_post:true,perlu_rekonsiliasi:false,detail:[{kode_akun:"511",debit:"450000.50",kredit:"0.00"},{kode_akun:"111",debit:"0.00",kredit:"450000.50"}],...rest}
}
export const journalSamples:Jurnal[]=[
  journal("001",{}),
  journal("002",{keterangan:"Penerimaan SPP Oktober",tipe_sumber:"AUTO_BILLING",detail:[{kode_akun:"111",debit:"750000.00",kredit:"0.00"},{kode_akun:"411",debit:"0.00",kredit:"750000.00"}]}),
  journal("003",{keterangan:"Realisasi Pekan Membaca",tipe_sumber:"AUTO_KEGIATAN",status:"PENDING",can_finance_post:false,created_by:3}),
  journal("004",{keterangan:"Penerimaan lama, bukti perlu dicocokkan",tipe_sumber:"AUTO_PENDAFTARAN",perlu_rekonsiliasi:true,can_finance_post:false}),
  journal("005",{keterangan:"Bahan pembelajaran yang sudah dicatat",status:"POSTED",posted_at:"2026-10-16T10:00:00+07:00"}),
  journal("006",{keterangan:"Kegiatan yang diajukan sendiri oleh Kepsek contoh",tipe_sumber:"AUTO_KEGIATAN",status:"PENDING",can_finance_post:false,created_by:2}),
  journal("007",{keterangan:"Draf kegiatan menunggu pengajuan",tipe_sumber:"AUTO_KEGIATAN",can_finance_post:false}),
]
