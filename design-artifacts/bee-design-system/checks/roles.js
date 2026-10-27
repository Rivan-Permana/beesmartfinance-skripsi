async (page) => {
  let role = 'Finance'
  let failCash = false
  const calls = []
  const paged = (results) => ({ count: results.length, next: null, previous: null, results })
  const baseJournal = { tanggal: '2026-10-15', can_finance_post: false, perlu_rekonsiliasi: false, created_by: 2, tipe_sumber: 'MANUAL', detail: [], keterangan: 'Jurnal contoh', approved_by: null, posted_at: null, is_deleted: false }
  const pending = [
    { ...baseJournal, id: '1', no_bukti: 'PENDING-LAYAK', status: 'PENDING' },
    { ...baseJournal, id: '2', no_bukti: 'MILIK-SENDIRI', status: 'PENDING', created_by: 1 },
    { ...baseJournal, id: '3', no_bukti: 'LANGSUNG-FINANCE', status: 'PENDING', can_finance_post: true },
    { ...baseJournal, id: '4', no_bukti: 'REKONSILIASI', status: 'PENDING', perlu_rekonsiliasi: true },
  ]
  const activities = [{ id: 1, nama: 'Kegiatan membaca contoh', akun_beban: '5.1', pagu: '7000000.00', realisasi: '1200000.00', sisa_pagu: '5800000.00', rasio_utilisasi: .17, status: 'BERJALAN', penanggung_jawab: 1, periode: 1 }]
  await page.unroute('**/api/**')
  await page.evaluate(() => localStorage.setItem('bee_access', 'synthetic-local-review'))
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace(/^.*\/api\/v1/, '')
    calls.push({ role, method: request.method(), path, status: url.searchParams.get('status') })
    if (request.method() !== 'GET') return route.fulfill({ status: 405, json: { detail: 'Local review: mutations disabled' } })
    let data = paged([])
    if (path === '/auth/me/') data = { id: 1, username: 'contoh', nama: 'Pengguna Contoh', is_superuser: false, groups: [role] }
    else if (path === '/dashboard/ringkasan/') data = { kas: '78450000.00', total_pendapatan: '43800000.00', total_beban: '28650000.00', surplus_defisit: '15150000.00', anggaran: { pagu: '90000000.00', realisasi: '28650000.00' }, periode_filter: { label: 'Oktober 2026', tahun: 2026, bulan: 10, mode: 'month' }, operasional: { siswa_aktif: 40, hadir_bulan_ini: 25, absensi_sparkline: [{label:'Okt',hadir:25}] } }
    else if (path === '/dashboard/prediksi-kas/') {
      if (failCash) return route.fulfill({ status: 503, json: { detail: 'Synthetic failure' } })
      data = [5,6,7,8,9,10].map((bulan) => ({ periode: `2026-${bulan}`, tahun: 2026, bulan, arus_kas_masuk: '43800000', arus_kas_keluar: '28650000', net_cash_flow_bulanan: '15150000' }))
    }
    else if (path === '/dashboard/laba-rugi-bulanan/') data = { tahun: 2026, data: [5,6,7,8,9,10].map(bulan => ({ bulan, pendapatan: 43800000, beban: 28650000 })) }
    else if (path.includes('laba-rugi')) data = { pendapatan: [{ kode_akun:'4.1',nama_akun:'Pendapatan SPP',saldo_akhir:'43800000' }], beban: [{ kode_akun:'5.1',nama_akun:'Operasional',saldo_akhir:'28650000' }] }
    else if (path.includes('realisasi-anggaran')) data = [{ kode_akun:'5.1',nama_akun:'Operasional',pagu:'90000000',realisasi:'28650000' }]
    else if (path === '/jurnal/') data = paged(url.searchParams.get('status') === 'PENDING' ? pending : [{ ...baseJournal, id:'5', no_bukti:'JURNAL-CONTOH', status:url.searchParams.get('status') ?? 'DRAFT' }])
    else if (path === '/kegiatan/') data = paged(activities)
    else if (path === '/siswa/') data = paged([{ id:1, nis:'CONTOH-001',nama:'Siswa Contoh',status:'aktif',spp_nominal:'750000.00',kelompok:1 }])
    else if (path === '/kelompok/') data = paged([{ id:1, nama:'A1',jenjang:1,jenjang_kode:'TK A' }])
    await route.fulfill({ status: 200, json: data })
  })
  const evidence = []
  try {
  for (const value of ['Finance', 'SchoolPrincipal', 'Administration', 'TeacherInCharge']) {
    role = value
    const home = value === 'Administration' ? '/siswa' : value === 'TeacherInCharge' ? '/kegiatan' : '/dashboard'
    await page.setViewportSize({ width: 1440, height: 1000 })
    await page.goto(`http://127.0.0.1:4173${home}`)
    await page.locator('.bee-page h1').waitFor()
    if (home === '/dashboard') await page.locator('.dashboard-scope').filter({ hasText: 'Ringkasan:' }).waitFor()
    else await page.locator('.p-datatable-tbody tr').first().waitFor()
    await page.evaluate(() => document.fonts.ready)
    await page.locator('.p-datatable-mask').waitFor({state:'hidden'})
    await page.waitForFunction(() => document.getAnimations().every(animation => animation.playState !== 'running'))
    const text = await page.locator('.shell-content').innerText()
    if (text.includes('Tren Kehadiran')) throw new Error('Attendance reached a financial dashboard')
    if (value === 'SchoolPrincipal') {
      const queue = await page.locator('.journal-queue').innerText()
      if (!queue.includes('PENDING-LAYAK') || ['MILIK-SENDIRI','LANGSUNG-FINANCE','REKONSILIASI'].some(id => queue.includes(id))) throw new Error('Incorrect principal review eligibility')
    }
    if (value === 'TeacherInCharge' && calls.some(call => call.role === value && call.path === '/coa/')) throw new Error('Teacher loaded management-only account options')
    const title = await page.locator('.bee-page h1').innerText()
    await page.screenshot({ path: `design-artifacts/bee-design-system/role-${value}-05.png`, scale: 'css' })
    evidence.push({ role:value, home, title, width:await page.evaluate(() => document.documentElement.scrollWidth), font:await page.locator('body').evaluate(el => getComputedStyle(el).fontFamily) })
  }
  role = 'Finance'
  await page.goto('http://127.0.0.1:4173/dashboard')
  await page.locator('.dashboard-scope').filter({ hasText: 'Ringkasan:' }).waitFor()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.waitForFunction(() => document.documentElement.scrollWidth <= innerWidth)
  const mobile = await page.evaluate(() => ({ viewport:innerWidth, width:document.documentElement.scrollWidth }))
  if (mobile.width > mobile.viewport) throw new Error('Dashboard mobile overflow')
  await page.getByRole('button', { name:'Menu', exact:true }).click()
  await page.getByRole('dialog').waitFor()
  await page.keyboard.press('Escape')
  await page.getByRole('dialog').waitFor({state:'hidden'})
  await page.waitForFunction(() => document.activeElement?.getAttribute('aria-label') === 'Menu')
  const focusReturned = await page.getByRole('button', {name:'Menu',exact:true}).evaluate(el => el === document.activeElement)
  await page.screenshot({ path:'design-artifacts/bee-design-system/dashboard-mobile-05.png',scale:'css' })
  failCash = true
  await page.getByRole('button',{name:'Muat ulang',exact:true}).click()
  await page.getByText('Arus kas belum berhasil dimuat.',{exact:true}).waitFor()
  const partialFailure = await page.locator('.dashboard-error').innerText()
  const noWrites = calls.every(c => c.method === 'GET')
  return { evidence, mobile, focusReturned, partialFailure, noWrites, source:'Local API fixtures only', calls }
  } finally {
    await page.unroute('**/api/**')
    await page.goto('http://127.0.0.1:4173/design-system.html')
    await page.evaluate(() => localStorage.removeItem('bee_access'))
  }
}
