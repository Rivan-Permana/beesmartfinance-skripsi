async(page)=>{
  await page.goto('http://127.0.0.1:4173/design-system.html')
  const fixture=await page.evaluate(async()=>{const m=await import('/src/design-system/payroll-fixtures.ts');return JSON.parse(JSON.stringify({salary:m.payrollSalary,loan:m.payrollLoan,staff:m.payrollStaff[0]}))})
  const staff=Array.from({length:28},(_,i)=>({...fixture.staff,id:i+1,nama:`Pegawai Contoh ${String(i+1).padStart(2,'0')}`,status_aktif:i!==2}))
  let salaries=staff.map((p,i)=>({...fixture.salary,id:i+1,pegawai:p.id,jurnal:i===1?'GAJI-JURNAL':null}))
  let loans=staff.map((p,i)=>({...fixture.loan,id:i+1,pegawai:p.id,jurnal:i===1?'KASBON-JURNAL':null}))
  let failSalary=false,failLoans=false,failPeople=false,rejectSalary=true,rejectLoan=true,ambiguousLoan=false,failDetail=false
  let releaseSalary,releaseAction
  const writes=[],calls=[],geometry=[],errors=[]
  const onError=e=>errors.push(String(e));page.on('pageerror',onError)
  const paged=(rows,page=1)=>({count:rows.length,next:page*12<rows.length?'next':null,previous:null,results:rows.slice((page-1)*12,page*12)})
  await page.unroute('**/api/**')
  await page.evaluate(()=>localStorage.setItem('bee_access','synthetic-local-review'))
  await page.route('**/api/**',async route=>{
    const request=route.request(),url=new URL(request.url()),path=url.pathname.replace(/^.*\/api\/v1/,'')
    calls.push({path,method:request.method(),page:url.searchParams.get('page')})
    const id=Number(path.split('/')[2])
    if(request.method()!=='GET'){
      const body=request.postData()?request.postDataJSON():null
      writes.push({path,method:request.method(),body})
      if(path==='/gaji/'&&request.method()==='POST'){
        if(rejectSalary){rejectSalary=false;return route.fulfill({status:400,json:{periode_bulan:['Periksa periode contoh.']}})}
        await new Promise(resolve=>releaseSalary=resolve)
        const gross=['gaji_pokok','tunjangan_jabatan','tunjangan_pengabdian','tunjangan_asuransi','uang_makan','transport','bonus_insentif','thr'].reduce((n,k)=>n+Math.round(Number(body[k])*100),0)
        const result={...fixture.salary,...body,id:99,potongan_pinjaman:'100000.00',total_bruto:(gross/100).toFixed(2),total_potongan:(100000+Number(body.potongan_asuransi)).toFixed(2),total_netto:((gross-10000000-Math.round(Number(body.potongan_asuransi)*100))/100).toFixed(2)}
        salaries=[result,...salaries];return route.fulfill({status:201,json:result})
      }
      if(/^\/gaji\/\d+\/$/.test(path)&&request.method()==='PUT'){const result={...salaries.find(r=>r.id===id),...body};salaries=salaries.map(r=>r.id===id?result:r);return route.fulfill({json:result})}
      if(path==='/gaji/1/posting/'){
        await new Promise(resolve=>releaseAction=resolve)
        salaries=salaries.map(r=>r.id===1?{...r,jurnal:'GAJI-COMMITTED'}:r);loans=loans.map(r=>r.pegawai===1?{...r,sisa_pinjaman:'0.00',sudah_terbayar:r.jumlah_pinjaman}:r)
        return route.fulfill({status:503,json:{detail:'Respons hilang setelah commit fixture'}})
      }
      if(/^\/gaji\/\d+\/$/.test(path)&&request.method()==='DELETE'){salaries=salaries.filter(r=>r.id!==id);return route.fulfill({status:204,body:''})}
      if(path==='/pinjaman/'&&request.method()==='POST'){
        if(rejectLoan){rejectLoan=false;return route.fulfill({status:400,json:{jumlah_pinjaman:['Data ditolak (fixture).']}})}
        const result={...body,id:loans.length+100,sudah_terbayar:'0.00',sisa_pinjaman:body.jumlah_pinjaman,jurnal:null};loans=[result,...loans]
        return route.fulfill({status:ambiguousLoan?503:201,json:ambiguousLoan?{detail:'Respons hilang setelah commit fixture'}:result})
      }
      if(/^\/pinjaman\/\d+\/$/.test(path)&&request.method()==='PUT'){const result={...loans.find(r=>r.id===id),...body};loans=loans.map(r=>r.id===id?result:r);return route.fulfill({json:result})}
      if(path==='/pinjaman/1/cairkan/'){loans=loans.map(r=>r.id===1?{...r,jurnal:'KASBON-COMMITTED'}:r);return route.fulfill({status:503,json:{detail:'Respons hilang setelah commit fixture'}})}
      if(/^\/pinjaman\/\d+\/$/.test(path)&&request.method()==='DELETE'){loans=loans.filter(r=>r.id!==id);return route.fulfill({status:204,body:''})}
      return route.fulfill({status:405,json:{detail:'Fixture review blocks unexpected mutation'}})
    }
    let data=paged([])
    if(path==='/auth/me/')data={id:1,username:'contoh',groups:['Finance'],is_superuser:false}
    else if(path==='/pegawai/'){if(failPeople)return route.fulfill({status:503,json:{detail:'Fixture failure'}});data=paged(staff,Number(url.searchParams.get('page')||1))}
    else if(path==='/gaji/'){if(failSalary)return route.fulfill({status:503,json:{detail:'Fixture failure'}});data=paged(salaries,Number(url.searchParams.get('page')||1))}
    else if(path==='/pinjaman/'){if(failLoans)return route.fulfill({status:503,json:{detail:'Fixture failure'}});data=paged(loans,Number(url.searchParams.get('page')||1))}
    else if(/^\/gaji\/\d+\/$/.test(path)){if(failDetail)return route.fulfill({status:503,json:{detail:'Fixture detail failure'}});data=salaries.find(r=>r.id===id);if(!data)return route.fulfill({status:404,json:{detail:'Removed fixture'}})}
    else if(/^\/pinjaman\/\d+\/$/.test(path)){if(failDetail)return route.fulfill({status:503,json:{detail:'Fixture detail failure'}});data=loans.find(r=>r.id===id);if(!data)return route.fulfill({status:404,json:{detail:'Removed fixture'}})}
    return route.fulfill({json:data})
  })
  const button=name=>page.getByRole('button',{name,exact:true}).filter({visible:true})
  async function choose(id,option){await page.locator('#'+id).click();await page.getByRole('option',{name:option,exact:true}).click();await page.getByRole('listbox').waitFor({state:'hidden'})}
  async function closeDetail(){await button('Tutup rincian').click();await page.getByRole('dialog').waitFor({state:'hidden'})}
  async function widths(screen){
    for(const width of [1440,1024,768,390,320]){
      await page.setViewportSize({width,height:900})
      await page.evaluate(async()=>{await Promise.all(document.getAnimations().filter(a=>a.effect?.getComputedTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{})))})
      const result=await page.evaluate(()=>{
        const dialogs=[...document.querySelectorAll('.p-dialog')].filter(e=>e.getBoundingClientRect().width)
        const problems=[]
        for(const d of dialogs){const r=d.getBoundingClientRect(),c=d.querySelector('.p-dialog-content'),f=d.querySelector('.p-dialog-footer');if(r.x<0||r.right>innerWidth+1||r.y<0||r.bottom>innerHeight+1||d.scrollWidth>d.clientWidth+1||c.scrollWidth>c.clientWidth+1)problems.push('dialog overflow');if(f){const old=c.scrollTop;c.scrollTop=c.scrollHeight;const last=[...c.querySelectorAll('input,textarea,[role="combobox"]')].filter(e=>e.getBoundingClientRect().width).at(-1);if(last&&last.getBoundingClientRect().bottom>f.getBoundingClientRect().y+1)problems.push('last field clipped');c.scrollTop=old}}
        return {width:innerWidth,pageWidth:document.documentElement.scrollWidth,problems}
      })
      geometry.push({screen,...result});if(result.pageWidth>width||result.problems.length)throw new Error(screen+JSON.stringify(result))
    }
  }
  async function shot(name){await page.locator('.p-toast-close-button').evaluateAll(bs=>bs.forEach(b=>b.click()));await page.screenshot({path:`design-artifacts/bee-design-system/payroll-${name}-011.png`,scale:'css',animations:'disabled'})}
  async function fillLoan(){await choose('loan-employee','Pegawai Contoh 28');await page.locator('#loan-date').fill('18/10/2026');await page.locator('#loan-date').press('Tab');await page.locator('#loan-amount').fill('1250000,25');await page.locator('#loan-installment').fill('0');await page.locator('#loan-installment').press('Tab')}
  try{
    await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/gaji');await page.getByText('1–15 dari 28 slip',{exact:true}).waitFor()
    await widths('salary-list');await page.setViewportSize({width:1440,height:1000});await shot('salary-desktop')
    await page.locator('#salary-search').fill('Pegawai Contoh 28');await page.getByText('1–1 dari 1 slip',{exact:true}).waitFor();await page.locator('#salary-search').fill('')
    await button('Buat slip gaji').click();await button('Simpan slip').click();if(writes.length)throw new Error('Blank salary employee submitted')
    await choose('salary-employee','Pegawai Contoh 28');await page.locator('#salary-year').fill('2027');await page.locator('#salary-gaji_pokok').fill('4000000,10');await page.locator('#salary-tunjangan_asuransi').fill('25000,25');await page.locator('#salary-uang_makan').fill('50000,50');await page.locator('#salary-attendance').fill('18');await page.locator('#salary-attendance').press('Tab')
    await button('Simpan slip').click();await page.getByText(/Input tetap ada/).waitFor();if(await page.locator('#salary-uang_makan').inputValue()!=='50.000,5')throw new Error('Salary error lost components')
    await widths('salary-form');await shot('salary-form-mobile');await page.setViewportSize({width:1440,height:1000});await shot('salary-form-desktop')
    await button('Simpan slip').click();while(!releaseSalary)await page.waitForTimeout(10);await page.keyboard.press('Escape');if(!await page.getByRole('dialog',{name:'Buat slip gaji'}).isVisible()||!await page.locator('#salary-gaji_pokok').isDisabled())throw new Error('Pending salary can change/close')
    await page.getByRole('button',{name:'Kasbon',exact:true}).filter({visible:true}).evaluate(e=>e.click());if(!page.url().endsWith('/gaji'))throw new Error('Pending save navigated away')
    releaseSalary();await page.getByRole('dialog',{name:'Rincian slip gaji',exact:true}).waitFor();const saved=writes.filter(w=>w.path==='/gaji/').at(-1).body
    if(saved.tunjangan_asuransi!=='25000.25'||saved.uang_makan!=='50000.50'||saved.hari_hadir!==18||'potongan_pinjaman' in saved)throw new Error('Salary contract/decimal changed')
    await widths('salary-slip');await shot('salary-slip-mobile');await page.setViewportSize({width:1440,height:1000});await shot('salary-slip-desktop')
    await page.evaluate(()=>{window.print=()=>window.dispatchEvent(new Event('beforeprint'))});await button('Cetak slip').click();await page.setViewportSize({width:794,height:1123});await page.emulateMedia({media:'print'});const print=await page.evaluate(()=>({appHidden:getComputedStyle(document.querySelector('#app')).display==='none',slipVisible:getComputedStyle(document.querySelector('.payroll-slip-dialog')).display!=='none',footerHidden:getComputedStyle(document.querySelector('.payroll-slip-dialog .p-dialog-footer')).display==='none',pageWidth:document.documentElement.scrollWidth}));if(!print.appHidden||!print.slipVisible||!print.footerHidden||print.pageWidth>794)throw new Error('Print scope broken '+JSON.stringify(print));await shot('salary-print');await page.emulateMedia({media:'screen'});await page.evaluate(()=>window.dispatchEvent(new Event('afterprint')));await closeDetail()
    await page.setViewportSize({width:1440,height:1000});await button('Tindakan slip Pegawai Contoh 03 Oktober 2026').click();await page.getByRole('menuitem',{name:'Ubah slip',exact:true}).click();await page.getByRole('dialog',{name:'Ubah slip gaji'}).waitFor();if(await page.locator('#salary-tunjangan_asuransi').inputValue()!=='25.000,25')throw new Error('Existing component lost');await page.locator('#salary-gaji_pokok').fill('4200000,25');await page.locator('#salary-gaji_pokok').press('Tab');await button('Simpan perubahan').click();await page.getByRole('dialog',{name:'Rincian slip gaji'}).waitFor();await closeDetail()
    await button('Tindakan slip Pegawai Contoh 01 Oktober 2026').click();await page.getByRole('menuitem',{name:'Posting ke jurnal',exact:true}).click();await button('Buat jurnal gaji').waitFor();await page.getByText('Memeriksa data terbaru…',{exact:true}).waitFor({state:'hidden'});await button('Buat jurnal gaji').click();while(!releaseAction)await page.waitForTimeout(10);await page.keyboard.press('Escape');if(!await button('Kembali').isDisabled())throw new Error('Pending action closes');releaseAction();await page.getByText(/Respons belum memastikan hasil tindakan/).waitFor();if(!await button('Buat jurnal gaji').isDisabled())throw new Error('Ambiguous posting can replay');await widths('salary-posting');await shot('salary-posting-mobile');await button('Periksa status terbaru').click();await page.getByRole('dialog').waitFor({state:'hidden'});if(writes.filter(w=>w.path==='/gaji/1/posting/').length!==1)throw new Error('Posting replayed');await button('Buat slip gaji').click();await choose('salary-employee','Pegawai Contoh 01');await page.locator('.employee-readonly').getByText('Rp 0',{exact:true}).waitFor();await button('Kembali').click()
    await page.setViewportSize({width:1440,height:1000});await button('Tindakan slip Pegawai Contoh 04 Oktober 2026').click();await page.getByRole('menuitem',{name:'Hapus slip',exact:true}).click();await page.getByText('Memeriksa data terbaru…',{exact:true}).waitFor({state:'hidden'});await button('Hapus slip').click();await page.getByRole('dialog').waitFor({state:'hidden'})
    failPeople=true;await button('Muat ulang daftar').click();await page.reload();await page.getByText('1–15 dari 28 slip',{exact:true}).waitFor();await page.getByText(/Daftar pegawai belum berhasil dimuat/).first().waitFor();await button('Buat slip gaji').click();if(!await button('Simpan slip').isDisabled())throw new Error('Unknown payroll options can save');failPeople=false;await page.getByRole('dialog').getByRole('button',{name:'Muat ulang data pendukung',exact:true}).click();await button('Simpan slip').waitFor({state:'visible'});await button('Kembali').click()
    failSalary=true;await button('Muat ulang daftar').click();await page.getByRole('heading',{name:'Daftar gaji belum dapat ditampilkan'}).waitFor();if(await page.locator('.employee-cards li').count())throw new Error('Failed salary list kept stale records');failSalary=false;await button('Coba muat ulang gaji').click();await page.getByText('1–15 dari 28 slip',{exact:true}).waitFor()
    await page.goto('http://127.0.0.1:4173/pinjaman');await page.getByText('1–15 dari 28 pengajuan',{exact:true}).waitFor();await widths('loan-list');await shot('loan-list-mobile');await page.setViewportSize({width:1440,height:1000});await shot('loan-list-desktop')
    await page.locator('#loan-search').fill('Pegawai Contoh 28');await page.getByText('1–1 dari 1 pengajuan',{exact:true}).waitFor();await page.locator('#loan-search').fill('')
    await button('Ajukan kasbon').click();await button('Simpan pengajuan').click();if(writes.some(w=>w.path==='/pinjaman/'&&w.method==='POST'))throw new Error('Blank loan submitted');await fillLoan();await page.locator('#loan-date').fill('31/02/2026');await page.locator('#loan-date').press('Tab');await button('Simpan pengajuan').click();if(writes.some(w=>w.path==='/pinjaman/'&&w.method==='POST'))throw new Error('Invalid loan date sent');await page.locator('#loan-date').fill('18/10/2026');await page.locator('#loan-date').press('Tab');await button('Simpan pengajuan').click();await page.getByText(/Input tetap ada/).waitFor();await widths('loan-form');await shot('loan-form-mobile');await page.setViewportSize({width:1440,height:1000});await shot('loan-form-desktop');await button('Simpan pengajuan').click();await page.getByRole('dialog',{name:'Rincian kasbon'}).waitFor();await widths('loan-detail');await shot('loan-detail-mobile');await closeDetail()
    const created=writes.filter(w=>w.path==='/pinjaman/'&&w.method==='POST').at(-1).body;if(created.tanggal_pinjaman!=='2026-10-18'||created.jumlah_pinjaman!=='1250000.25'||created.angsuran_per_bulan!=='0.00')throw new Error('Loan date/cents/zero changed')
    await page.setViewportSize({width:1440,height:1000});await button('Tindakan kasbon Pegawai Contoh 03 1 Okt 2026').click();await page.getByRole('menuitem',{name:'Ubah kasbon',exact:true}).click();await page.locator('#loan-installment').fill('0');await page.locator('#loan-installment').press('Tab');await button('Simpan perubahan').click();await page.getByRole('dialog',{name:'Rincian kasbon'}).waitFor();await closeDetail()
    await button('Cairkan kasbon Pegawai Contoh 01').click();await page.getByText('Memeriksa data terbaru…',{exact:true}).waitFor({state:'hidden'});await button('Buat jurnal pencairan').click();await page.getByText(/Respons belum memastikan hasil tindakan/).waitFor();if(!await button('Buat jurnal pencairan').isDisabled())throw new Error('Ambiguous disbursement can replay');await widths('loan-disbursement');await shot('loan-disbursement-mobile');await button('Periksa status terbaru').click();await page.getByRole('dialog').waitFor({state:'hidden'});if(writes.filter(w=>w.path==='/pinjaman/1/cairkan/').length!==1)throw new Error('Disbursement replayed')
    await page.setViewportSize({width:1440,height:1000});ambiguousLoan=true;await button('Ajukan kasbon').click();await fillLoan();await button('Simpan pengajuan').click();await page.getByText(/Hasil penyimpanan belum terkonfirmasi/).waitFor();if(!await page.locator('#loan-amount').isDisabled())throw new Error('Ambiguous create input can change');await button('Periksa daftar kasbon').click();await page.getByRole('dialog').waitFor({state:'hidden'});await page.getByText('1–15 dari 30 pengajuan',{exact:true}).waitFor()
    await button('Tindakan kasbon Pegawai Contoh 04 1 Okt 2026').click();await page.getByRole('menuitem',{name:'Hapus pengajuan',exact:true}).click();await page.getByText('Memeriksa data terbaru…',{exact:true}).waitFor({state:'hidden'});await button('Hapus pengajuan').click();await page.getByRole('dialog').waitFor({state:'hidden'})
    failDetail=true;await button('Cairkan kasbon Pegawai Contoh 05').click();await button('Periksa status terbaru').waitFor();if(!await button('Buat jurnal pencairan').isDisabled())throw new Error('Action allowed before fresh detail');failDetail=false;await button('Periksa status terbaru').click();await page.getByText('Memeriksa data terbaru…',{exact:true}).waitFor({state:'hidden'});await button('Kembali').click()
    failLoans=true;await button('Muat ulang daftar').click();await page.getByRole('heading',{name:'Daftar kasbon belum dapat ditampilkan'}).waitFor();if(await page.locator('.employee-cards li').count())throw new Error('Failed loan list kept stale data');failLoans=false;await button('Coba muat ulang kasbon').click();await page.getByText('1–15 dari 29 pengajuan',{exact:true}).waitFor()
    if(errors.length)throw new Error(errors.join('\n'))
    return {ok:true,geometry,print,writes:writes.map(w=>({path:w.path,method:w.method})),checks:['all-page lists/search','explicit validation and local dates','all salary components/cents retained','server deduction omitted from payload','inactive existing employee','input preserved after rejection','pending close/navigation locks','server result slip','isolated print scope','fresh detail gate','ambiguous posting/disbursement status read without replay, loan deduction refreshed','ambiguous loan create checked in list','eligible delete','independent option errors/list retry'],errors,scope:'All API requests mocked; no business database changed; printer stubbed'}
  }catch(error){await page.screenshot({path:'design-artifacts/bee-design-system/payroll-failure.png',scale:'css',animations:'disabled'});return {ok:false,error:String(error),url:page.url(),calls:calls.slice(-12),text:(await page.locator('body').innerText()).slice(-2200)}}finally{
    releaseSalary?.();releaseAction?.();page.off('pageerror',onError);await page.emulateMedia({media:'screen'});await page.unroute('**/api/**');await page.evaluate(()=>{localStorage.removeItem('bee_access');localStorage.removeItem('bee_refresh');document.querySelector('#app')?.__vue_app__?.unmount();document.body.classList.remove('bee-print-payroll')});await page.setViewportSize({width:1440,height:1000});await page.goto('http://127.0.0.1:4173/login',{waitUntil:'domcontentloaded'}).catch(()=>{})
  }
}
