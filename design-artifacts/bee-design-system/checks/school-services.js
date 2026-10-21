async(page)=>{
  await page.goto('http://127.0.0.1:4173/login')
  const now=new Date(),year=now.getFullYear(),month=now.getMonth()+1
  const students=Array.from({length:28},(_,i)=>({id:i+1,nama:i===0?'Alya Putri':i===1?'Bima Pratama':`Siswa contoh ${String(i+1).padStart(2,'0')}`,nis:`LM-${String(i+1).padStart(3,'0')}`,status:'aktif',kelompok:1,alamat:'Jalan Melati '+(i+1),spp_nominal:'0',nama_ayah:'',kontak_ayah:'',nama_ibu:'',kontak_ibu:'',tanggal_lahir:null,periode:1}))
  const fleets=Array.from({length:28},(_,i)=>({id:i+1,nama_supir:i===0?'Pak Budi':`Pengemudi ${String(i+1).padStart(2,'0')}`,jenis_mobil:'Avanza',kapasitas:7,keterangan:'Rute Melati'}))
  const registrations=students.map((s,i)=>({id:100+i,siswa:s.id,armada:i+1,harga:i===0?'0.00':'20000.25'}))
  registrations.push({id:1,siswa:1,armada:2,harga:'90000.00'})
  const photo='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120"><rect width="200" height="120" fill="#f4f6fa"/><ellipse cx="100" cy="60" rx="65" ry="45" fill="white" stroke="#c4ccd8"/><circle cx="95" cy="58" r="24" fill="#ffc342"/><rect x="117" y="45" width="25" height="35" rx="5" fill="#3d9967"/></svg>')
  let tariff={tarif_harian:'20000.25',tarif_jumat:'10000.00',is_default:false},failTariff=false,failRate=true,failFleet=true,holdFleet,releaseFleet,failMenu=true,failRecap=false
  let menuDate,menuRows=[]
  const calls=[],writes=[],errors=[],geometry=[]
  const onError=e=>errors.push(e.message);page.on('pageerror',onError)
  const paged=(route,rows,pageNum)=>route.fulfill({status:200,json:{count:rows.length,next:pageNum*25<rows.length?'?page='+String(pageNum+1):null,previous:null,results:rows.slice((pageNum-1)*25,pageNum*25)}})
  await page.unroute('**/api/**')
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,''),params=Object.fromEntries(url.searchParams),method=request.method(),pageNum=Number(params.page||1)
    calls.push({path,params,method})
    if(path==='/auth/me/')return route.fulfill({status:200,json:{id:1,username:'contoh',nama:'Pengguna contoh',is_superuser:false,groups:['Administration']}})
    if(method==='GET'){
      if(path==='/tarif-katering/')return route.fulfill(failTariff?{status:503,json:{detail:'Kegagalan tarif fixture'}}:{status:200,json:{periode_bulan:Number(params.bulan),periode_tahun:Number(params.tahun),...tariff}})
      if(path==='/jenjang/')return paged(route,[{id:1,kode:'TK',nama:'Taman kanak-kanak'}],pageNum)
      if(path==='/kelompok/')return paged(route,[{id:1,nama:'Melati',jenjang:1}],pageNum)
      if(path==='/siswa/')return paged(route,students,pageNum)
      if(path==='/armada-jemputan/')return paged(route,fleets,pageNum)
      if(path==='/pendaftaran-jemputan/')return paged(route,registrations,pageNum)
      if(path==='/kehadiran-siswa/'){
        if(failRecap)return route.fulfill({status:503,json:{detail:'Kegagalan rekap fixture'}})
        return paged(route,students.flatMap(s=>[{id:s.id*2,siswa:s.id,tanggal:`${year}-10-15`,status:'hadir',ikut_katering:true,jemput_datang:true,jemput_pulang:false},{id:s.id*2+1,siswa:s.id,tanggal:`${year}-10-16`,status:'hadir',ikut_katering:true,jemput_datang:false,jemput_pulang:true}]),pageNum)
      }
      if(path==='/menu-katering/'){
        if(!menuDate){menuDate=params.tanggal__gte;menuRows=[{id:1,tanggal:menuDate,keterangan:'Nasi, ayam, sayur bayam dan buah pepaya',gambar_url:photo}]}
        return paged(route,params.tanggal?menuRows.filter(r=>r.tanggal===params.tanggal):menuRows.filter(r=>r.tanggal>=params.tanggal__gte&&r.tanggal<=params.tanggal__lte),pageNum)
      }
      if(path.startsWith('/export/legacy/'))return route.fulfill({status:200,body:'Nama,Total\nContoh,100',contentType:'text/csv'})
      return paged(route,[],pageNum)
    }
    const body=request.headers()['content-type']?.includes('application/json')?request.postDataJSON():request.postData()
    writes.push({path,method,body})
    if(path==='/tarif-katering/'&&method==='PUT'){
      if(failRate){failRate=false;return route.fulfill({status:503,json:{detail:'Tarif belum tersimpan (fixture)'}})}
      tariff={tarif_harian:String(body.tarif_harian),tarif_jumat:String(body.tarif_jumat),is_default:false};return route.fulfill({status:200,json:tariff})
    }
    if(path.startsWith('/menu-katering/')){
      if(method==='POST'){
        if(failMenu){failMenu=false;return route.fulfill({status:400,json:{detail:'Foto belum dapat disimpan (fixture)'}})}
        const date=/name="tanggal"\r\n\r\n([^\r]+)/.exec(body)?.[1];const row={id:2,tanggal:date,keterangan:'',gambar_url:photo};menuRows.push(row);return route.fulfill({status:201,json:row})
      }
      const id=Number(path.split('/').filter(Boolean).at(-1)),index=menuRows.findIndex(r=>r.id===id)
      if(method==='PATCH'){menuRows[index].keterangan=body.keterangan;return route.fulfill({status:200,json:menuRows[index]})}
      if(method==='DELETE'){menuRows.splice(index,1);return route.fulfill({status:204,body:''})}
    }
    if(path.startsWith('/armada-jemputan/')){
      if(method==='POST'){
        if(failFleet){failFleet=false;return route.fulfill({status:400,json:{detail:'Nama ditolak (fixture)'}})}
        if(holdFleet)await new Promise(resolve=>releaseFleet=resolve)
        const row={id:300,...body};fleets.push(row);return route.fulfill({status:201,json:row})
      }
      const id=Number(path.split('/').filter(Boolean).at(-1)),index=fleets.findIndex(r=>r.id===id)
      if(method==='PATCH'){Object.assign(fleets[index],body);return route.fulfill({status:200,json:fleets[index]})}
      if(method==='DELETE'){fleets.splice(index,1);return route.fulfill({status:204,body:''})}
    }
    if(path.startsWith('/pendaftaran-jemputan/')){
      if(method==='POST'){const row={id:300,...body};registrations.push(row);return route.fulfill({status:201,json:row})}
      const id=Number(path.split('/').filter(Boolean).at(-1)),index=registrations.findIndex(r=>r.id===id)
      if(method==='PATCH'){Object.assign(registrations[index],body);return route.fulfill({status:200,json:registrations[index]})}
      if(method==='DELETE'){registrations.splice(index,1);return route.fulfill({status:204,body:''})}
    }
    return route.fulfill({status:405,json:{detail:'Fixture only'}})
  })
  async function download(label){await page.evaluate(()=>{const original=URL.createObjectURL;URL.createObjectURL=blob=>{window.__serviceCsv=blob.text();return original(blob)}});const [file]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:label,exact:true}).click()]);return {name:file.suggestedFilename(),content:await page.evaluate(()=>window.__serviceCsv)}}
  async function widths(kind){for(const width of [1440,1024,768,390,320]){await page.setViewportSize({width,height:1000});await page.evaluate(()=>scrollTo(0,0));const geo=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));if(geo.scroll>width)throw new Error(kind+' overflows: '+JSON.stringify(geo));geometry.push({kind,...geo})}}
  async function shot(path){await page.locator('.p-toast-close-button').evaluateAll(buttons=>buttons.forEach(button=>button.click()));await page.locator('.p-toast-message').first().waitFor({state:'hidden'});await page.screenshot({path:'design-artifacts/bee-design-system/'+path,animations:'disabled'})}
  const visibleButton=name=>page.getByRole('button',{name,exact:true}).filter({visible:true}).first()
  try{
    await page.evaluate(()=>{localStorage.setItem('bee_access','synthetic-local-review');localStorage.removeItem('bee_refresh')})
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/katering')
    await page.locator('.service-recap-table').getByText('Alya Putri',{exact:true}).waitFor()
    await page.evaluate(()=>document.fonts.ready)
    await shot('katering-desktop-09.png')
    await page.locator('.catering-tariff summary').click()
    await page.locator('#catering-rate').fill('30000,50');await page.locator('#catering-rate').press('Tab')
    const csvBefore=await download('Unduh CSV')
    if(csvBefore.content.split('\n').length!==29||!csvBefore.content.includes('20000.25'))throw new Error('CSV clipped or draft rate applied')
    await page.getByRole('combobox',{name:'Bulan',exact:true}).click();await page.getByRole('option',{name:'Maret',exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'})
    if((await download('Unduh CSV')).name!==`rekap-katering-${year}-${String(month).padStart(2,'0')}.csv`)throw new Error('CSV switched to unapplied month')
    await page.getByRole('button',{name:'Simpan tarif',exact:true}).click();await page.getByText(/Input tetap ada. Rekap masih memakai/).waitFor()
    if(!await page.locator('#catering-rate').inputValue().then(value=>value.includes('30.000,5')))throw new Error('Failed rate draft lost')
    await page.getByRole('button',{name:'Simpan tarif',exact:true}).click();await page.locator('.catering-tariff summary').waitFor()
    await page.waitForFunction(()=>document.querySelector('#catering-rate')?.value.includes('30.000,5')&&!document.querySelector('.service-recap')?.getAttribute('aria-busy')?.includes('true'))
    await page.locator('#catering-search').fill('Alya');const csvFiltered=await download('Unduh CSV');if(csvFiltered.content.split('\n').length!==2)throw new Error('CSV ignored search')
    await page.locator('#catering-search').fill('')
    await download('CSV format lama')
    const legacy=calls.filter(c=>c.path==='/export/legacy/katering/').at(-1);if(legacy.params.bulan!==String(month))throw new Error('Legacy used pending month')
    failTariff=true;await page.getByRole('button',{name:'Muat ulang rekap',exact:true}).first().click();await page.getByText('Rekap belum dapat ditampilkan',{exact:true}).waitFor()
    if(await page.locator('.service-recap-table').count()||!await page.getByRole('button',{name:'Unduh CSV',exact:true}).isDisabled())throw new Error('Tariff failure leaves fabricated totals')
    failTariff=false;await page.getByRole('button',{name:'Muat ulang rekap',exact:true}).first().click();await page.locator('.service-recap-table').waitFor()
    await widths('catering');await page.locator('.service-recap-cards li').first().scrollIntoViewIfNeeded();await shot('katering-mobile-09.png')
    await page.getByRole('button',{name:'Menu mingguan',exact:true}).click();await page.locator('.menu-days li').first().waitFor()
    await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>scrollTo(0,0));await shot('katering-menu-desktop-09.png')
    await page.getByRole('button',{name:/^Isi menu /}).first().click();await page.getByRole('button',{name:'Simpan menu',exact:true}).click();await page.getByText('Isi keterangan atau pilih foto menu terlebih dahulu.',{exact:true}).waitFor()
    await page.locator('#menu-foto').setInputFiles({name:'menu.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScLbtAAAAABJRU5ErkJggg==','base64')})
    await page.getByRole('button',{name:'Simpan menu',exact:true}).click();await page.getByText(/Input tetap ada. Hasil pengiriman/).waitFor()
    if(!(await page.locator('.service-preview').getAttribute('src')).startsWith('blob:'))throw new Error('Photo draft lost on error')
    await page.setViewportSize({width:320,height:1000});if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Menu dialog overflows');await shot('katering-menu-form-mobile-09.png')
    await page.getByRole('button',{name:'Simpan menu',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'})
    await page.getByRole('button',{name:/^Hapus menu /}).last().click();await page.getByRole('button',{name:'Hapus menu',exact:true}).click();await page.getByText('Menu dihapus',{exact:true}).waitFor()
    await page.getByRole('button',{name:/^Ubah menu /}).first().click();await page.locator('#menu-keterangan').fill('Nasi, sayur dan buah');await page.getByRole('button',{name:'Simpan menu',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});await page.getByText('Nasi, sayur dan buah',{exact:true}).waitFor()
    await widths('menu')
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/jemputan')
    await page.locator('.service-result-count').getByText('1–10 dari 28 armada',{exact:true}).waitFor()
    await page.locator('#fleet-search').fill('28');await page.locator('.service-result-count').getByText('1–1 dari 1 armada',{exact:true}).waitFor();await page.locator('#fleet-search').fill('')
    await page.getByRole('button',{name:'Tambah armada',exact:true}).click();await page.getByRole('button',{name:'Simpan',exact:true}).click();await page.getByText(/Periksa isian wajib/).waitFor()
    await page.locator('#fleet-driver').fill('Pak Danu');await page.locator('#fleet-capacity').fill('0');await page.locator('#fleet-capacity').press('Tab')
    await page.getByRole('button',{name:'Simpan',exact:true}).click();await page.getByText(/Input tetap ada./).waitFor()
    holdFleet=true;await page.getByRole('button',{name:'Simpan',exact:true}).click();while(!releaseFleet)await page.waitForTimeout(10)
    await page.keyboard.press('Escape');if(!await page.getByRole('dialog').isVisible()||!await page.getByRole('button',{name:'Kembali',exact:true}).isDisabled())throw new Error('Pending dialog can close')
    releaseFleet();await page.getByRole('dialog').waitFor({state:'hidden'})
    await shot('jemputan-armada-desktop-09.png')
    await page.locator('#fleet-search').fill('Pak Danu');await page.getByRole('button',{name:'Ubah armada Pak Danu',exact:true}).filter({visible:true}).click();await page.locator('#fleet-car').fill('Innova');await page.getByRole('button',{name:'Simpan',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});await page.getByRole('button',{name:'Hapus armada Pak Danu',exact:true}).filter({visible:true}).click();await page.getByRole('button',{name:'Hapus',exact:true}).click();await page.getByText('Tidak ada hasil yang cocok',{exact:true}).waitFor();await page.locator('#fleet-search').fill('')
    await widths('fleet')
    await page.getByRole('button',{name:'Pendaftaran siswa',exact:true}).click();await page.locator('.service-result-count').getByText('1–10 dari 29 pendaftaran',{exact:true}).waitFor()
    await page.locator('#registration-search').fill('Alya')
    await visibleButton('Ubah pendaftaran').click();await page.getByRole('dialog').waitFor()
    if(await page.locator('#transport-price').inputValue()!=='0')throw new Error('Zero price replaced with default')
    await page.getByRole('button',{name:'Simpan',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'})
    await page.setViewportSize({width:1440,height:1000});await page.locator('#registration-search').fill('');await shot('jemputan-peserta-desktop-09.png')
    await page.getByRole('button',{name:'Daftarkan siswa',exact:true}).click();await page.locator('#transport-student').click();await page.getByRole('option',{name:'Siswa contoh 28 · LM-028',exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'});await page.locator('#transport-fleet').click();await page.getByRole('option',{name:'Pak Budi (Avanza)',exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'});await page.locator('#transport-price').fill('12500,25');await page.locator('#transport-price').press('Tab');await page.getByRole('button',{name:'Simpan',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});await page.locator('#registration-search').fill('Siswa contoh 28');await page.getByText('1–2 dari 2 pendaftaran',{exact:true}).waitFor();await page.getByRole('button',{name:'Hapus pendaftaran Siswa contoh 28',exact:true}).filter({visible:true}).last().click();await page.getByRole('button',{name:'Hapus',exact:true}).click();await page.getByText('1–1 dari 1 pendaftaran',{exact:true}).waitFor();await page.locator('#registration-search').fill('')
    await widths('registration');await shot('jemputan-peserta-mobile-09.png')
    await page.getByRole('button',{name:'Rekap jemputan',exact:true}).click();await page.locator('.service-recap-cards li').first().waitFor()
    const transportCsv=await download('Unduh CSV')
    if(transportCsv.content.split('\n').length!==29||!transportCsv.content.split('\n')[1].endsWith(',0,1,1,0'))throw new Error('Newest zero tariff or CSV pages incorrect')
    await page.setViewportSize({width:1440,height:1000});await shot('jemputan-rekap-desktop-09.png')
    await widths('transport-recap');await page.locator('.service-recap-cards li').first().scrollIntoViewIfNeeded();await shot('jemputan-rekap-mobile-09.png')
    failRecap=true;await page.getByRole('button',{name:'Muat ulang rekap',exact:true}).first().click();await page.getByText('Rekap belum dapat ditampilkan',{exact:true}).waitFor();if(!await page.getByRole('button',{name:'Unduh CSV',exact:true}).isDisabled())throw new Error('Transport failure keeps CSV enabled')
    failRecap=false;await page.getByRole('button',{name:'Muat ulang rekap',exact:true}).last().click();await page.locator('.service-recap-cards li').first().waitFor()
    if(errors.length)throw new Error(errors.join('\n'))
    return {ok:true,geometry,mutations:writes.map(w=>({path:w.path,method:w.method})),csvRows:{katering:csvBefore.content.split('\n').length-1,jemputan:transportCsv.content.split('\n').length-1},checks:['all-page lists','unsaved tariff excluded from CSV','applied period exports','filtered CSV','tariff error removes stale numbers','photo-only menu/error preserves file','menu create/edit/delete','fleet create/edit/delete, validation and zero capacity','pending locks Escape','registration create/edit/delete, zero price preserved','newest registration matches billing','no overflow 320–1440','recap failure/recovery'],errors}
  }catch(error){return {ok:false,error:String(error),text:(await page.locator('body').innerText()).slice(-1800)}}finally{
    if(releaseFleet)releaseFleet()
    await page.unroute('**/api/**');page.off('pageerror',onError)
    await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh');document.querySelector('#app')?.__vue_app__?.unmount()})
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/login')
  }
}
