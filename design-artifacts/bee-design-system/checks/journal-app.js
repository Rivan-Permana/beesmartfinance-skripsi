async(page)=>{
  await page.goto('http://127.0.0.1:4173/design-system.html')
  const fixtures=await page.evaluate(async()=>{const m=await import('/src/design-system/journal-fixtures.ts');return JSON.parse(JSON.stringify({rows:m.journalSamples,accounts:m.journalAccounts}))})
  let rows=[...fixtures.rows,...Array.from({length:5},(_,i)=>({...fixtures.rows[0],id:`extra-${i}`,no_bukti:`EXTRA-${i}`}))]
  let role='Finance',failSave=true,failPost=true,failList=false,failAccounts=false
  let releaseCreate
  const calls=[],writes=[],errors=[]
  const onError=e=>errors.push(e.message)
  page.on('pageerror',onError)
  const paged=results=>({count:results.length,next:null,previous:null,results})
  await page.unroute('**/api/**')
  await page.evaluate(()=>localStorage.setItem('bee_access','synthetic-local-review'))
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,'')
    calls.push({role,path,method:request.method(),params:Object.fromEntries(url.searchParams)})
    if(request.method()!=='GET'){
      const payload=request.postData()?request.postDataJSON():null
      writes.push({role,path,method:request.method(),payload})
      if(path==='/jurnal/'&&request.method()==='POST'&&role==='Finance'){
        if(failSave)return route.fulfill({status:503,json:{detail:'Synthetic failure'}})
        await new Promise(resolve=>{releaseCreate=resolve})
        const row={...fixtures.rows[0],...payload,id:'created-local'}
        rows=[row,...rows]
        return route.fulfill({status:201,json:row})
      }
      if(path==='/jurnal/created-local/catat/'&&role==='Finance'){
        if(failPost)return route.fulfill({status:503,json:{detail:'Synthetic posting response failure'}})
        rows=rows.map(row=>row.id==='created-local'?{...row,status:'POSTED'}:row)
        return route.fulfill({status:200,json:rows.find(row=>row.id==='created-local')})
      }
      if(path==='/jurnal/001/'&&request.method()==='PUT'&&role==='Finance'){
        rows=rows.map(row=>row.id==='001'?{...row,...payload}:row)
        return route.fulfill({status:200,json:rows.find(row=>row.id==='001')})
      }
      if(path==='/jurnal/extra-0/'&&request.method()==='DELETE'&&role==='Finance'){rows=rows.filter(row=>row.id!=='extra-0');return route.fulfill({status:204,body:''})}
      if(path==='/jurnal/007/submit/'&&role==='Finance'){rows=rows.map(row=>row.id==='007'?{...row,status:'PENDING'}:row);return route.fulfill({status:200,json:rows.find(row=>row.id==='007')})}
      if(path==='/jurnal/002/batal-penerimaan/'&&role==='Finance'){
        if(!payload.alasan)return route.fulfill({status:400,json:{detail:'Reason required'}})
        rows=rows.map(row=>row.id==='002'?{...row,status:'VOID'}:row);return route.fulfill({status:200,json:rows.find(row=>row.id==='002')})
      }
      if(path==='/jurnal/005/void/'&&role==='SchoolPrincipal'){
        const original=rows.find(row=>row.id==='005')
        const reversal={...original,id:'reversal-local',no_bukti:'REV-CONTOH-005',tipe_sumber:'REVERSAL',can_finance_post:false,detail:original.detail.map(line=>({...line,debit:line.kredit,kredit:line.debit}))}
        rows=[reversal,...rows]
        return route.fulfill({status:201,json:{detail:'Jurnal pembalik contoh dicatat.',pembalik:reversal}})
      }
      if(path==='/jurnal/003/approve/'&&role==='SchoolPrincipal'){
        rows=rows.map(row=>row.id==='003'?{...row,status:'POSTED',approved_by:2}:row)
        return route.fulfill({status:200,json:rows.find(row=>row.id==='003')})
      }
      return route.fulfill({status:405,json:{detail:'Local review blocked this mutation'}})
    }
    let data=paged([])
    if(path==='/auth/me/')data={id:role==='SchoolPrincipal'?2:1,username:'contoh',nama:'Pengguna contoh',is_superuser:false,groups:[role]}
    else if(path==='/coa/'){
      if(failAccounts)return route.fulfill({status:503,json:{detail:'Synthetic account failure'}})
      data=paged(fixtures.accounts)
    }else if(path==='/jurnal/'){
      if(failList)return route.fulfill({status:503,json:{detail:'Synthetic list failure'}})
      const search=(url.searchParams.get('search')??'').toLowerCase(),status=url.searchParams.get('status'),kind=url.searchParams.get('jenis')
      const filtered=rows.filter(row=>(!search||`${row.no_bukti} ${row.keterangan}`.toLowerCase().includes(search))&&(!status||row.status===status)&&(!kind||row.detail.some(line=>line.kode_akun.startsWith(kind==='masuk'?'4':'5'))))
      const number=Number(url.searchParams.get('page')??1)
      if((number-1)*10>=filtered.length&&number>1)return route.fulfill({status:404,json:{detail:'Invalid page'}})
      data={count:filtered.length,next:number*10<filtered.length?'fixture-next':null,previous:null,results:filtered.slice((number-1)*10,number*10)}
    }else if(/^\/jurnal\/[^/]+\/$/.test(path))data=rows.find(row=>row.id===path.split('/')[2])
    return route.fulfill({status:200,json:data})
  })
  try{
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/jurnal?jenis=keluar')
    await page.getByText('1–10 dari 11 jurnal',{exact:true}).waitFor()
    if(calls.find(call=>call.path==='/jurnal/').params.jenis!=='keluar')throw new Error('Journal alias lost query filter')
    await page.screenshot({path:'design-artifacts/bee-design-system/role-Finance-jurnal-06.png',animations:'disabled'})
    await page.getByRole('button',{name:'Halaman berikutnya',exact:true}).click()
    await page.getByText('11–11 dari 11 jurnal',{exact:true}).waitFor()
    const before=calls.filter(call=>call.path==='/jurnal/').length
    await page.locator('#journal-search').fill('CONTOH-001')
    if(calls.filter(call=>call.path==='/jurnal/').length!==before)throw new Error('Unapplied search changed results')
    await page.getByRole('button',{name:'Terapkan',exact:true}).click()
    await page.getByText('1–1 dari 1 jurnal',{exact:true}).waitFor()
    const searchCall=calls.filter(call=>call.path==='/jurnal/').at(-1)
    if(searchCall.params.page!=='1'||searchCall.params.search!=='CONTOH-001'||searchCall.params.jenis!=='keluar')throw new Error('Search/page scope changed')
    await page.getByRole('button',{name:'Reset filter',exact:true}).click()
    await page.getByText('1–10 dari 11 jurnal',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Buat jurnal',exact:true}).click()
    const form=page.getByRole('dialog',{name:'Buat jurnal',exact:true})
    await form.locator('#journal-proof').fill('LOCAL-TEST-001')
    await form.locator('#journal-description').fill('Nominal desimal contoh')
    await form.locator('#journal-date').fill('16/10/2026')
    await form.locator('#journal-date').press('Tab')
    await form.locator('#journal-account-0').click()
    await page.getByRole('option',{name:'Bahan pembelajaran',exact:true}).click()
    await page.getByRole('listbox').waitFor({state:'hidden'})
    await form.locator('#journal-account-1').click()
    await page.getByRole('option',{name:'Kas sekolah',exact:true}).click()
    await page.getByRole('listbox').waitFor({state:'hidden'})
    await form.locator('#journal-debit-0').fill('1250000,50')
    await form.locator('#journal-debit-0').press('Tab')
    await form.locator('#journal-credit-1').fill('1250000,50')
    await form.locator('#journal-credit-1').press('Tab')
    await form.locator('#journal-account-0').click()
    await page.getByRole('listbox').waitFor()
    await form.evaluate(e=>e.querySelector('form').requestSubmit())
    await form.getByText(/Input tetap ada/).waitFor()
    await page.getByRole('listbox').waitFor({state:'hidden'})
    if(await form.locator('#journal-proof').inputValue()!=='LOCAL-TEST-001')throw new Error('Input lost after failed save')
    failSave=false
    await form.locator('#journal-date').click()
    await page.locator('.p-datepicker-panel').waitFor()
    await form.evaluate(e=>e.querySelector('form').requestSubmit())
    await page.waitForFunction(()=>document.querySelector('.journal-form-fields')?.disabled===true)
    await page.locator('.p-datepicker-panel').waitFor({state:'hidden'})
    await page.keyboard.press('Escape')
    if(!await form.isVisible())throw new Error('Pending form closed on Escape')
    releaseCreate()
    await form.waitFor({state:'hidden'})
    const payload=writes.filter(write=>write.path==='/jurnal/').at(-1).payload
    if(payload.tanggal!=='2026-10-16'||payload.detail[0].debit!=='1250000.50'||payload.detail[1].kredit!=='1250000.50')throw new Error('Precision/local date changed')
    await page.getByRole('button',{name:'Periksa jurnal LOCAL-TEST-001',exact:true}).filter({visible:true}).click()
    const detail=page.getByRole('dialog',{name:'Rincian jurnal',exact:true})
    await detail.getByRole('button',{name:'Catat ke buku besar',exact:true}).click()
    const confirmation=page.getByRole('dialog',{name:'Catat ke buku besar',exact:true})
    await confirmation.getByRole('button',{name:'Catat ke buku besar',exact:true}).click()
    await confirmation.getByRole('button',{name:'Periksa ulang daftar',exact:true}).waitFor()
    await confirmation.getByRole('button',{name:'Periksa ulang daftar',exact:true}).click()
    await confirmation.getByRole('button',{name:'Periksa ulang daftar',exact:true}).waitFor({state:'hidden'})
    if(!calls.some(call=>call.path==='/jurnal/created-local/'&&call.method==='GET'))throw new Error('Failed action did not retrieve current status')
    failPost=false
    await confirmation.getByRole('button',{name:'Catat ke buku besar',exact:true}).click()
    await confirmation.waitFor({state:'hidden'})
    await page.goto('http://127.0.0.1:4173/jurnal')
    await page.getByText('1–10 dari 13 jurnal',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Periksa jurnal CONTOH-001',exact:true}).filter({visible:true}).click()
    await detail.getByRole('button',{name:'Ubah draf',exact:true}).click()
    const edit=page.getByRole('dialog',{name:'Ubah draf jurnal',exact:true})
    await edit.locator('#journal-description').fill('Keterangan diubah di fixture')
    await edit.getByRole('button',{name:'Simpan draf',exact:true}).click()
    await edit.waitFor({state:'hidden'})
    await detail.getByText('Keterangan diubah di fixture',{exact:true}).waitFor()
    await detail.getByRole('button',{name:'Tutup rincian',exact:true}).click()
    for(const [proof,label] of [['CONTOH-007','Ajukan persetujuan'],['EXTRA-0','Hapus draf'],['CONTOH-002','Batalkan penerimaan']]){
      await page.getByRole('button',{name:`Periksa jurnal ${proof}`,exact:true}).filter({visible:true}).click()
      await detail.getByRole('button',{name:label,exact:true}).click()
      const dialog=page.getByRole('dialog',{name:label,exact:true})
      if(label==='Batalkan penerimaan'){
        const before=writes.length
        await dialog.getByRole('button',{name:label,exact:true}).click()
        if(writes.length!==before)throw new Error('Empty cancellation reason sent')
        await dialog.locator('#journal-cancel-reason').fill('Bukti penerimaan contoh keliru')
      }
      await dialog.getByRole('button',{name:label,exact:true}).click()
      await dialog.waitFor({state:'hidden'})
    }
    if(writes.find(write=>write.path==='/jurnal/002/batal-penerimaan/').payload.alasan!=='Bukti penerimaan contoh keliru')throw new Error('Cancellation reason payload changed')
    role='SchoolPrincipal'
    await page.reload()
    await page.getByText('1–10 dari 12 jurnal',{exact:true}).waitFor()
    if(await page.getByRole('button',{name:'Buat jurnal',exact:true}).count())throw new Error('Principal sees journal creation')
    await page.getByRole('button',{name:'Periksa jurnal CONTOH-006',exact:true}).filter({visible:true}).click()
    if(await detail.getByRole('button',{name:'Setujui dan catat',exact:true}).count())throw new Error('Own approval exposed')
    await detail.getByRole('button',{name:'Tutup rincian',exact:true}).click()
    await page.getByRole('button',{name:'Periksa jurnal CONTOH-003',exact:true}).filter({visible:true}).click()
    await detail.getByRole('button',{name:'Setujui dan catat',exact:true}).click()
    const approval=page.getByRole('dialog',{name:'Setujui dan catat',exact:true})
    await approval.getByRole('button',{name:'Setujui dan catat',exact:true}).click()
    await approval.waitFor({state:'hidden'})
    await page.getByRole('button',{name:'Periksa jurnal CONTOH-005',exact:true}).filter({visible:true}).click()
    await detail.getByRole('button',{name:'Buat jurnal pembalik',exact:true}).click()
    const reversal=page.getByRole('dialog',{name:'Buat jurnal pembalik',exact:true})
    await reversal.getByRole('button',{name:'Buat jurnal pembalik',exact:true}).click()
    await reversal.waitFor({state:'hidden'})
    await page.getByRole('button',{name:'Periksa jurnal REV-CONTOH-005',exact:true}).filter({visible:true}).waitFor()
    await page.setViewportSize({width:320,height:800})
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Production journal page overflows 320px')
    await page.screenshot({path:'design-artifacts/bee-design-system/role-Principal-jurnal-mobile-06.png',animations:'disabled'})
    failAccounts=true
    await page.reload()
    await page.getByText('1–10 dari 13 jurnal',{exact:true}).waitFor()
    await page.getByText('Daftar akun belum berhasil dimuat.',{exact:false}).waitFor()
    if(await page.getByRole('button',{name:/Periksa jurnal CONTOH-001/}).filter({visible:true}).count()!==1)throw new Error('Accounts failure hid journals')
    failList=true
    await page.reload()
    await page.getByRole('button',{name:'Muat ulang jurnal',exact:true}).waitFor()
    if(await page.getByText('Belum ada jurnal',{exact:true}).count())throw new Error('List failure shown as empty data')
    failList=false;failAccounts=false
    await page.getByRole('button',{name:'Muat ulang jurnal',exact:true}).click()
    await page.getByText('1–10 dari 13 jurnal',{exact:true}).waitFor()
    if(errors.length)throw new Error(errors.join('\n'))
    return {ok:true,writes,checks:['server pagination/search/jenis','filter apply scope','save and action recovery/GET status','pending Escape locked','decimal payload/local date','Finance create/edit/delete/submit/cancel/post','Principal reversal/own approval blocked/eligible allowed','320px','accounts failure independent','list failure retry'],errors}
  }finally{
    if(releaseCreate)releaseCreate()
    await page.unroute('**/api/**')
    page.off('pageerror',onError)
    await page.evaluate(()=>localStorage.removeItem('bee_access'))
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/design-system.html#layar-jurnal')
    await page.reload()
  }
}
