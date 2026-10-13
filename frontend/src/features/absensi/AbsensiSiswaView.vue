<script setup lang="ts">
import Button from "primevue/button"
import DatePicker from "primevue/datepicker"
import Message from "primevue/message"
import { useConfirm } from "primevue/useconfirm"
import { useToast } from "primevue/usetoast"
import { computed, ref, watch } from "vue"

import AttendanceGrid, { type AttendanceRow } from "./AttendanceGrid.vue"
import { jenjangApi, kelompokApi, kehadiranApi } from "./api"
import { notifyError, notifySuccess } from "@/core/errors"
import { siswaApi } from "@/features/siswa/api"
import EmptyState from "@/shared/components/EmptyState.vue"
import PageLayout from "@/shared/components/PageLayout.vue"
import type { Jenjang, Kelompok, Siswa } from "@/types/api"

const toast = useToast()
const confirm = useConfirm()

const step = ref(1)
const jenjangList = ref<Jenjang[]>([])
const kelompokList = ref<Kelompok[]>([])
const selectedJenjang = ref<Jenjang | null>(null)
const selectedKelompok = ref<Kelompok | null>(null)
const tanggal = ref<Date>(new Date())
const students = ref<Siswa[]>([])
const attendance = ref<Record<number, AttendanceRow>>({})
const loading = ref(false)
const saving = ref(false)

const tanggalStr = computed(() => {
  const d = tanggal.value
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  return `${y}-${m}-${day}`
})

const stepLabels = ["Jenjang", "Kelompok", "Absensi"]

const summaryLabel = computed(() => {
  if (!selectedJenjang.value || !selectedKelompok.value) return ""
  return `${selectedJenjang.value.kode} · ${selectedKelompok.value.nama}`
})

async function loadJenjang() {
  loading.value = true
  try {
    jenjangList.value = await jenjangApi.list()
  } catch (e) {
    notifyError(toast, e, "Gagal memuat jenjang.")
  } finally {
    loading.value = false
  }
}

async function loadKelompok() {
  if (!selectedJenjang.value) return
  loading.value = true
  try {
    kelompokList.value = await kelompokApi.list({
      jenjang: selectedJenjang.value.id,
    })
  } catch (e) {
    notifyError(toast, e, "Gagal memuat kelompok.")
  } finally {
    loading.value = false
  }
}

async function loadGrid() {
  if (!selectedKelompok.value) return
  loading.value = true
  try {
    const [siswaRes, hadirRes] = await Promise.all([
      siswaApi.listAll({ kelompok: selectedKelompok.value.id, status: "aktif" }),
      kehadiranApi.list({ tanggal: tanggalStr.value }),
    ])
    students.value = siswaRes
    const existing = new Map(hadirRes.results.map((h) => [h.siswa, h]))
    const map: Record<number, AttendanceRow> = {}
    for (const s of students.value) {
      const prev = existing.get(s.id)
      map[s.id] = prev
        ? {
            siswaId: s.id,
            existingId: prev.id,
            status: prev.status,
            ikut_katering: prev.ikut_katering,
            jemput_datang: prev.jemput_datang,
            jemput_pulang: prev.jemput_pulang,
          }
        : {
            siswaId: s.id,
            status: "hadir",
            ikut_katering: false,
            jemput_datang: false,
            jemput_pulang: false,
          }
    }
    attendance.value = map
  } catch (e) {
    notifyError(toast, e, "Gagal memuat data absensi.")
  } finally {
    loading.value = false
  }
}

function pickJenjang(j: Jenjang) {
  selectedJenjang.value = j
  selectedKelompok.value = null
  step.value = 2
  loadKelompok()
}

function pickKelompok(k: Kelompok) {
  selectedKelompok.value = k
  step.value = 3
  loadGrid()
}

function goBack() {
  if (step.value === 3) {
    step.value = 2
    return
  }
  if (step.value === 2) {
    step.value = 1
    selectedKelompok.value = null
  }
}

function goToStep(target: number) {
  if (target >= step.value) return
  if (target === 1) {
    step.value = 1
    selectedKelompok.value = null
    return
  }
  if (target === 2 && selectedJenjang.value) {
    step.value = 2
    selectedKelompok.value = null
    loadKelompok()
  }
}

watch(tanggal, () => {
  if (step.value === 3 && selectedKelompok.value) loadGrid()
})

async function save() {
  saving.value = true
  try {
    const rows = Object.values(attendance.value)
    await Promise.all(
      rows.map((row) => {
        const payload = {
          siswa: row.siswaId,
          tanggal: tanggalStr.value,
          status: row.status,
          ikut_katering: row.ikut_katering,
          jemput_datang: row.jemput_datang,
          jemput_pulang: row.jemput_pulang,
        }
        return row.existingId
          ? kehadiranApi.update(row.existingId, payload)
          : kehadiranApi.create(payload)
      }),
    )
    notifySuccess(toast, `Absensi ${tanggalStr.value} tersimpan (${rows.length} siswa).`, {
      detail: "Buka Rekap Absensi untuk melihat total bulan ini.",
    })
    await loadGrid()
  } catch (e) {
    notifyError(toast, e, "Gagal menyimpan absensi.")
  } finally {
    saving.value = false
  }
}

async function deleteAttendance(siswaId: number) {
  const row = attendance.value[siswaId]
  if (!row?.existingId) return
  confirm.require({
    message: "Hapus catatan absensi siswa ini untuk tanggal yang dipilih?",
    header: "Hapus Absensi",
    acceptLabel: "Hapus",
    acceptClass: "p-button-danger",
    accept: async () => {
      try {
        await kehadiranApi.remove(row.existingId!)
        notifySuccess(toast, "Absensi dihapus")
        await loadGrid()
      } catch (e) {
        notifyError(toast, e, "Gagal menghapus absensi.")
      }
    },
  })
}

