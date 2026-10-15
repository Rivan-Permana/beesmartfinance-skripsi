<script setup lang="ts">
import Button from "primevue/button"
import Column from "primevue/column"
import DataTable from "primevue/datatable"
import Message from "primevue/message"
import ProgressBar from "primevue/progressbar"
import Select from "primevue/select"
import Tab from "primevue/tab"
import TabList from "primevue/tablist"
import TabPanel from "primevue/tabpanel"
import TabPanels from "primevue/tabpanels"
import Tabs from "primevue/tabs"
import { useToast } from "primevue/usetoast"
import { computed, onMounted, ref, watch } from "vue"

import { laporanApi } from "./api"
import { downloadCsv } from "@/core/export"
import { notifyError } from "@/core/errors"
import { formatRp } from "@/core/format"
import { coaApi } from "@/features/jurnal/api"
import PageLayout from "@/shared/components/PageLayout.vue"
import PeriodPicker from "@/shared/components/PeriodPicker.vue"
import type {
  BukuBesarRow,
  Coa,
  LabaRugiResult,
  PosisiKeuanganResult,
  RealisasiAnggaranRow,
  SaldoRow,
} from "@/types/api"

const toast = useToast()

const tab = ref("neraca")
const periodeBulan = ref(new Date().getMonth() + 1)
const periodeTahun = ref(new Date().getFullYear())
const periodParams = computed(() => ({ tahun: periodeTahun.value, bulan: periodeBulan.value }))
function rp(v: string | number | null | undefined) {
  return formatRp(v)
}
function pct(pagu: string, realisasi: string) {
  const p = Number(pagu) || 0
  return p > 0 ? Math.round((Number(realisasi) / p) * 100) : 0
}

// --- shared data: COA utk filter buku besar ---
const coaList = ref<Coa[]>([])
onMounted(async () => {
  try { coaList.value = await coaApi.list() } catch { /* fallback kosong */ }
})

// --- Neraca Saldo ---
const neraca = ref<SaldoRow[]>([])
const loadingNeraca = ref(false)
async function loadNeraca() {
  loadingNeraca.value = true
  try { neraca.value = await laporanApi.neracaSaldo({ tahun: periodeTahun.value }) }
  catch (e) { notifyError(toast, e, "Gagal memuat neraca saldo.") }
  finally { loadingNeraca.value = false }
}

// --- Laba Rugi ---
const labaRugi = ref<LabaRugiResult | null>(null)
const loadingLR = ref(false)
async function loadLabaRugi() {
  loadingLR.value = true
  try { labaRugi.value = await laporanApi.labaRugi({ tahun: periodeTahun.value }) }
  catch (e) { notifyError(toast, e, "Gagal memuat laba rugi.") }
  finally { loadingLR.value = false }
}

// --- Posisi Keuangan ---
const posisi = ref<PosisiKeuanganResult | null>(null)
const loadingPK = ref(false)
async function loadPosisi() {
  loadingPK.value = true
  try { posisi.value = await laporanApi.posisiKeuangan({ tahun: periodeTahun.value }) }
  catch (e) { notifyError(toast, e, "Gagal memuat posisi keuangan.") }
  finally { loadingPK.value = false }
}
const totalAset = computed(() =>
  (posisi.value?.aset ?? []).reduce((s, r) => s + Number(r.saldo_akhir), 0),
)
const totalLiabEkuitas = computed(() => {
  const l = (posisi.value?.liabilitas ?? []).reduce((s, r) => s + Number(r.saldo_akhir), 0)
  const e = (posisi.value?.ekuitas ?? []).reduce((s, r) => s + Number(r.saldo_akhir), 0)
  return l + e
})

// --- Realisasi Anggaran ---
const realisasi = ref<RealisasiAnggaranRow[]>([])
const loadingRA = ref(false)
async function loadRealisasi() {
  loadingRA.value = true
  try { realisasi.value = await laporanApi.realisasiAnggaran(periodeTahun.value) }
  catch (e) { notifyError(toast, e, "Gagal memuat realisasi anggaran.") }
  finally { loadingRA.value = false }
}

// --- Buku Besar ---
const kodeAkun = ref<string | null>(null)
const mutasi = ref<BukuBesarRow[]>([])
const loadingBB = ref(false)
async function loadBukuBesar() {
  if (!kodeAkun.value) return
  loadingBB.value = true
  try {
    mutasi.value = await laporanApi.bukuBesar(kodeAkun.value, periodParams.value)
  }
  catch (e) { notifyError(toast, e, "Gagal memuat buku besar.") }
  finally { loadingBB.value = false }
}
const mutasiDenganSaldo = computed(() => {
  let saldo = 0
  const kreditNormal = coaList.value.find((akun) => akun.kode_akun === kodeAkun.value)?.posisi_normal === "K"
  return mutasi.value.map((m) => {
    saldo += Number(m.debit) - Number(m.kredit)
    return { ...m, saldo: kreditNormal ? -saldo : saldo }
  })
})

