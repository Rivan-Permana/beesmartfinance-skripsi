async(page)=>{
  await page.goto('http://127.0.0.1:4173/login')
  const names=['Alya Putri','Bima Pratama','Citra Maharani','Daffa Ramadhan','Elena Safira','Farhan Akbar','Ghina Azzahra','Hana Kirana']
  const students=Array.from({length:34},(_,i)=>({id:i+1,nama:i<8?names[i]:`Siswa contoh ${String(i+1).padStart(2,'0')}`,nis:`LM-${String(i+1).padStart(3,'0')}`,kelompok:1,status:'aktif',spp_nominal:'750000',nama_ayah:'',kontak_ayah:'',nama_ibu:'',kontak_ibu:'',alamat:'',tanggal_lahir:null,periode:1}))
  const records=Array.from({length:32},(_,i)=>({id:101+i,siswa:i+1,tanggal:'2026-10-15',status:i===26?'sakit':'hadir',ikut_katering:i<4,jemput_datang:i===1,jemput_pulang:i===1}))
  const levels=[{id:2,kode:'PG',nama:'Playgroup'},{id:1,kode:'TK',nama:'Taman kanak-kanak'}]
  const groups=[{id:1,nama:'Melati',jenjang:1,jenjang_kode:'TK'},{id:2,nama:'Mawar',jenjang:1,jenjang_kode:'TK'}]
  let role='Administration',failOnce=true,releasePending,failRead=false
  const calls=[],writes=[],errors=[],viewports=[]
  const onError=e=>errors.push(e.message)
  page.on('pageerror',onError)
  function paged(route,rows,page,size=25){const start=(page-1)*size;return route.fulfill({status:200,json:{count:rows.length,next:start+size<rows.length?'?page='+String(page+1):null,previous:null,results:rows.slice(start,start+size)}})}
  await page.unroute('**/api/**')
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,''),params=Object.fromEntries(url.searchParams),method=request.method(),pageNumber=Number(params.page||1)
    calls.push({path,method,params})
    if(path==='/auth/me/')return route.fulfill({status:200,json:{id:1,username:'contoh',nama:'Pengguna contoh',is_superuser:false,groups:[role]}})
    if(method==='GET'){
      if(path==='/jenjang/')return paged(route,levels,pageNumber,1)
      if(path==='/kelompok/')return paged(route,groups,pageNumber,1)
      if(path==='/siswa/')return paged(route,params.kelompok==='2'?[]:students,pageNumber)
      if(path==='/kehadiran-siswa/'){
        if(failRead)return route.fulfill({status:503,json:{detail:'Kegagalan fixture lokal'}})
        const data=params.tanggal?records.filter(r=>r.tanggal===params.tanggal):records.map(r=>({...r,tanggal:params.tanggal__gte}))
        return paged(route,data,pageNumber)
      }
      return paged(route,[],pageNumber)
    }
    writes.push({path,method,body:method==='DELETE'?null:request.postDataJSON()})
    if(!path.startsWith('/kehadiran-siswa/'))return route.fulfill({status:405,json:{detail:'Fixture only'}})
    if(method==='POST'){
      const body=request.postDataJSON()
      if(body.siswa===33&&failOnce){records.push({id:233,...body});return route.fulfill({status:503,json:{detail:'Respons hilang setelah tersimpan (fixture)'}})}
      if(body.siswa===34&&failOnce){await new Promise(resolve=>releasePending=resolve);failOnce=false;return route.fulfill({status:503,json:{detail:'Belum tersimpan (fixture)'}})}
      if(records.some(r=>r.siswa===body.siswa&&r.tanggal===body.tanggal))return route.fulfill({status:400,json:{detail:'Duplikat fixture'}})
      const row={id:200+body.siswa,...body};records.push(row);return route.fulfill({status:201,json:row})
    }
    const id=Number(path.split('/').filter(Boolean).at(-1)),index=records.findIndex(r=>r.id===id)
    if(method==='PATCH'){Object.assign(records[index],request.postDataJSON());return route.fulfill({status:200,json:records[index]})}
    if(method==='DELETE'){records.splice(index,1);return route.fulfill({status:204,body:''})}
    return route.fulfill({status:405,json:{detail:'Fixture only'}})
  })
  async function select(id,label){await page.locator('#'+id).click();await page.getByRole('option',{name:label,exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'})}
  const student=(name)=>page.getByRole('article',{name:'Absensi '+name,exact:true})
  try{
    await page.evaluate(()=>{localStorage.setItem('bee_access','synthetic-local-review');localStorage.removeItem('bee_refresh')})
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/absensi-siswa')
    await page.locator('#attendance-date').fill('15/10/2026');await page.locator('#attendance-date').press('Tab')
    await select('attendance-level','Taman kanak-kanak');await select('attendance-group','Melati')
    await page.getByRole('button',{name:'Tampilkan siswa',exact:true}).click()
    await student('Siswa contoh 27').waitFor()
    if(await student('Siswa contoh 27').getByRole('button',{name:'Sakit untuk Siswa contoh 27',exact:true}).getAttribute('aria-pressed')!=='true')throw new Error('Existing attendance on page 2 lost')
    if(await page.getByRole('article').count()!==34)throw new Error('Student pagination clipped')
    for(const width of [1440,390]){
      await page.setViewportSize({width,height:1000})
      await page.evaluate(()=>scrollTo(0,1100))
      const mid=await page.evaluate(()=>({top:document.querySelector('.attendance-savebar').getBoundingClientRect().top,position:getComputedStyle(document.querySelector('.attendance-savebar')).position,viewport:innerHeight}))
      if(mid.position!=='static'||mid.top<=mid.viewport)throw new Error('Student save header overlays page during scroll '+JSON.stringify(mid))
      await page.evaluate(()=>scrollTo(0,document.documentElement.scrollHeight))
      const end=await page.evaluate(()=>{const r=document.querySelector('.attendance-savebar').getBoundingClientRect();return {top:r.top,bottom:r.bottom,viewport:innerHeight}})
      if(end.top<0||end.bottom>end.viewport)throw new Error('Student save action unreachable at list end '+JSON.stringify(end))
      await page.screenshot({path:`design-artifacts/bee-design-system/student-save-footer-${width}-012.png`})
    }
    await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>scrollTo(0,0))
    await page.evaluate(()=>document.fonts.ready)
    await page.screenshot({path:'design-artifacts/bee-design-system/absensi-desktop-08.png',animations:'disabled'})
    await page.getByRole('button',{name:'Izin untuk Siswa contoh 27',exact:true}).click()
    await page.getByRole('button',{name:'Izin untuk Siswa contoh 33',exact:true}).click()
    await page.locator('#attendance-date').fill('22/10/2026');await page.locator('#attendance-date').press('Tab')
    await page.locator('#attendance-date').click();await page.locator('.p-datepicker-panel').waitFor()
    await page.getByRole('button',{name:'Simpan absensi',exact:true}).evaluate(e=>e.click())
    await page.waitForFunction(()=>document.querySelector('.attendance-savebar')?.textContent.includes('Menyimpan'))
    await page.locator('.p-datepicker-panel').waitFor({state:'hidden'})
    if(!await page.locator('#attendance-date').isDisabled())throw new Error('Date remains editable during batch')
    if(!await page.getByRole('button',{name:'Hadir untuk Alya Putri',exact:true}).isDisabled())throw new Error('Row editable while batch is pending')
    while(!releasePending)await page.waitForTimeout(10)
    releasePending()
    await page.getByText(/1 catatan berhasil disimpan; 2 belum terkonfirmasi/).waitFor()
    if(await page.getByRole('button',{name:'Izin untuk Siswa contoh 33',exact:true}).getAttribute('aria-pressed')!=='true')throw new Error('Failed draft was lost')
    if(writes.some(w=>w.body&&w.body.tanggal!=='2026-10-15'))throw new Error('Save used unapplied date')
    await page.getByRole('button',{name:'Simpan absensi',exact:true}).click()
    await page.getByText('1 catatan disimpan untuk 2026-10-15.',{exact:true}).first().waitFor()
    if(writes.filter(w=>w.method==='POST'&&w.body.siswa===33).length!==1)throw new Error('Retry duplicated an already committed POST')
    if(writes.filter(w=>w.method==='PATCH'&&w.path.includes('/127/')).length!==1)throw new Error('Successful row was resent')
    await page.getByRole('button',{name:'Izin untuk Bima Pratama',exact:true}).click()
    if(!await page.getByRole('checkbox',{name:'Katering untuk Bima Pratama',exact:true}).isDisabled())throw new Error('Non-attending services not disabled')
    await page.getByRole('button',{name:'Hapus absensi Alya Putri',exact:true}).click()
    await page.getByRole('button',{name:'Hapus catatan',exact:true}).click()
    await page.getByText('Catatan dihapus. Pilihan Hadir pada form belum disimpan kembali.',{exact:true}).waitFor()
    if(await page.getByRole('button',{name:'Izin untuk Bima Pratama',exact:true}).getAttribute('aria-pressed')!=='true')throw new Error('Delete discarded another student draft')
    await page.getByRole('button',{name:'Tampilkan siswa',exact:true}).click()
    await page.getByText('Perubahan belum disimpan',{exact:true}).waitFor()
    await page.getByRole('button',{name:'Tetap di sini',exact:true}).click()
    if(await page.getByRole('button',{name:'Izin untuk Bima Pratama',exact:true}).getAttribute('aria-pressed')!=='true')throw new Error('Cancelled apply discarded input')
    await page.locator('#attendance-date').fill('99/10/2026');await page.locator('#attendance-date').press('Tab')
    const readsBefore=calls.filter(c=>c.path==='/kehadiran-siswa/').length
    await page.getByRole('button',{name:'Tampilkan siswa',exact:true}).click()
    await page.getByText('Periksa atau pilih ulang tanggal yang valid.',{exact:true}).waitFor()
    if(calls.filter(c=>c.path==='/kehadiran-siswa/').length!==readsBefore)throw new Error('Invalid manual date submitted')
    await page.locator('#attendance-date').press('Escape');await page.locator('h1').click();await page.locator('.p-datepicker-panel').waitFor({state:'hidden'})
    for(const width of [1440,1024,768,390,320]){
      await page.setViewportSize({width,height:1000});await page.evaluate(()=>scrollTo(0,0))
      const geo=await page.evaluate(()=>({screen:innerWidth,page:document.documentElement.scrollWidth,buttons:[...document.querySelectorAll('.attendance-status-buttons button')].slice(0,4).map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))}))
      if(geo.page>width||geo.buttons.some(b=>b.height<44))throw new Error('Attendance geometry failed: '+JSON.stringify(geo)+' '+JSON.stringify(await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&getComputedStyle(e).display!=='none').slice(0,10).map(e=>({tag:e.tagName,class:e.className,right:e.getBoundingClientRect().right})))))
      viewports.push({kind:'attendance',...geo})
    }
    await page.locator('#attendance-date').fill('15/10/2026');await page.locator('#attendance-date').press('Tab');await page.locator('#attendance-date').click()
    await page.locator('.p-datepicker-panel').waitFor({state:'visible'})
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Open calendar overflows mobile')
    await page.screenshot({path:'design-artifacts/bee-design-system/absensi-calendar-mobile-08.png',animations:'disabled'})
    await page.locator('#attendance-date').press('Escape');await page.locator('.p-datepicker-panel').waitFor({state:'hidden'})
    await page.evaluate(()=>document.querySelectorAll('.p-toast-close-button').forEach(button=>button.click()))
    await page.getByRole('article',{name:'Absensi Alya Putri',exact:true}).scrollIntoViewIfNeeded()
    await page.screenshot({path:'design-artifacts/bee-design-system/absensi-mobile-08.png',animations:'disabled'})
    await page.getByRole('button',{name:'Hadir untuk Alya Putri',exact:true}).focus()
    if(!await page.getByRole('button',{name:'Hadir untuk Alya Putri',exact:true}).evaluate(e=>e===document.activeElement))throw new Error('Cannot focus attendance choice')
    // Reload clears only fixture drafts; no real API request can escape the handler.
    role='TeacherInCharge'
    await page.evaluate(()=>document.querySelector('#app').__vue_app__.unmount())
    await page.goto('http://127.0.0.1:4173/rekap-siswa')
    await page.getByText('Baca saja. Hubungi Admin TU untuk koreksi absensi.',{exact:true}).waitFor()
    await page.locator('.recap-count').getByText(/dari/).waitFor()
    if(await page.getByRole('link',{name:'Isi absensi',exact:true}).count())throw new Error('Teacher has an edit attendance CTA')
    const applied=await page.locator('.attendance-recap-title h2').innerText()
    await select('recap-period','Juli '+(new Date().getMonth()>=6?new Date().getFullYear():new Date().getFullYear()-1))
    if(await page.locator('.attendance-recap-title h2').innerText()!==applied)throw new Error('Pending month changed result title')
    await page.evaluate(()=>{const original=URL.createObjectURL;URL.createObjectURL=blob=>{window.__attendanceCsv=blob.text();return original(blob)}})
    const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Unduh CSV',exact:true}).click()])
    const csv=await page.evaluate(()=>window.__attendanceCsv)
    if(csv.split('\n').length!==records.length+1)throw new Error('CSV clipped to displayed page')
    await page.locator('[aria-label="Halaman berikutnya"]').click()
    await page.locator('#recap-search').fill('Citra')
    await page.getByText('1–1 dari 1 siswa',{exact:true}).waitFor()
    await page.locator('#recap-search').fill('')
    await page.locator('#recap-only-data').uncheck()
    if(!(await page.locator('.recap-count').innerText()).includes('dari 34'))throw new Error('No-data students are hidden after toggle')
    await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>scrollTo(0,0))
    await page.screenshot({path:'design-artifacts/bee-design-system/rekap-teacher-desktop-08.png',animations:'disabled'})
    for(const width of [1440,1024,768,390,320]){
      await page.setViewportSize({width,height:1000})
      const geo=await page.evaluate(()=>({screen:innerWidth,page:document.documentElement.scrollWidth,cards:getComputedStyle(document.querySelector('.recap-mobile')).display}))
      if(geo.page>width)throw new Error('Recap overflows '+width)
      viewports.push({kind:'recap',...geo})
    }
    await page.locator('.recap-mobile li').first().scrollIntoViewIfNeeded()
    await page.screenshot({path:'design-artifacts/bee-design-system/rekap-mobile-08.png',animations:'disabled'})
    failRead=true
    await page.getByRole('button',{name:'Terapkan',exact:true}).click()
    await page.getByText('Rekap belum berhasil dimuat',{exact:true}).waitFor()
    if(!await page.getByRole('button',{name:'Unduh CSV',exact:true}).isDisabled())throw new Error('CSV enabled after read failure')
    if(await page.locator('.recap-mobile li').count())throw new Error('Failed recap retained old counts')
    failRead=false
    await page.getByRole('button',{name:'Muat ulang rekap',exact:true}).last().click()
    await page.locator('.recap-count').getByText(/dari/).waitFor()
    if(errors.length)throw new Error(errors.join('\n'))
    return {ok:true,viewports,writes: writes.map(w=>({method:w.method,siswa:w.body?.siswa,path:w.path})),csv:download.suggestedFilename(),csvRows:csv.split('\n').length-1,checks:['all-page roster/records/master options','partial save waits all outcomes','applied date preserved','unknown POST response recovered without duplicate','non-attending services disabled/cleared','delete keeps other drafts','cancelled apply keeps draft','manual invalid date rejected','teacher read-only recap','CSV includes all filtered pages','search resets page','no-data toggle','failure clears counts and disables CSV','responsive 320–1440','focusable status choices','open calendar at 320px'],errors}
  }catch(e){return {ok:false,error:String(e),text:(await page.locator('body').innerText()).slice(-2500),writes}}finally{
    if(releasePending)releasePending()
    await page.unroute('**/api/**');page.off('pageerror',onError)
    await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh')})
    await page.setViewportSize({width:1440,height:1000})
    await page.evaluate(()=>document.querySelector('#app').__vue_app__.unmount())
    await page.goto('http://127.0.0.1:4173/login')
  }
}
