async(page)=>{
  await page.goto('http://127.0.0.1:4173/login')
  const base={jenjang:1,tanggal_daftar:'2026-10-16',status:'TRIAL',biaya_sitin:'750000.25',biaya_formulir:'100000.10',biaya_pendaftaran:'0.00',total_biaya:'850000.35',total_terbayar:'0.00',sisa_biaya:'850000.35',perlu_rekonsiliasi:false,sitin_terbayar:false,formulir_terbayar:false,jurnal_sitin:null,jurnal_pendaftaran:null,pembayaran:[],siswa:null}
  const rows=Array.from({length:28},(_,i)=>({id:i+1,nama_calon:['Alya Putri','Bima Pratama','Citra Maharani','Daffa Ramadhan'][i]??`Calon contoh ${String(i+1).padStart(2,'0')}`,...structuredClone(base)}))
  Object.assign(rows[0],{sitin_terbayar:true,jurnal_sitin:'sitin-1',total_terbayar:'750000.25',sisa_biaya:'100000.10',pembayaran:[{jurnal_id:'sitin-1',tanggal:'2026-10-16',no_bukti:'SITIN-001',nominal:'750000.25',status:'DRAFT',dibatalkan:false,komponen:['SITIN']}]})
  Object.assign(rows[1],{perlu_rekonsiliasi:true,biaya_formulir:null,biaya_pendaftaran:'850000',total_biaya:null,total_terbayar:null,sisa_biaya:null,formulir_terbayar:null,sitin_terbayar:null,jurnal_sitin:'lama-1'})
  Object.assign(rows[2],{biaya_sitin:'0.00',biaya_formulir:'0.00',total_biaya:'0.00',sisa_biaya:'0.00'})
  Object.assign(rows[3],{status:'REGISTERED',siswa:44})
  let failCreate=true,holdCreate=false,releaseCreate,failPayment=true,holdPayment=true,releasePayment,failFinal=true,failList=false,failAccounts=true,failDetail=false
  let lastPayment=null,lastFinal=null
  const writes=[],calls=[],errors=[],geometry=[]
  const onError=e=>errors.push(e.message);page.on('pageerror',onError)
  const paged=(route,data,pageNum)=>route.fulfill({status:200,json:{count:data.length,next:pageNum*25<data.length?'?page='+String(pageNum+1):null,previous:null,results:data.slice((pageNum-1)*25,pageNum*25)}})
  await page.unroute('**/api/**')
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,''),method=request.method(),params=Object.fromEntries(url.searchParams)
    calls.push({method,path,params})
    if(path==='/auth/me/')return route.fulfill({status:200,json:{id:1,username:'contoh',nama:'Pengguna contoh',is_superuser:false,groups:['Administration']}})
    if(method==='GET'){
      if(path==='/jenjang/')return paged(route,[{id:1,kode:'TK A',nama:'TK A'},{id:2,kode:'TK B',nama:'TK B'}],Number(params.page||1))
      if(path==='/coa/')return route.fulfill(failAccounts?{status:503,json:{detail:'Kas tidak tersedia (fixture)'}}:{status:200,json:{count:2,next:null,previous:null,results:[{kode_akun:'111',nama_akun:'Kas sekolah',is_active:true,posisi_normal:'D',sub_golongan:null,saldo_awal:'0',tanggal_saldo_awal:null},{kode_akun:'411',nama_akun:'Pendapatan',is_active:true,posisi_normal:'K'}]}})
      if(path==='/pendaftaran-siswa/')return failList?route.fulfill({status:503,json:{detail:'Daftar tidak tersedia (fixture)'}}):paged(route,rows,Number(params.page||1))
      if(/^\/pendaftaran-siswa\/\d+\/$/.test(path)){const row=rows.find(r=>r.id===Number(path.split('/')[2]));return failDetail?route.fulfill({status:503,json:{detail:'Rincian tidak tersedia (fixture)'}}):route.fulfill({status:row?200:404,json:row??{detail:'Tidak ada'}})}
      return paged(route,[],1)
    }
    const body=method==='DELETE'?null:request.postDataJSON();writes.push({path,method,body})
    if(path==='/pendaftaran-siswa/'&&method==='POST'){
      if(failCreate){failCreate=false;return route.fulfill({status:400,json:{detail:'Data ditolak (fixture)'}})}
      if(holdCreate)await new Promise(resolve=>releaseCreate=resolve)
      const total=((Math.round(Number(body.biaya_sitin)*100)+Math.round(Number(body.biaya_formulir)*100))/100).toFixed(2)
      const row={...structuredClone(base),id:100,...body,total_biaya:total,sisa_biaya:total};rows.unshift(row);return route.fulfill({status:201,json:row})
    }
    const id=Number(path.split('/')[2]),index=rows.findIndex(r=>r.id===id),row=rows[index]
    if(method==='PATCH'){Object.assign(row,body);return route.fulfill({status:200,json:row})}
    if(method==='DELETE'){rows.splice(index,1);return route.fulfill({status:204,body:''})}
    if(path.endsWith('/bayar/')){
      if(holdPayment){await new Promise(resolve=>releasePayment=resolve);holdPayment=false}
      if(lastPayment){if(JSON.stringify(body)!==JSON.stringify(lastPayment))return route.fulfill({status:400,json:{detail:'Rincian pengulangan berubah (fixture)'}});return route.fulfill({status:200,json:{detail:'Idempotent',jurnal_id:'payment-2',pendaftaran:row}})}
      lastPayment=body
      Object.assign(row,{formulir_terbayar:true,jurnal_pendaftaran:'payment-2',total_terbayar:row.total_biaya,sisa_biaya:'0.00'})
      row.pembayaran.push({jurnal_id:'payment-2',tanggal:body.tanggal,no_bukti:body.no_bukti,nominal:body.nominal,status:'DRAFT',dibatalkan:false,komponen:body.komponen})
      if(failPayment){failPayment=false;return route.fulfill({status:503,json:{detail:'Respons terputus setelah penerimaan tersimpan (fixture)'}})}
      return route.fulfill({status:200,json:{detail:'ok',jurnal_id:'payment-2',pendaftaran:row}})
    }
    if(path.endsWith('/finalisasi/')){
      if(lastFinal&&JSON.stringify(body)!==JSON.stringify(lastFinal))return route.fulfill({status:400,json:{detail:'SPP pengulangan berubah (fixture)'}})
      lastFinal=body;Object.assign(row,{status:'REGISTERED',siswa:1000})
      if(failFinal){failFinal=false;return route.fulfill({status:503,json:{detail:'Respons terputus setelah finalisasi (fixture)'}})}
      return route.fulfill({status:200,json:row})
    }
    return route.fulfill({status:405,json:{detail:'Fixture only'}})
  })
  const button=name=>page.getByRole('button',{name,exact:true}).filter({visible:true}).first()
  async function shot(name){await page.locator('.p-toast-close-button').evaluateAll(buttons=>buttons.forEach(b=>b.click()));await page.locator('.p-toast-message').first().waitFor({state:'hidden'});await page.screenshot({path:'design-artifacts/bee-design-system/'+name,animations:'disabled'})}
  async function detail(name){await page.locator('#admission-search').fill(name);await button('Rincian '+name).click();await page.getByRole('button',{name:'Tutup rincian',exact:true}).waitFor();await page.getByText('Memeriksa rincian terbaru…',{exact:true}).waitFor({state:'hidden'})}
  async function widths(kind){for(const width of [1440,1024,768,390,320]){await page.setViewportSize({width,height:1000});const size=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));if(size.scroll>width)throw new Error(kind+' overflow '+JSON.stringify(size));geometry.push({kind,...size})}}
  try{
    await page.evaluate(()=>{localStorage.setItem('bee_access','synthetic-local-review');localStorage.removeItem('bee_refresh')})
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/pendaftaran')
    await page.getByText('1–15 dari 28 pendaftaran',{exact:true}).waitFor();await page.evaluate(()=>document.fonts.ready)
    await shot('pendaftaran-desktop-010.png')
    await page.getByRole('button',{name:'Halaman berikutnya',exact:true}).click();await page.getByText('16–28 dari 28 pendaftaran',{exact:true}).waitFor();await page.locator('#admission-search').fill('Calon contoh 28');await page.getByText('1–1 dari 1 pendaftaran',{exact:true}).waitFor();await page.locator('#admission-search').fill('')
    await button('Daftar calon baru').click();if(await page.locator('#formulir').inputValue()!==''||await page.locator('#sitin').inputValue()!=='')throw new Error('Fees have assumed defaults')
    await button('Simpan calon').click();if(writes.length)throw new Error('Blank form submitted')
    await page.locator('#nama-calon').fill('Nadia Safira');await page.locator('#formulir').fill('100000,10');await page.locator('#sitin').fill('750000,25');await page.locator('#tanggal').fill('99/10/2026');await page.locator('#tanggal').press('Tab');await button('Simpan calon').click();await page.getByText('Periksa atau pilih ulang tanggal daftar.',{exact:true}).waitFor();if(writes.length)throw new Error('Invalid manual date submitted')
    await page.locator('#tanggal').fill('18/10/2026');await page.locator('#tanggal').press('Tab');await page.locator('#tanggal').press('Escape');await button('Simpan calon').click();await page.getByText(/Data ditolak.*Input tetap ada/).waitFor()
    if(await page.locator('#nama-calon').inputValue()!=='Nadia Safira')throw new Error('Failed create lost name')
    await widths('create-form');await shot('pendaftaran-form-mobile-010.png')
    holdCreate=true;await button('Simpan calon').click();while(!releaseCreate)await page.waitForTimeout(10);await page.keyboard.press('Escape');if(!await page.getByRole('dialog').isVisible()||!await button('Kembali').isDisabled())throw new Error('Pending create closes');releaseCreate();await page.getByRole('dialog').waitFor({state:'hidden'})
    if(writes[0].body.tanggal_daftar!=='2026-10-18'||writes[0].body.biaya_formulir!=='100000.10'||writes[0].body.biaya_sitin!=='750000.25')throw new Error('Date/cents payload shifted')
    await page.setViewportSize({width:1440,height:1000});await detail('Nadia Safira');await button('Ubah calon').click();await page.locator('#nama-calon').fill('Nadia Safira Putri');await button('Simpan calon').click();await page.getByRole('dialog').waitFor({state:'hidden'});await detail('Nadia Safira Putri');await button('Hapus calon').click();await button('Hapus calon').click();await page.getByRole('dialog').waitFor({state:'hidden'});await page.locator('#admission-search').fill('')
    await detail('Bima Pratama');if(await button('Catat penerimaan').count()||await button('Ubah calon').count())throw new Error('Legacy row can be received/edited with history');await shot('pendaftaran-legacy-010.png');await button('Tutup rincian').click()
    await detail('Alya Putri');await shot('pendaftaran-rincian-desktop-010.png');await widths('detail');await page.setViewportSize({width:1440,height:1000});await button('Catat penerimaan').click();await page.getByRole('button',{name:'Muat ulang Kas/Bank',exact:true}).waitFor();if(!await button('Simpan penerimaan').isDisabled())throw new Error('Payment enabled after COA failure')
    failAccounts=false;await button('Muat ulang Kas/Bank').click();await page.getByRole('button',{name:'Muat ulang Kas/Bank',exact:true}).waitFor({state:'hidden'})
    if(!await page.locator('#bayar-SITIN').isDisabled()||!await page.locator('#bayar-FORMULIR').isChecked())throw new Error('Unpaid component selection incorrect')
    await page.locator('#bayar-bukti').fill('FORM-001');await page.locator('#bayar-kas').click();await page.getByRole('option',{name:'111 · Kas sekolah',exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'});await page.locator('#bayar-tanggal').fill('18/10/2026');await page.locator('#bayar-tanggal').press('Tab')
    await button('Simpan penerimaan').click();while(!releasePayment)await page.waitForTimeout(10);await page.keyboard.press('Escape');if(!await button('Kembali').isDisabled())throw new Error('Pending payment can close');releasePayment();await button('Coba ulang penerimaan').waitFor()
    if(!await page.locator('#bayar-bukti').isDisabled())throw new Error('Ambiguous receipt input can change')
    await widths('payment-form');await shot('pendaftaran-penerimaan-mobile-010.png');await button('Coba ulang penerimaan').click();await page.getByRole('dialog').waitFor({state:'hidden'})
    const paymentWrites=writes.filter(w=>w.path.endsWith('/bayar/'));if(paymentWrites.length!==2||JSON.stringify(paymentWrites[0].body)!==JSON.stringify(paymentWrites[1].body)||paymentWrites[0].body.nominal!=='100000.10')throw new Error('Retry changed receipt payload')
    await detail('Alya Putri');await page.getByText('FORM-001',{exact:true}).waitFor();if(await button('Catat penerimaan').count())throw new Error('Paid component offered again');await button('Tutup rincian').click()
    await detail('Citra Maharani');await button('Finalisasi').click();if(await page.locator('#spp').inputValue()!=='')throw new Error('SPP has assumed default');await button('Finalisasi siswa').click();if(writes.some(w=>w.path.endsWith('/finalisasi/')))throw new Error('Blank SPP submitted');await widths('final-form');await page.locator('#spp').fill('0');await page.locator('#spp').press('Tab');await button('Finalisasi siswa').click();await button('Coba ulang finalisasi').waitFor();if(!await page.locator('#spp').isDisabled())throw new Error('Ambiguous finalization SPP can change');await button('Coba ulang finalisasi').click();await page.getByText('Terdaftar',{exact:true}).filter({visible:true}).first().waitFor();await page.getByRole('link',{name:'Buka data siswa',exact:false}).waitFor()
    const finals=writes.filter(w=>w.path.endsWith('/finalisasi/'));if(finals.length!==2||finals.some(w=>w.body.spp_nominal!=='0.00'))throw new Error('Finalization did not preserve zero SPP');if(paymentWrites.length!==writes.filter(w=>w.path.endsWith('/bayar/')).length)throw new Error('Finalization created a receipt')
    await shot('pendaftaran-finalisasi-010.png');await button('Tutup rincian').click();await page.locator('#admission-search').fill('');await page.locator('#admission-status').click();await page.getByRole('option',{name:'Terdaftar',exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'});await page.getByText('1–2 dari 2 pendaftaran',{exact:true}).waitFor();await page.locator('#admission-status').click();await page.getByRole('option',{name:'Semua status',exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'});await widths('directory');await shot('pendaftaran-mobile-010.png')
    failDetail=true;await detail('Alya Putri');await button('Muat ulang rincian').waitFor();if(await button('Finalisasi').count())throw new Error('Actions shown before fresh detail');failDetail=false;await button('Muat ulang rincian').click();await page.getByText('Memeriksa rincian terbaru…',{exact:true}).waitFor({state:'hidden'});await button('Tutup rincian').click()
    await page.locator('#admission-search').fill('');failList=true;await button('Muat ulang daftar').click();await page.getByText('Pendaftaran belum dapat ditampilkan',{exact:true}).waitFor();if(await page.locator('.admission-cards li').count())throw new Error('List failure retained stale records');failList=false;await button('Muat ulang pendaftaran').click();await page.getByText('1–15 dari 28 pendaftaran',{exact:true}).waitFor()
    if(errors.length)throw new Error(errors.join('\n'))
    return {ok:true,geometry,writes:writes.map(w=>({method:w.method,path:w.path})),checks:['all-page list and search pagination','explicit blank fees/SPP','local date and cents','manual invalid date blocked','create error/pending preserves form','edit/delete eligible trial','legacy unknown and history locks','fresh detail gate','COA failure recovery','only unpaid full component','ambiguous receipt replay identical','finalization zero SPP/idempotent replay/no receipt','responsive 320–1440','list failure removes stale data'],errors}
  }catch(error){return {ok:false,error:String(error),text:(await page.locator('body').innerText()).slice(-2000)}}finally{
    if(releaseCreate)releaseCreate();if(releasePayment)releasePayment()
    await page.unroute('**/api/**');page.off('pageerror',onError);await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh');document.querySelector('#app')?.__vue_app__?.unmount()});await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/login')
  }
}
