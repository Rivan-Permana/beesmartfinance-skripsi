async(page)=>{
  await page.goto('http://127.0.0.1:4173/login')
  const year=new Date().getFullYear()
  const row=(code,name,normal,debit,credit,balance)=>({kode_akun:code,nama_akun:name,posisi_normal:normal,total_debit:debit,total_kredit:credit,saldo_akhir:balance})
  const neraca=[row('111','Kas sekolah','D','1000.25','0','1000.25'),row('311','Modal awal','K','0','1000.25','1000.25'),row('411','Pendapatan SPP','K','0','250.50','250.50'),row('511','Beban bahan pembelajaran','D','50.00','0','50.00')]
  const lr={pendapatan:[row('411','Pendapatan SPP','K','0','250.50','250.50')],beban:[row('511','Beban bahan pembelajaran','D','50','0','50')],total_pendapatan:'250.50',total_beban:'50.00',laba_rugi:'200.50'}
  const posisi={aset:[row('111','Kas sekolah','D','1500.25','0','1500.25'),row('129','Akumulasi penyusutan','K','0','250','250')],liabilitas:[row('211','Utang usaha','K','0','250.25','250.25')],ekuitas:[row('311','Modal awal','K','0','1000','1000')]}
  const budgets=[{kode_akun:'511',nama_akun:'Bahan pembelajaran',tahun_anggaran:year,pagu:'1000',realisasi:'996',sisa_pagu:'4'},{kode_akun:'512',nama_akun:'Kegiatan sekolah',tahun_anggaran:year,pagu:'1000',realisasi:'1500',sisa_pagu:'-500'},{kode_akun:'513',nama_akun:'Pagu belum ditetapkan',tahun_anggaran:year,pagu:'0',realisasi:'50',sisa_pagu:'-50'}]
  const ledger=[{tanggal:`${year}-02-01`,no_bukti:'SALDO-AWAL',keterangan:'Saldo awal periode',debit:'0',kredit:'1000.25'},{tanggal:`${year}-02-05`,no_bukti:'BKT-SPP-001',keterangan:'Penerimaan SPP contoh',debit:'0',kredit:'250.50'},{tanggal:`${year}-02-06`,no_bukti:'BKT-KOREKSI',keterangan:'Koreksi tercatat contoh',debit:'50',kredit:'0'}]
  const accounts=[{kode_akun:'411',nama_akun:'Pendapatan SPP',posisi_normal:'K',is_active:false,sub_golongan:null,saldo_awal:'0',tanggal_saldo_awal:null}]
  const calls=[],writes=[],errors=[]
  let role='Finance',failReport=false,failAccounts=false,holdYear=false,releaseHeld
  const onError=error=>errors.push(error.message)
  page.on('pageerror',onError)
  await page.unroute('**/api/**')
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,'')
    calls.push({role,path,method:request.method(),params:Object.fromEntries(url.searchParams)})
    if(request.method()!=='GET'){writes.push(path);return route.fulfill({status:405,json:{detail:'Read-only local review'}})}
    if(path==='/auth/me/')return route.fulfill({status:200,json:{id:1,username:'contoh',nama:'Pengguna contoh',is_superuser:false,groups:[role]}})
    if(path==='/coa/')return route.fulfill(failAccounts?{status:503,json:{detail:'Synthetic account failure'}}:{status:200,json:{count:accounts.length,next:null,previous:null,results:accounts}})
    if(path.startsWith('/laporan/')){
      if(failReport)return route.fulfill({status:503,json:{detail:'Synthetic report failure'}})
      if(holdYear&&path==='/laporan/neraca-saldo/'&&Number(url.searchParams.get('tahun'))===year-1)await new Promise(resolve=>{releaseHeld=resolve})
      let data=[]
      if(path==='/laporan/neraca-saldo/')data=Number(url.searchParams.get('tahun'))===year-1?neraca.map(item=>({...item,nama_akun:`HASIL LAMA ${item.nama_akun}`})):neraca
      if(path==='/laporan/laba-rugi/')data=lr
      if(path==='/laporan/posisi-keuangan/')data=posisi
      if(path==='/laporan/realisasi-anggaran/')data=budgets
      if(path==='/laporan/buku-besar/411/')data=ledger.map(item=>({...item,tanggal:item.tanggal.replace(String(year),url.searchParams.get('tahun'))}))
      return route.fulfill({status:200,json:data})
    }
    return route.fulfill({status:200,json:{count:0,next:null,previous:null,results:[]}})
  })
  try{
    await page.evaluate(()=>{localStorage.setItem('bee_access','synthetic-local-review');localStorage.removeItem('bee_refresh')})
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/laporan')
    await page.locator('.report-table').getByText('Kas sekolah',{exact:true}).waitFor()
    await page.evaluate(()=>document.fonts.ready)
    await page.screenshot({path:'design-artifacts/bee-design-system/laporan-neraca-desktop-07.png',animations:'disabled'})
    if(await page.locator('#report-month').count())throw new Error('Month exposed for annual report')
    if(calls.find(call=>call.path==='/laporan/neraca-saldo/').params.bulan)throw new Error('Annual endpoint received a month')
    await page.locator('#report-year').click()
    await page.getByRole('option',{name:String(year-1),exact:true}).click()
    await page.getByText('Pilihan belum diterapkan.',{exact:false}).waitFor()
    if(await page.locator('.report-applied-period').innerText()!==`Hingga 31 Desember ${year}`)throw new Error('Pending year changed title')
    const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Unduh CSV',exact:true}).click()])
    if(download.suggestedFilename()!==`neraca-saldo-${year}.csv`)throw new Error('CSV uses unapplied year')
    await page.evaluate(()=>{window.__reportPrint=null;window.print=()=>{window.__reportPrint={period:document.querySelector('.report-applied-period')?.textContent,title:document.querySelector('.report-document h2')?.textContent,rows:document.querySelectorAll('.report-table tbody tr').length}}})
    await page.getByRole('button',{name:'Cetak laporan',exact:true}).click()
    const printed=await page.evaluate(()=>window.__reportPrint)
    if(printed.period!==`Hingga 31 Desember ${year}`||printed.rows!==4)throw new Error('Print scope changed before Apply')
    await page.emulateMedia({media:'print'})
    const printView=await page.evaluate(()=>({controls:getComputedStyle(document.querySelector('.report-controls')).display,tabs:getComputedStyle(document.querySelector('.p-tablist')).display,brand:getComputedStyle(document.querySelector('.report-print-brand')).display,title:document.querySelector('.report-document h2')?.textContent}))
    if(printView.controls!=='none'||printView.tabs!=='none'||printView.brand==='none')throw new Error('Print hides wrong content')
    await page.screenshot({path:'design-artifacts/bee-design-system/laporan-print-07.png',animations:'disabled'})
    await page.emulateMedia({media:'screen'})
    holdYear=true
    await page.getByRole('button',{name:'Terapkan',exact:true}).click()
    if(!await page.getByRole('button',{name:'Cetak laporan',exact:true}).isDisabled())throw new Error('Print enabled during loading')
    await page.getByRole('tab',{name:'Laba rugi',exact:true}).click()
    await page.getByText('Laba periode',{exact:true}).waitFor()
    if(await page.locator('.report-applied-period').innerText()!==`Januari–Desember ${year-1}`)throw new Error('Applied scope was not shared across reports')
    releaseHeld();holdYear=false
    await page.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/laporan/neraca-saldo/'))
    if(await page.getByText(/HASIL LAMA/).count())throw new Error('Late response replaced current report')
    await page.screenshot({path:'design-artifacts/bee-design-system/laporan-laba-rugi-07.png',animations:'disabled'})
    await page.getByRole('tab',{name:'Posisi keuangan',exact:true}).click()
    await page.getByText('Total aset',{exact:true}).first().waitFor()
    const totals=await page.locator('.report-result').innerText()
    if(!totals.includes('Rp 1.250,25')||!totals.includes('Rp 0'))throw new Error('Contra account position totals incorrect')
    await page.getByRole('tab',{name:'Realisasi anggaran',exact:true}).click()
    await page.getByText('99,6%',{exact:true}).waitFor()
    await page.getByText('150%',{exact:true}).waitFor()
    await page.getByText('Persentase tidak tersedia',{exact:true}).waitFor()
    await page.screenshot({path:'design-artifacts/bee-design-system/laporan-anggaran-07.png',animations:'disabled'})
    failAccounts=true
    await page.getByRole('tab',{name:'Buku besar',exact:true}).click()
    await page.getByRole('button',{name:'Muat ulang akun',exact:true}).waitFor()
    if(calls.some(call=>call.path==='/laporan/buku-besar/411/'))throw new Error('Ledger requested before account chosen')
    failAccounts=false
    await page.getByRole('button',{name:'Muat ulang akun',exact:true}).click()
    await page.locator('#report-account').click()
    await page.getByRole('option',{name:'Pendapatan SPP',exact:true}).click()
    await page.getByRole('listbox').waitFor({state:'hidden'})
    await page.locator('#report-month').click()
    await page.getByRole('option',{name:'Februari',exact:true}).click()
    await page.getByRole('button',{name:'Terapkan',exact:true}).click()
    await page.locator('.report-ledger-summary').getByText('Rp 1.200,75',{exact:true}).waitFor()
    const ledgerCall=calls.filter(call=>call.path==='/laporan/buku-besar/411/').at(-1)
    if(ledgerCall.params.bulan!=='2'||ledgerCall.params.tahun!==String(year-1))throw new Error('Ledger monthly scope changed')
    await page.screenshot({path:'design-artifacts/bee-design-system/laporan-buku-besar-07.png',animations:'disabled'})
    const viewports=[]
    for(const width of [1440,1024,768,390,320]){
      await page.setViewportSize({width,height:1000})
      const geometry=await page.evaluate(()=>({width:innerWidth,page:document.documentElement.scrollWidth,table:document.querySelector('.report-scroll').scrollWidth,tableClient:document.querySelector('.report-scroll').clientWidth}))
      if(geometry.page>width)throw new Error('Report page overflow at '+width)
      if(await page.locator('#report-kind').isVisible()){
        if(!(await page.locator('#report-kind').innerText()).includes('Buku besar'))throw new Error('Active report hidden in mobile navigation')
      }
      viewports.push(geometry)
    }
    await page.screenshot({path:'design-artifacts/bee-design-system/laporan-buku-besar-mobile-07.png',animations:'disabled'})
    await page.locator('.report-scroll').focus()
    await page.locator('.report-scroll').press('End')
    await page.setViewportSize({width:1440,height:1000})
    failReport=true
    await page.getByRole('button',{name:'Terapkan',exact:true}).click()
    await page.getByRole('button',{name:'Muat ulang laporan',exact:true}).waitFor()
    if(await page.locator('.report-table').count())throw new Error('Failed report retains old values')
    if(!await page.getByRole('button',{name:'Cetak laporan',exact:true}).isDisabled())throw new Error('Print enabled after failure')
    failReport=false
    await page.getByRole('button',{name:'Muat ulang laporan',exact:true}).click()
    await page.locator('.report-ledger-summary').getByText('Rp 1.200,75',{exact:true}).waitFor()
    role='SchoolPrincipal'
    await page.reload()
    await page.locator('.report-table').getByText('Kas sekolah',{exact:true}).waitFor()
    await page.screenshot({path:'design-artifacts/bee-design-system/role-Principal-laporan-07.png',animations:'disabled'})
    if(writes.length)throw new Error('Report sent API mutations')
    if(errors.length)throw new Error(errors.join('\n'))
    return {ok:true,writes:writes.length,viewports,printScope:printed,csv:download.suggestedFilename(),checks:['annual vs ledger monthly scopes','unapplied filter','stale response ignored','CSV and print applied scope','contra account totals','zero/99.6/150 percent','COA failure recovery','credit-normal opening ledger','report failure removes data and blocks print','both roles'],errors}
  }finally{
    if(releaseHeld)releaseHeld()
    await page.unroute('**/api/**')
    page.off('pageerror',onError)
    await page.emulateMedia({media:'screen'})
    await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh')})
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/login')
  }
}
