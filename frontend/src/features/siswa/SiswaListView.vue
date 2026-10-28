<script setup lang="ts">
import Button from "primevue/button"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { kelompokApi } from "@/features/absensi/api"
import { siswaApi } from "./api"
import { friendlyError, notifyError, notifySuccess } from "@/core/errors"
import Icon from "@/shared/components/PhosphorIcon.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import SiswaDirectory from "./SiswaDirectory.vue"
import SiswaFormDialog from "./SiswaFormDialog.vue"
import TagihanPaymentDialog from "@/features/tagihan/TagihanPaymentDialog.vue"
import { tagihanApi } from "@/features/tagihan/api"
import { paymentFormFor, paymentPayload, paymentValid, type TagihanPaymentForm } from "@/features/tagihan/payment"
import { coaApi } from "@/features/jurnal/api"
import type { Coa, Kelompok, Siswa, SiswaInput, Tagihan } from "@/types/api"
import { useAuthStore } from '@/stores/auth'

const toast = useToast()
const confirm = useConfirm()
const router = useRouter()
const rows = ref<Siswa[]>([])
const kelompokList = ref<Kelompok[]>([])
const loading = ref(false)
const loadError = ref("")
const groupError = ref(false)
const dialog = ref(false)
const editing = ref<Siswa | null>(null)
const saving = ref(false)
const saveError = ref("")

async function load() {
  loading.value = true
  loadError.value = ""
  try {
    const [students, groups] = await Promise.allSettled([siswaApi.listAll(), kelompokApi.list()])
    rows.value = students.status === "fulfilled" ? students.value : []
    if (students.status === "rejected") loadError.value = "Data siswa belum berhasil dimuat. Periksa koneksi, lalu coba lagi."
    groupError.value = groups.status === "rejected"
    if (groups.status === "fulfilled") kelompokList.value = groups.value
  } finally {
    loading.value = false
  }
}
function openCreate() { editing.value = null; saveError.value = ""; dialog.value = true }
function openEdit(row: Siswa) { editing.value = row; saveError.value = ""; dialog.value = true }
async function save(payload: Partial<SiswaInput>) {
  if (saving.value) return
  saving.value = true
  saveError.value = ""
  try {
    if (editing.value) {
      await siswaApi.update(editing.value.id, payload)
      notifySuccess(toast, "Data siswa diperbarui")
    } else {
      await siswaApi.create(payload)
      notifySuccess(toast, "Siswa baru ditambahkan")
    }
    dialog.value = false
    await load()
  } catch (e) {
    const error = friendlyError(e, "Data siswa belum berhasil disimpan.")
    saveError.value = [error.summary, error.detail].filter(Boolean).join(". ")
  } finally {
    saving.value = false
  }
}
function confirmDelete(row: Siswa) {
  confirm.require({
    message: `Hapus data ${row.nama}? Periksa kembali siswa yang dipilih sebelum melanjutkan.`,
    header: "Hapus data siswa?", rejectLabel: "Kembali", acceptLabel: "Hapus siswa",
    acceptProps: { severity: "danger" },
    accept: async () => {
      try {
        await siswaApi.remove(row.id)
        notifySuccess(toast, "Siswa dihapus")
        await load()
      } catch (e) {
        notifyError(toast, e, "Data siswa belum berhasil dihapus.")
      }
    },
  })
}
const receiveDialog = ref(false)
const receiveTarget = ref<Tagihan | null>(null)
const receiveStudent = ref("")
const receiveForm = ref<TagihanPaymentForm>({ tanggal: new Date(), no_bukti: "", akun_kas: "", request_id: "", alokasi: [] })
const receiveSaving = ref(false)
const receiveError = ref("")
const kasOptions = ref<Coa[]>([])
async function loadAccounts() {
  try {
    const coa = await coaApi.list()
    kasOptions.value = coa.filter((c) => c.is_active && ["111", "112", "1011", "1101", "1102"].includes(c.kode_akun))
  } catch (e) {
    notifyError(toast, e, "Akun penerimaan belum berhasil dimuat.")
  }
}
async function openReceive(row: Siswa) {
  if (!row.biaya_masuk) return
  try {
    const [tagihan] = await Promise.all([tagihanApi.get(row.biaya_masuk.tagihan), kasOptions.value.length ? null : loadAccounts()])
    receiveTarget.value = tagihan
    receiveStudent.value = row.nama
    receiveError.value = ""
    receiveForm.value = paymentFormFor(tagihan, kasOptions.value[0]?.kode_akun ?? "")
    receiveDialog.value = true
  } catch (e) {
    notifyError(toast, e, "Rincian biaya masuk belum berhasil dimuat.")
  }
}
async function saveReceive() {
  if (!receiveTarget.value || !paymentValid(receiveForm.value) || receiveSaving.value) return
  receiveSaving.value = true
  receiveError.value = ""
  try {
    const res = await tagihanApi.bayar(receiveTarget.value.id, paymentPayload(receiveForm.value))
    notifySuccess(toast, "Penerimaan biaya masuk tersimpan", res)
    receiveDialog.value = false
    await load()
  } catch (e) {
    const error = friendlyError(e, "Penerimaan belum berhasil disimpan.")
    receiveError.value = [error.summary, error.detail].filter(Boolean).join(". ")
  } finally {
    receiveSaving.value = false
  }
}
onMounted(load)
const canWrite = computed(() => useAuthStore().hasRole(['Administration']))
</script>

<template>
  <PageLayout title="Data siswa" :subtitle="canWrite?'Kelola profil dan administrasi siswa PG/TK.':'Lihat profil dan tarif siswa PG/TK. Perubahan data dilakukan Staf TU.'" :surface="false">
    <template v-if="canWrite" #actions><Button label="Tambah siswa" @click="openCreate"><template #icon><Icon name="plus" /></template></Button></template>
    <SiswaDirectory :rows="rows" :kelompok="kelompokList" :loading="loading" :error="loadError" :group-error="groupError" :readonly="!canWrite" @create="openCreate" @edit="openEdit" @remove="confirmDelete" @receive="openReceive" @retry="load" @manage-groups="router.push('/kelompok')" />
    <TagihanPaymentDialog v-if="canWrite" v-model="receiveDialog" v-model:form="receiveForm" :target="receiveTarget" :student-name="receiveStudent" :accounts="kasOptions" :saving="receiveSaving" :error="receiveError" @save="saveReceive" @reload-accounts="loadAccounts" />
    <SiswaFormDialog v-model="dialog" :student="editing" :kelompok="kelompokList" :saving="saving" :error="saveError" :group-error="groupError" @save="save" />
  </PageLayout>
</template>
