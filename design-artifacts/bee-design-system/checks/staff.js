async(page)=>{
  const base='http://127.0.0.1:4173'
  const staff=Array.from({length:28},(_,i)=>({id:i+1,nama:`Pegawai Contoh ${String(i+1).padStart(2,'0')}`,nip:`CONTOH-${i+1}`,jabatan:i%2?'Guru':'Staf',nomor_hp:null,alamat:null,status_aktif:i!==2,tanggal_mulai_kerja:'2026-01-05',tanggal_selesai_kerja:null,user:i===0?4:null}))
  const today=new Date(),todayStr=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`
  let records=Array.from({length:17},(_,i)=>({id:i+1,pegawai:i+1,tanggal:todayStr,hadir:1,izin:0,sakit:0,terlambat:0}))
  records[1]={...records[1],izin:1}
  let failStaff=false,failAttendance=false,ambiguousSave=true
  const writes=[],geometry=[],errors=[]
  page.on('pageerror',e=>errors.push(String(e)))
  await page.unroute('**/api/**')
  await page.evaluate(()=>localStorage.setItem('bee_access','synthetic-local-review'))
  const paged=(rows,page)=>({count:rows.length,next:page*10<rows.length?'next':null,previous:null,results:rows.slice((page-1)*10,page*10)})
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,'')
    const id=Number(path.split('/')[2]),method=request.method()
    if(method!=='GET'){
      const body=request.postData()?request.postDataJSON():null
      writes.push({path,method,body})
      if(path==='/pegawai/'&&method==='POST'){const record={...body,id:99,user:null};staff.unshift(record);return route.fulfill({status:201,json:record})}
      if(/^\/pegawai\/\d+\/$/.test(path)&&method==='PUT'){const record={...staff.find(r=>r.id===id),...body};staff.splice(staff.findIndex(r=>r.id===id),1,record);return route.fulfill({json:record})}
      if(/^\/pegawai\/\d+\/$/.test(path)&&method==='DELETE'){staff.splice(staff.findIndex(r=>r.id===id),1);return route.fulfill({status:204,body:''})}
      if(path==='/absen-pegawai/bulk-save/'&&method==='POST'){
        for(const item of body.items){records=records.filter(r=>r.pegawai!==item.pegawai||r.tanggal!==body.tanggal);if(item.hadir+item.izin+item.sakit+item.terlambat)records.push({...item,id:records.length+100,tanggal:body.tanggal})}
        return route.fulfill({status:ambiguousSave?503:200,json:ambiguousSave?{detail:'Respons hilang setelah sebagian catatan disimpan'}:{count:body.items.length}})
      }
      return route.fulfill({status:405,json:{detail:'Fixture blocks unexpected mutation'}})
    }
    let result=paged([],1)
    if(path==='/auth/me/')result={id:1,username:'admin.contoh',groups:['Administration'],is_superuser:false}
    else if(path==='/pegawai/'){if(failStaff)return route.fulfill({status:503,json:{detail:'Daftar pegawai gagal'}});result=paged(staff,Number(url.searchParams.get('page')||1))}
    else if(/^\/pegawai\/\d+\/$/.test(path)){result=staff.find(r=>r.id===id);if(!result)return route.fulfill({status:404,json:{detail:'Tidak ada'}})}
    else if(path==='/absen-pegawai/'){if(failAttendance)return route.fulfill({status:503,json:{detail:'Absensi gagal'}});result=paged(records.filter(r=>r.tanggal===url.searchParams.get('tanggal')),Number(url.searchParams.get('page')||1))}
    else if(path==='/absen-pegawai/rekap-bulanan/')result=[{pegawai:1,nama:'Pegawai Contoh 01',hadir:20,izin:1,sakit:0,terlambat:2},{pegawai:2,nama:'Pegawai Contoh 02',hadir:19,izin:0,sakit:1,terlambat:1}]
    return route.fulfill({json:result})
  })
  const button=name=>page.getByRole('button',{name,exact:true}).filter({visible:true})
  const check=(condition,why)=>{if(!condition)throw Error(why)}
  async function widths(surface){for(const width of [1440,1024,768,390,320]){
    await page.setViewportSize({width,height:900})
    await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>a.effect?.getComputedTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{})))})
    const result=await page.evaluate(()=>{const dialogs=[...document.querySelectorAll('.p-dialog')].filter(e=>e.getBoundingClientRect().width);return {width:innerWidth,page:document.documentElement.scrollWidth,dialog:dialogs.map(e=>{const c=e.querySelector('.p-dialog-content'),f=e.querySelector('.p-dialog-footer');if(c)c.scrollTop=c.scrollHeight;const last=c?.querySelector('.staff-account');return {left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,scroll:e.scrollWidth,client:e.clientWidth,lastReachable:!last||!f||last.getBoundingClientRect().bottom<=f.getBoundingClientRect().top+2}})}})
    geometry.push({surface,...result})
    check(result.page<=width+1&&result.dialog.every(d=>d.left>=-1&&d.right<=width+1&&d.scroll<=d.client+1&&d.lastReachable),`overflow ${surface} ${width}: ${JSON.stringify(result)}`)
  }}
  await page.goto(base+'/pegawai')
  await page.getByRole('heading',{name:'Direktori pegawai'}).waitFor()
  await page.getByText('1–15 dari 28 pegawai').waitFor()
  check((await page.locator('table.employee-table tbody tr').count())===15,'directory pagination')
  await widths('directory')
  await page.setViewportSize({width:1440,height:900}); await page.screenshot({path:'design-artifacts/bee-design-system/staff-directory-desktop-012.png',fullPage:true})
  await page.setViewportSize({width:390,height:900}); await page.screenshot({path:'design-artifacts/bee-design-system/staff-directory-mobile-012.png',fullPage:true})
  await page.setViewportSize({width:1440,height:900})
  await page.getByRole('textbox',{name:'Cari pegawai'}).fill('Contoh 28')
  check((await page.locator('table.employee-table tbody tr').count())===1,'search last page')
  await page.getByRole('textbox',{name:'Cari pegawai'}).fill('')
  await button('Ubah Pegawai Contoh 01').first().click()
  await page.locator('#staff-address').fill('Alamat fiktif')
  await button('Simpan perubahan').click()
  await page.getByRole('dialog').waitFor({state:'hidden'})
  check(writes.some(w=>w.path==='/pegawai/1/'&&w.method==='PUT'&&w.body.tanggal_mulai_kerja==='2026-01-05'&&!('user' in w.body)),'edit preserves local date and account relation')
  failStaff=true;await button('Muat ulang daftar').click();await page.getByRole('heading',{name:'Daftar pegawai belum dapat ditampilkan'}).waitFor()
  failStaff=false;await button('Coba muat ulang pegawai').click();await page.getByText('1–15 dari 28 pegawai').waitFor()
  await button('Tambah pegawai').click()
  await page.getByRole('dialog').waitFor()
  await widths('profile')
  await page.setViewportSize({width:390,height:900}); await page.screenshot({path:'design-artifacts/bee-design-system/staff-profile-mobile-012.png',fullPage:false})
  await page.setViewportSize({width:1440,height:900})
  await button('Simpan pegawai').click()
  check(await page.getByText('Isi nama lengkap pegawai.').isVisible(),'required name')
  await page.locator('#staff-name').fill('Pegawai Baru')
  await page.locator('#staff-nip').fill('BARU-1')
  await button('Simpan pegawai').click()
  await page.getByRole('dialog').waitFor({state:'hidden'})
  check(writes.some(w=>w.path==='/pegawai/'&&w.body.nama==='Pegawai Baru'&&!('user' in w.body)),'profile payload')
  await page.goto(base+'/absensi-pegawai')
  await page.locator('.staff-roster h2').waitFor()
  await page.getByText('29 pegawai ·',{exact:false}).first().waitFor()
  check(await page.getByText('Catatan lama:',{exact:false}).isVisible(),'mixed record preserved')
  await widths('attendance')
  for(const width of [1440,390]){
    await page.setViewportSize({width,height:900})
    await page.evaluate(()=>window.scrollTo(0,1100))
    const midway=await page.evaluate(()=>({bar:document.querySelector('.staff-savebar').getBoundingClientRect().top,position:getComputedStyle(document.querySelector('.staff-savebar')).position,viewport:innerHeight}))
    check(midway.position==='static'&&midway.bar>midway.viewport,`save bar covers page header at ${width}: ${JSON.stringify(midway)}`)
    await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight))
    const bottom=await page.evaluate(()=>{const r=document.querySelector('.staff-savebar').getBoundingClientRect();return {top:r.top,bottom:r.bottom,viewport:innerHeight}})
    check(bottom.top>=0&&bottom.bottom<=bottom.viewport,`save action not reachable at list end ${width}: ${JSON.stringify(bottom)}`)
    await page.screenshot({path:`design-artifacts/bee-design-system/staff-save-footer-${width}-012.png`})
    geometry.push({surface:'deep-scroll',width,midway,bottom})
  }
  await page.evaluate(()=>window.scrollTo(0,0))
  await page.setViewportSize({width:1440,height:900}); await page.screenshot({path:'design-artifacts/bee-design-system/staff-attendance-desktop-012.png',fullPage:true})
  await page.setViewportSize({width:390,height:900}); await page.screenshot({path:'design-artifacts/bee-design-system/staff-attendance-mobile-012.png',fullPage:false})
  await page.setViewportSize({width:1440,height:900})
  const first=page.locator('.staff-attendance-row').first()
  await first.getByRole('button',{name:'Izin'}).click()
  check(await first.getByText('Diubah, belum disimpan').isVisible(),'dirty state')
  await page.getByRole('button',{name:'Pegawai',exact:true}).filter({visible:true}).click()
  await page.getByRole('alertdialog').waitFor()
  await button('Tetap di sini').click()
  check(page.url().endsWith('/absensi-pegawai'),'dirty navigation guard')
  await button('Simpan absensi').click()
  await button('Periksa hasil simpan').waitFor()
  check(writes.filter(w=>w.path==='/absen-pegawai/bulk-save/').length===1,'single bulk request')
  await button('Periksa hasil simpan').click()
  await button('Periksa hasil simpan').waitFor({state:'hidden'})
  await button('Simpan absensi').waitFor()
  check(writes.filter(w=>w.path==='/absen-pegawai/bulk-save/').length===1,'no duplicate after ambiguous response')
  failAttendance=true;await button('Muat ulang catatan').click();await page.getByRole('heading',{name:'Daftar absensi belum dapat ditampilkan'}).waitFor()
  failAttendance=false;await button('Muat ulang absensi').click();await page.getByText('29 pegawai ·',{exact:false}).first().waitFor()
  await page.getByRole('tab',{name:'Rekap bulanan'}).click()
  await button('Tampilkan rekap').click()
  await page.getByText('2 pegawai memiliki catatan').waitFor()
  check((await page.locator('.staff-recap-heading').textContent()).includes('2 pegawai'),'monthly recap')
  await widths('recap')
  await page.setViewportSize({width:390,height:900}); await page.screenshot({path:'design-artifacts/bee-design-system/staff-recap-mobile-012.png',fullPage:false})
  await page.setViewportSize({width:1440,height:900})
  await page.unroute('**/api/**')
  await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh');document.querySelector('#app')?.__vue_app__?.unmount()})
  await page.goto(base+'/login')
  return {ok:true,geometry,writes:writes.map(w=>({path:w.path,method:w.method,keys:Object.keys(w.body||{})})),errors}
}
