async(page)=>{
  await page.goto('http://127.0.0.1:4173/design-system.html')
  const fixtures=await page.evaluate(async()=>{const m=await import('/src/design-system/activity-fixtures.ts');return JSON.parse(JSON.stringify({rows:m.activitySamples,periods:m.activityPeriods,staff:m.activityStaff,accounts:m.activityAccounts,details:m.activityDetails}))})
  let rows=fixtures.rows
  let details=fixtures.details
  let role='TeacherInCharge'
  let failSave=true
  let failPeriods=false
  let failList=false
  let holdPeriod=false
  let releasePeriod
  let readyResolve
  let ready
  const calls=[]
  const writes=[]
  const paged=(results,next=null,count=results.length)=>({count,next,previous:null,results})
  await page.unroute('**/api/**')
  await page.evaluate(()=>localStorage.setItem('bee_access','synthetic-local-review'))
  await page.route('**/api/**',async route=>{
    const request=route.request()
    const url=new URL(request.url())
    const path=url.pathname.replace(/^.*\/api\/v1/,'')
    calls.push({role,path,method:request.method(),page:url.searchParams.get('page'),period:url.searchParams.get('periode')})
    if(request.method()!=='GET'){
      const payload=request.postDataJSON()
      writes.push({role,path,method:request.method(),payload})
      if(path==='/kegiatan/1/realisasi/' && role==='TeacherInCharge'){
        if(failSave)return route.fulfill({status:503,json:{detail:'Synthetic temporary failure'}})
        const current=rows.find(row=>row.id===1)
        const cents=Math.round(Number(current.realisasi)*100)+Math.round(payload.nominal*100)
        rows=rows.map(row=>row.id!==1?row:{...row,realisasi:(cents/100).toFixed(2),sisa_pagu:((Math.round(Number(row.pagu)*100)-cents)/100).toFixed(2),rasio_utilisasi:cents/(Number(row.pagu)*100)})
        details[1]=[...details[1],{tanggal:payload.tanggal,deskripsi:payload.deskripsi,nominal:payload.nominal.toFixed(2)}]
        return route.fulfill({status:201,json:{detail:'Contoh tercatat',realisasi_id:4,jurnal_id:'CONTOH-JURNAL'}})
      }
      if(path==='/kegiatan/' && request.method()==='POST' && role==='SchoolPrincipal'){
        const created={...fixtures.rows[1],...payload,id:4,realisasi:'0.00',sisa_pagu:payload.pagu,rasio_utilisasi:0,periode_kode:'2026/2027'}
        rows.push(created);details[4]=[]
        return route.fulfill({status:201,json:created})
      }
      return route.fulfill({status:405,json:{detail:'Local review: mutation disabled'}})
    }
    let data=paged([])
    if(path==='/auth/me/')data={id:1,username:'contoh',nama:'Pengguna Contoh',is_superuser:false,groups:[role]}
    else if(path==='/kegiatan/'){
      if(failList)return route.fulfill({status:503,json:{detail:'Synthetic failure'}})
      const period=Number(url.searchParams.get('periode'))
      if(holdPeriod && period===1)await new Promise(resolve=>{releasePeriod=resolve;readyResolve()})
      const filtered=period?rows.filter(row=>row.periode===period):rows
      const page=Number(url.searchParams.get('page')??1)
      data=paged(filtered.slice((page-1)*2,page*2),page*2<filtered.length?`http://127.0.0.1:4173/api/v1/kegiatan/?page=${page+1}`:null,filtered.length)
    }else if(path==='/periode/'){
      if(failPeriods)return route.fulfill({status:503,json:{detail:'Synthetic failure'}})
      data=paged(fixtures.periods)
    }else if(path==='/coa/')data=paged(fixtures.accounts)
    else if(path==='/pegawai/')data=paged(fixtures.staff)
    else if(/^\/kegiatan\/\d+\/laporan\/$/.test(path)){
      const row=rows.find(row=>row.id===Number(path.split('/')[2]))
      data={kegiatan:row.nama,pagu:row.pagu,realisasi:row.realisasi,sisa_pagu:row.sisa_pagu,rasio_utilisasi:row.rasio_utilisasi,rincian:details[row.id]??[]}
    }
    return route.fulfill({status:200,json:data})
  })
  try{
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/kegiatan')
    await page.getByText('Menampilkan 1–3 dari 3 kegiatan',{exact:true}).waitFor()
    if(calls.some(call=>call.role==='TeacherInCharge' && ['/coa/','/pegawai/'].includes(call.path)))throw new Error('Teacher requested management-only options')
    if(await page.getByRole('button',{name:'Buat kegiatan',exact:true}).count())throw new Error('Teacher can create activity')
    if(await page.getByRole('button',{name:/Tindakan kegiatan/}).count())throw new Error('Teacher sees management menu')
    await page.evaluate(()=>document.fonts.ready)
    await page.screenshot({path:'design-artifacts/bee-design-system/role-TeacherInCharge-kegiatan-05.png',scale:'css',animations:'disabled'})
    await page.getByRole('button',{name:'Catat realisasi Pekan membaca',exact:true}).click()
    const d=page.getByRole('dialog',{name:'Catat realisasi',exact:true})
    await d.getByRole('button',{name:'Catat realisasi',exact:true}).click()
    await d.getByText(/Isi nominal lebih dari nol/).waitFor()
    if(writes.length)throw new Error('Zero realization was sent')
    await d.locator('#realisasi-amount').fill('5800000,01')
    await d.locator('#realisasi-amount').press('Tab')
    await d.getByRole('button',{name:'Catat realisasi',exact:true}).click()
    if(writes.length)throw new Error('Over-budget realization was sent')
    await d.locator('#realisasi-amount').fill('150000,25')
    await d.locator('#realisasi-date').fill('16/10/2026')
    await d.locator('#realisasi-date').press('Tab')
    await d.locator('#realisasi-description').fill('Pembelian alat peraga contoh')
    await d.getByRole('button',{name:'Catat realisasi',exact:true}).click()
    await d.getByText(/Periksa laporan sebelum mengirim ulang/).waitFor()
    const retained=await d.locator('#realisasi-description').inputValue()
    if(retained!=='Pembelian alat peraga contoh')throw new Error('Realization input was lost after error')
    await d.getByRole('button',{name:'Periksa laporan kegiatan',exact:true}).click()
    const report=page.getByRole('dialog',{name:'Laporan kegiatan',exact:true})
    await report.getByText('Pembelian buku contoh',{exact:true}).waitFor()
    await report.getByRole('button',{name:'Tutup',exact:true}).click()
    failSave=false
    await d.getByRole('button',{name:'Catat realisasi',exact:true}).click()
    await d.waitFor({state:'hidden'})
    if(writes[0].payload.tanggal!=='2026-10-16'||writes[0].payload.nominal!==150000.25)throw new Error('Realization payload changed date or precision')
    await page.getByRole('button',{name:'Laporan Pekan membaca',exact:true}).click()
    await report.getByText('Pembelian alat peraga contoh',{exact:true}).waitFor()
    await report.getByRole('button',{name:'Tutup',exact:true}).click()
    await page.setViewportSize({width:320,height:800})
    await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth)
    await page.evaluate(()=>scrollTo(0,0))
    await page.screenshot({path:'design-artifacts/bee-design-system/role-TeacherInCharge-mobile-05.png',scale:'css',animations:'disabled'})
    await page.locator('.kegiatan-mobile').getByRole('button',{name:'Catat realisasi',exact:true}).first().click()
    await d.waitFor()
    const mobile=await d.evaluate(el=>({scroll:el.scrollWidth,client:el.clientWidth,viewport:innerWidth}))
    if(mobile.scroll>mobile.client)throw new Error('Realization dialog overflows mobile')
    await d.getByRole('button',{name:'Batal',exact:true}).click()
    role='SchoolPrincipal'
    await page.setViewportSize({width:1440,height:1000})
    await page.reload()
    await page.getByRole('button',{name:'Buat kegiatan',exact:true}).waitFor()
    await page.getByText('Menampilkan 1–3 dari 3 kegiatan',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Buat kegiatan',exact:true}).click()
    const form=page.getByRole('dialog',{name:'Buat kegiatan',exact:true})
    await form.getByRole('button',{name:'Buat kegiatan',exact:true}).click()
    await form.getByText('Isi nama kegiatan.',{exact:true}).waitFor()
    const before=writes.length
    await form.locator('#activity-name').fill('Kegiatan uji lokal')
    await form.locator('#activity-account').click()
    await page.getByRole('option',{name:'Beban kegiatan sekolah',exact:true}).click()
    await form.locator('#activity-budget').fill('1250000,50')
    await form.locator('#activity-start').fill('16/10/2026')
    await form.locator('#activity-start').press('Tab')
    await form.locator('#activity-end').fill('15/10/2026')
    await form.locator('#activity-end').press('Tab')
    await form.getByRole('button',{name:'Buat kegiatan',exact:true}).click()
    await form.getByText('Tanggal selesai tidak boleh sebelum tanggal mulai.',{exact:true}).waitFor()
    if(writes.length!==before)throw new Error('Invalid activity dates were sent')
    await form.locator('#activity-end').fill('31/10/2026')
    await form.locator('#activity-end').press('Tab')
    await form.getByRole('button',{name:'Buat kegiatan',exact:true}).click()
    await form.waitFor({state:'hidden'})
    const created=writes.find(item=>item.path==='/kegiatan/'&&item.method==='POST').payload
    if(created.tanggal_mulai!=='2026-10-16'||created.tanggal_selesai!=='2026-10-31'||created.pagu!=='1250000.50')throw new Error('Activity create contract changed')
    await page.getByText('Kegiatan uji lokal',{exact:true}).first().waitFor()
    await page.getByRole('button',{name:'Tindakan kegiatan Pekan membaca',exact:true}).click()
    if(await page.getByRole('menuitem',{name:'Hapus kegiatan',exact:true}).count())throw new Error('Activity with realization can be deleted')
    await page.keyboard.press('Escape')
    await page.getByRole('button',{name:'Tindakan kegiatan Kunjungan edukasi',exact:true}).click()
    await page.getByRole('menuitem',{name:'Hapus kegiatan',exact:true}).waitFor()
    await page.keyboard.press('Escape')
    await page.screenshot({path:'design-artifacts/bee-design-system/role-SchoolPrincipal-kegiatan-05.png',scale:'css',animations:'disabled'})
    holdPeriod=true
    ready=new Promise(resolve=>{readyResolve=resolve})
    await page.locator('#kegiatan-period').click()
    await page.getByRole('option',{name:'2026/2027',exact:true}).click()
    await ready
    await page.locator('#kegiatan-period').click()
    await page.getByRole('option',{name:'2025/2026',exact:true}).click()
    await page.getByText('Menampilkan 1–1 dari 1 kegiatan',{exact:true}).waitFor()
    const old=page.waitForResponse(response=>response.url().includes('/kegiatan/')&&new URL(response.url()).searchParams.get('periode')==='1')
    releasePeriod();holdPeriod=false
    await (await old).finished()
    await page.evaluate(()=>new Promise(requestAnimationFrame))
    const current=await page.locator('.kegiatan-desktop tbody').innerText()
    if(!current.includes('Pentas akhir tahun')||current.includes('Pekan membaca'))throw new Error('Stale period replaced current activities')
    failPeriods=true
    await page.reload()
    await page.getByText('Pilihan tahun pelajaran belum berhasil dimuat. Daftar kegiatan tetap tersedia.',{exact:true}).waitFor()
    await page.getByText('Menampilkan 1–4 dari 4 kegiatan',{exact:true}).waitFor()
    failList=true
    await page.reload()
    await page.getByText('Kegiatan belum berhasil dimuat. Periksa koneksi, lalu coba lagi.',{exact:true}).waitFor()
    if(await page.getByRole('heading',{name:'Belum ada kegiatan',exact:true}).count())throw new Error('Failure shown as empty data')
    return {teacherManagementRequests:calls.filter(call=>call.role==='TeacherInCharge'&&['/coa/','/pegawai/'].includes(call.path)),laterPageLoaded:calls.some(call=>call.path==='/kegiatan/'&&call.page==='2'),retained,mobile,created,realization:writes[0].payload,stalePeriodIgnored:true,scope:'All API requests intercepted. Realization retry is a simulated rejection/retry, not a backend idempotency guarantee',writes:writes.map(item=>({role:item.role,path:item.path,method:item.method}))}
  }finally{
    releasePeriod?.()
    await page.unroute('**/api/**')
    await page.goto('http://127.0.0.1:4173/design-system.html#layar-kegiatan')
    await page.evaluate(()=>localStorage.removeItem('bee_access'))
  }
}