loadJenjang()
</script>

<template>
  <PageLayout
    title="Absensi Siswa"
    subtitle="Tandai kehadiran harian, katering, dan jemputan per kelompok"
  >
    <template #actions>
      <Button
        v-if="step === 3"
        label="Simpan Absensi"
        icon="pi pi-check"
        :loading="saving"
        :disabled="students.length === 0 || loading"
        @click="save"
      />
    </template>

    <Message severity="info" :closable="false" class="page-hint">
      Isi absensi per kelompok. Data tersimpan per tanggal — bisa diubah atau dihapus selama belum di-rekap final.
      Siswa tidak hadir otomatis tidak ikut katering/jemputan.
    </Message>

    <nav class="wizard-bar" aria-label="Langkah absensi">
      <Button
        v-if="step > 1"
        label="Kembali"
        icon="pi pi-arrow-left"
        severity="secondary"
        text
        size="small"
        class="wizard-back"
        @click="goBack"
      />
      <div class="wizard-steps">
        <button
          v-for="(label, i) in stepLabels"
          :key="label"
          type="button"
          class="wizard-step bee-section-title"
          :class="{
            active: step === i + 1,
            done: step > i + 1,
            clickable: step > i + 1,
          }"
          :disabled="step <= i + 1"
          :title="step > i + 1 ? `Kembali ke langkah ${label}` : undefined"
          @click="goToStep(i + 1)"
        >
          <span class="num">{{ i + 1 }}</span>
          {{ label }}
        </button>
      </div>
    </nav>

    <!-- Step 1: Jenjang -->
    <section v-if="step === 1" class="step-panel">
      <p class="hint">Pilih jenjang kelas hari ini.</p>
      <div v-if="loading" class="hint">Memuat jenjang…</div>
      <div v-else class="pick-grid">
        <button
          v-for="j in jenjangList"
          :key="j.id"
          type="button"
          class="bee-pick-card"
          @click="pickJenjang(j)"
        >
          <span class="bee-pick-card__code">{{ j.kode }}</span>
          <span class="bee-pick-card__name">{{ j.nama }}</span>
        </button>
      </div>
      <EmptyState
        v-if="!loading && jenjangList.length === 0"
        message="Belum ada jenjang. Jalankan seed_demo atau tambah master jenjang."
      />
    </section>

    <!-- Step 2: Kelompok -->
    <section v-if="step === 2" class="step-panel">
      <p class="hint">
        Jenjang <strong>{{ selectedJenjang?.kode }}</strong> — pilih kelompok.
      </p>
      <div v-if="loading" class="hint">Memuat kelompok…</div>
      <div v-else class="pick-grid">
        <button
          v-for="k in kelompokList"
          :key="k.id"
          type="button"
          class="bee-pick-card"
          @click="pickKelompok(k)"
        >
          <span class="bee-pick-card__code">{{ k.nama }}</span>
        </button>
      </div>
      <EmptyState
        v-if="!loading && kelompokList.length === 0"
        message="Belum ada kelompok untuk jenjang ini."
      />
    </section>

    <!-- Step 3: Grid -->
    <section v-if="step === 3" class="step-panel">
      <div class="step-toolbar">
        <Message severity="info" :closable="false" class="summary-msg">
          {{ summaryLabel }} · {{ tanggalStr }}
        </Message>
        <div class="date-field">
          <label for="tanggal-absensi">Tanggal</label>
          <DatePicker
            id="tanggal-absensi"
            v-model="tanggal"
            date-format="yy-mm-dd"
            show-icon
            fluid
          />
        </div>
      </div>

      <div v-if="loading" class="hint">Memuat siswa…</div>
      <EmptyState
        v-else-if="students.length === 0"
        message="Belum ada siswa aktif di kelompok ini."
      />
      <AttendanceGrid
        v-else
        :students="students"
        :model-value="attendance"
        @update:model-value="attendance = $event"
        @delete="deleteAttendance"
      />
    </section>
  </PageLayout>
</template>

<style scoped>
.page-hint {
  margin-bottom: 1rem;
}
.wizard-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}
.wizard-back {
  flex-shrink: 0;
}
.wizard-steps {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  flex: 1;
}
.wizard-step {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  background: var(--app-bg);
  color: var(--app-text-muted);
  font-size: 0.85rem;
  font-weight: 700;
  border: none;
  font-family: inherit;
  cursor: default;
}
.wizard-step.clickable {
  cursor: pointer;
}
.wizard-step.clickable:hover {
  background: color-mix(in srgb, var(--bee-green, #2e9e5b) 25%, white);
}
.wizard-step.active {
  background: var(--bee-navy);
  color: #fff;
}
.wizard-step.done {
  background: color-mix(in srgb, var(--bee-green, #2e9e5b) 15%, white);
  color: var(--bee-navy);
}
.wizard-step:disabled:not(.active) {
  opacity: 1;
}
.wizard-step .num {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 0.7rem;
  background: rgba(0, 0, 0, 0.08);
}
.wizard-step.active .num {
  background: rgba(255, 255, 255, 0.25);
}
.hint {
  color: var(--app-text-muted);
  margin: 0 0 1rem;
}
.pick-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 0.75rem;
}
.step-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 1rem;
}
.summary-msg {
  flex: 1;
  min-width: 12rem;
  margin: 0;
}
.date-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-width: 11rem;
}
.date-field label {
  font-weight: 600;
  font-size: 0.85rem;
}
</style>