// auto-load tiap pindah tab pertama kali
const loaded = ref<Record<string, boolean>>({})

async function reloadTab(t: string) {
  if (t === "neraca") await loadNeraca()
  if (t === "lr") await loadLabaRugi()
  if (t === "pk") await loadPosisi()
  if (t === "ra") await loadRealisasi()
  if (t === "bb" && kodeAkun.value) await loadBukuBesar()
}

watch(tab, async (t) => {
  if (loaded.value[t]) return
  loaded.value[t] = true
  await reloadTab(t)
}, { immediate: true })

async function applyPeriod() {
  loaded.value = { [tab.value]: true }
  await reloadTab(tab.value)
}

function cetak() {
  window.print()
}

function exportNeracaCsv() {
  downloadCsv(
    `neraca-saldo-${periodeTahun.value}.csv`,
    ["Kode", "Nama", "Posisi", "Debit", "Kredit", "Saldo"],
    neraca.value.map((r) => [
      r.kode_akun, r.nama_akun, r.posisi_normal,
      r.total_debit, r.total_kredit, r.saldo_akhir,
    ]),
  )
}
</script>

<template>
  <PageLayout title="Laporan Keuangan" subtitle="Neraca saldo, laba rugi, posisi keuangan, dan buku besar">
    <template #filters>
      <PeriodPicker v-model:bulan="periodeBulan" v-model:tahun="periodeTahun" />
      <Button label="Terapkan" icon="pi pi-filter" size="small" @click="applyPeriod" />
    </template>
    <template #actions>
      <Button label="Cetak" icon="pi pi-print" severity="secondary" @click="cetak" />
      <Button v-if="tab === 'neraca'" label="Export CSV" icon="pi pi-download" text @click="exportNeracaCsv" />
    </template>

    <Message severity="info" :closable="false" class="mb">
      Laporan mencakup <strong>saldo awal bertanggal dan jurnal berstatus POSTED</strong>.
      Neraca saldo dan posisi keuangan menampilkan saldo sampai akhir {{ periodeTahun }};
      laba rugi menampilkan tahun tersebut. Buku besar membawa saldo awal periode saat difilter per bulan.
    </Message>

    <div class="laporan-print">
    <Tabs v-model:value="tab">
      <TabList>
        <Tab value="neraca">Neraca Saldo</Tab>
        <Tab value="lr">Laba Rugi</Tab>
        <Tab value="pk">Posisi Keuangan</Tab>
        <Tab value="ra">Realisasi Anggaran</Tab>
        <Tab value="bb">Buku Besar</Tab>
      </TabList>
      <TabPanels>
        <!-- Neraca Saldo -->
        <TabPanel value="neraca">
          <DataTable :value="neraca" :loading="loadingNeraca" data-key="kode_akun" striped-rows>
            <template #empty>Belum ada data.</template>
            <Column field="kode_akun" header="Kode" />
            <Column field="nama_akun" header="Nama Akun" />
            <Column header="Posisi">
              <template #body="{ data }">{{ data.posisi_normal === "D" ? "Debit" : "Kredit" }}</template>
            </Column>
            <Column header="Total Debit"><template #body="{ data }">{{ rp(data.total_debit) }}</template></Column>
            <Column header="Total Kredit"><template #body="{ data }">{{ rp(data.total_kredit) }}</template></Column>
            <Column header="Saldo Akhir"><template #body="{ data }">{{ rp(data.saldo_akhir) }}</template></Column>
          </DataTable>
        </TabPanel>

        <!-- Laba Rugi -->
        <TabPanel value="lr">
          <div v-if="labaRugi" class="lr">
            <section>
              <h3>Pendapatan</h3>
              <table class="report">
                <tbody>
                  <tr v-for="r in labaRugi.pendapatan" :key="r.kode_akun">
                    <td>{{ r.kode_akun }} — {{ r.nama_akun }}</td>
                    <td class="num">{{ rp(r.saldo_akhir) }}</td>
                  </tr>
                  <tr class="total">
                    <td>Total Pendapatan</td>
                    <td class="num">{{ rp(labaRugi.total_pendapatan) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
            <section>
              <h3>Beban</h3>
              <table class="report">
                <tbody>
                  <tr v-for="r in labaRugi.beban" :key="r.kode_akun">
                    <td>{{ r.kode_akun }} — {{ r.nama_akun }}</td>
                    <td class="num">{{ rp(r.saldo_akhir) }}</td>
                  </tr>
                  <tr class="total">
                    <td>Total Beban</td>
                    <td class="num">{{ rp(labaRugi.total_beban) }}</td>
                  </tr>
                </tbody>
              </table>
            </section>
            <div class="lr-result" :class="{ negatif: Number(labaRugi.laba_rugi) < 0 }">
              <span>{{ Number(labaRugi.laba_rugi) >= 0 ? "Laba" : "Rugi" }} Periode</span>
              <strong>{{ rp(labaRugi.laba_rugi) }}</strong>
            </div>
          </div>
          <div v-else-if="loadingLR" class="muted">Memuat…</div>
        </TabPanel>

        <!-- Posisi Keuangan -->
        <TabPanel value="pk">
          <div v-if="posisi" class="pk-grid">
            <section>
              <h3>Aset</h3>
              <table class="report">
                <tbody>
                  <tr v-for="r in posisi.aset" :key="r.kode_akun">
                    <td>{{ r.kode_akun }} — {{ r.nama_akun }}</td>
                    <td class="num">{{ rp(r.saldo_akhir) }}</td>
                  </tr>
                  <tr class="total"><td>Total Aset</td><td class="num">{{ rp(totalAset) }}</td></tr>
                </tbody>
              </table>
            </section>
            <section>
              <h3>Liabilitas + Ekuitas</h3>
              <table class="report">
                <tbody>
                  <tr v-for="r in posisi.liabilitas" :key="r.kode_akun">
                    <td>L · {{ r.kode_akun }} — {{ r.nama_akun }}</td>
                    <td class="num">{{ rp(r.saldo_akhir) }}</td>
                  </tr>
                  <tr v-for="r in posisi.ekuitas" :key="r.kode_akun">
                    <td>E · {{ r.kode_akun }} — {{ r.nama_akun }}</td>
                    <td class="num">{{ rp(r.saldo_akhir) }}</td>
                  </tr>
                  <tr class="total"><td>Total Liab. + Ekuitas</td><td class="num">{{ rp(totalLiabEkuitas) }}</td></tr>
                </tbody>
              </table>
            </section>
          </div>
          <div v-else-if="loadingPK" class="muted">Memuat…</div>
        </TabPanel>

        <!-- Realisasi Anggaran -->
        <TabPanel value="ra">
          <DataTable :value="realisasi" :loading="loadingRA" striped-rows>
            <template #empty>Belum ada data anggaran untuk tahun ini.</template>
            <Column field="kode_akun" header="Akun" />
            <Column field="nama_akun" header="Nama" />
            <Column header="Pagu"><template #body="{ data }">{{ rp(data.pagu) }}</template></Column>
            <Column header="Realisasi"><template #body="{ data }">{{ rp(data.realisasi) }}</template></Column>
            <Column header="Sisa"><template #body="{ data }">{{ rp(data.sisa_pagu) }}</template></Column>
            <Column header="Utilisasi" style="min-width: 12rem">
              <template #body="{ data }">
                <ProgressBar :value="pct(data.pagu, data.realisasi)" />
              </template>
            </Column>
          </DataTable>
        </TabPanel>

        <!-- Buku Besar -->
        <TabPanel value="bb">
          <div class="toolbar">
            <label>Akun</label>
            <Select
              v-model="kodeAkun"
              :options="coaList"
              option-label="nama_akun"
              option-value="kode_akun"
              filter
              placeholder="Pilih akun"
              style="min-width: 22rem"
              @change="loadBukuBesar"
            />
          </div>
          <DataTable :value="mutasiDenganSaldo" :loading="loadingBB" striped-rows>
            <template #empty>{{ kodeAkun ? "Belum ada mutasi." : "Pilih akun untuk melihat buku besar." }}</template>
            <Column field="tanggal" header="Tanggal" />
            <Column field="no_bukti" header="No. Bukti" />
            <Column field="keterangan" header="Keterangan" />
            <Column header="Debit"><template #body="{ data }">{{ rp(data.debit) }}</template></Column>
            <Column header="Kredit"><template #body="{ data }">{{ rp(data.kredit) }}</template></Column>
            <Column header="Saldo">
              <template #body="{ data }">
                <span :class="{ negatif: data.saldo < 0 }">{{ rp(data.saldo) }}</span>
              </template>
            </Column>
          </DataTable>
        </TabPanel>
      </TabPanels>
    </Tabs>
    </div>
  </PageLayout>
</template>

<style scoped>
.toolbar {
  display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.85rem;
}
.toolbar label { font-weight: 600; }
.lr, .pk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; }
section h3 { margin: 0 0 0.5rem; }
.report { width: 100%; border-collapse: collapse; }
.report td { padding: 0.35rem 0.4rem; border-bottom: 1px dashed var(--app-border); }
.report .num { text-align: right; }
.report .total td { font-weight: 800; border-top: 2px solid var(--app-border); border-bottom: none; }
.lr-result {
  grid-column: 1 / -1; display: flex; justify-content: space-between;
  background: var(--app-surface); border: 1px solid var(--app-border);
  border-radius: 12px; padding: 0.9rem 1.1rem; font-size: 1.1rem;
}
.lr-result strong { color: #2e9e5b; }
.lr-result.negatif strong { color: var(--bee-magenta); }
.negatif { color: var(--bee-magenta); }
.muted { color: var(--app-text-muted); padding: 1rem; }
.mb { margin-bottom: 1rem; }
</style>

<style>
@media print {
  .bee-page__header,
  .p-tablist,
  .p-message,
  .bee-page__filters {
    display: none !important;
  }
  .laporan-print {
    padding: 0;
  }
}
</style>
