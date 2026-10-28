<script setup lang="ts">
import { ref } from "vue"
import Button from "primevue/button"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import SiswaDirectory from "@/features/siswa/SiswaDirectory.vue"
import SiswaFormDialog from "@/features/siswa/SiswaFormDialog.vue"
import Icon from "@/shared/components/PhosphorIcon.vue"
import type { Kelompok, Siswa, SiswaInput } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()
const groups: Kelompok[] = [
  { id: 1, nama: "Melati", jenjang: 1, jenjang_kode: "TK A" },
  { id: 2, nama: "Matahari", jenjang: 2, jenjang_kode: "TK B" },
  { id: 3, nama: "Kupu-kupu", jenjang: 3, jenjang_kode: "PG" },
]
const recordInfo: Pick<Siswa, "nama" | "nis" | "kelompok" | "status" | "spp_nominal">[] = [
  { nama: "Alya Putri", nis: "LM-26001", kelompok: 1, status: "aktif", spp_nominal: "750000.00" },
  { nama: "Bima Pratama", nis: "LM-26002", kelompok: 2, status: "aktif", spp_nominal: "800000.00" },
  { nama: "Citra Maharani", nis: "LM-26003", kelompok: 1, status: "cuti", spp_nominal: "750000.00" },
  { nama: "Daffa Ramadhan", nis: "LM-26004", kelompok: null, status: "aktif", spp_nominal: "700000.00" },
  { nama: "Elena Safira", nis: "LM-26005", kelompok: 3, status: "aktif", spp_nominal: "650000.00" },
  { nama: "Farhan Aditya", nis: "LM-26006", kelompok: 2, status: "lulus", spp_nominal: "800000.00" },
  { nama: "Gita Anindya", nis: null, kelompok: 1, status: "aktif", spp_nominal: "750000.00" },
  { nama: "Hana Kirana", nis: "LM-26008", kelompok: 3, status: "aktif", spp_nominal: "650000.00" },
  { nama: "Ibrahim Akbar", nis: "LM-26009", kelompok: 2, status: "naik", spp_nominal: "800000.00" },
  { nama: "Jihan Azzahra", nis: "LM-26010", kelompok: 1, status: "aktif", spp_nominal: "750000.00" },
  { nama: "Kenzo Mahendra", nis: "LM-26011", kelompok: null, status: "aktif", spp_nominal: "700000.00" },
  { nama: "Laras Ayuningtyas", nis: "LM-26012", kelompok: 2, status: "pindah", spp_nominal: "800000.00" },
 ]
const samples: Siswa[] = recordInfo.map((record, i) => ({
  ...record, id: i + 1, tanggal_lahir: null, periode: null, alamat: "",
  nama_ayah: "", kontak_ayah: "", nama_ibu: "", kontak_ibu: "",
  nama_panggilan: null, jenis_kelamin: null, tempat_lahir: null,
  diskon_kategori: [], diskon_nominal: "0.00", uang_masuk: null, uang_kegiatan: null,
  uang_pengembangan: null, uang_seragam: null, biaya_masuk: null,
}))
const rows = ref<Siswa[]>(structuredClone(samples))
const editing = ref<Siswa | null>(null)
const dialog = ref(false)
function resetSamples() { rows.value = structuredClone(samples) }
function create() { editing.value = null; dialog.value = true }
function edit(row: Siswa) { editing.value = row; dialog.value = true }
function save(payload: Partial<SiswaInput>) {
  if (editing.value) rows.value = rows.value.map((row) => row.id === editing.value!.id ? { ...row, ...payload } : row)
  else rows.value = [...rows.value, { ...samples[0]!, ...payload, id: Math.max(0, ...rows.value.map(row => row.id)) + 1 }]
  dialog.value = false
  toast.add({ severity: "success", summary: "Contoh siswa diperbarui", detail: "Perubahan hanya di halaman ini. Data sekolah tidak berubah.", life: 4000 })
}
function remove(row: Siswa) {
  confirm.require({ header: "Hapus siswa contoh?", message: `${row.nama} akan dihapus dari daftar contoh ini saja.`, rejectLabel: "Kembali", acceptLabel: "Hapus contoh", acceptProps: { severity: "danger" }, accept: () => { rows.value = rows.value.filter(item => item.id !== row.id) } })
}
function explainGroups() { toast.add({ severity: "info", summary: "Kelola kelompok", detail: "Di aplikasi, tindakan ini membuka halaman Kelompok. Halaman ini tetap memakai data contoh.", life: 4000 }) }
</script>

<template>
  <section id="layar-siswa" class="system-section">
    <header class="system-section-heading"><h2>Fondasi menjadi layar kerja.</h2><p>Direktori dan form yang sama dipakai halaman Siswa aplikasi. Coba pencarian, filter, halaman berikutnya, dan ubah data. Seluruh nama di sini fiktif; perubahan hanya berlaku sampai halaman dimuat ulang.</p></header>
    <div class="student-sample-header"><div><h3>Data siswa</h3><p>Kelola profil dan administrasi siswa PG/TK.</p></div><Button label="Tambah siswa" @click="create"><template #icon><Icon name="plus" /></template></Button></div>
    <SiswaDirectory :rows="rows" :kelompok="groups" @create="create" @edit="edit" @remove="remove" @manage-groups="explainGroups" />
    <SiswaFormDialog v-model="dialog" :student="editing" :kelompok="groups" @save="save" />
    <Button class="student-reset" label="Pulihkan 12 siswa contoh" severity="secondary" text @click="resetSamples" />
  </section>
</template>

<style scoped>
.student-sample-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--bee-space-4); margin-bottom: var(--bee-space-5); }
.student-sample-header h3 { font-size: var(--bee-type-title); font-weight: 600; line-height: var(--bee-leading-heading); }.student-sample-header p { color: var(--app-text-muted); margin: var(--bee-space-2) 0 0; }.student-reset { margin-top: var(--bee-space-3); }
@media(max-width:767px) { .student-sample-header h3 { font-size: var(--bee-type-title-mobile); } }
</style>
