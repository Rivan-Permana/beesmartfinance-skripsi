import type { Coa, Tagihan } from "@/types/api"
export const billingNames = new Map([[1,"Alya Putri"],[2,"Bima Pratama"],[3,"Citra Maharani"],[4,"Daffa Ramadhan"]])
export const billingAccounts: Coa[] = [{kode_akun:"111",nama_akun:"Kas sekolah contoh",sub_golongan:null,posisi_normal:"D",is_active:true,saldo_awal:"0.00",tanggal_saldo_awal:null}]
function bill(id: number, rest: Partial<Tagihan>): Tagihan {
  return {id,siswa:id,siswa_nama:billingNames.get(id),periode_bulan:10,periode_tahun:2026,total:"750000.00",total_terbayar:"0.00",sisa_tagihan:"750000.00",status:"BELUM",jurnal:null,perlu_rekonsiliasi:false,pembayaran:[],detail:[{id:id*10,komponen:"SPP",kategori:"BULANAN",keterangan:"SPP Oktober",akun_pendapatan:"411",nominal:"750000.00",total_terbayar:"0.00"}],...rest}
}
export const billingSamples: Tagihan[] = [
  bill(1,{total:"900000.50",sisa_tagihan:"900000.50",detail:[{id:10,komponen:"SPP",kategori:"BULANAN",keterangan:"SPP Oktober",akun_pendapatan:"411",nominal:"750000.25",total_terbayar:"0.00"},{id:11,komponen:"KATERING",kategori:"BULANAN",keterangan:"Katering Oktober",akun_pendapatan:"412",nominal:"150000.25",total_terbayar:"0.00"}]}),
  bill(2,{status:"SEBAGIAN",total_terbayar:"300000.00",sisa_tagihan:"450000.00",detail:[{id:20,komponen:"SPP",kategori:"BULANAN",keterangan:"SPP Oktober",akun_pendapatan:"411",nominal:"750000.00",total_terbayar:"300000.00"}],pembayaran:[{id:1,tanggal:"2026-10-05",no_bukti:"CONTOH-002",nominal:"300000.00",akun_kas:"111",jurnal:"CONTOH-JURNAL",jurnal_status:"POSTED",created_by:null,dibatalkan:false,alasan_batal:"",dibatalkan_pada:null,alokasi:[{detail:20,nominal:"300000.00"}]}]}),
  bill(3,{status:"LUNAS",total_terbayar:"750000.00",sisa_tagihan:"0.00",detail:[{id:30,komponen:"SPP",kategori:"BULANAN",keterangan:"SPP Oktober",akun_pendapatan:"411",nominal:"750000.00",total_terbayar:"750000.00"}],pembayaran:[{id:2,tanggal:"2026-10-08",no_bukti:"CONTOH-003",nominal:"750000.00",akun_kas:"111",jurnal:"CONTOH-JURNAL-2",jurnal_status:"POSTED",created_by:null,dibatalkan:false,alasan_batal:"",dibatalkan_pada:null,alokasi:[{detail:30,nominal:"750000.00"}]}]}),
  bill(4,{status:"SEBAGIAN",periode_bulan:9,total_terbayar:null,sisa_tagihan:null,perlu_rekonsiliasi:true}),
]
