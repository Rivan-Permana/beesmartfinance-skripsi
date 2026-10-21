<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Message from 'primevue/message'
import Icon from '@/shared/components/PhosphorIcon.vue'
const props=defineProps<{visible:boolean;title:string;label:string;amount:string;description:string;confirmLabel:string;danger?:boolean;pending:boolean;checking:boolean;error:string;uncertain:boolean;ready:boolean}>()
const emit=defineEmits<{close:[];confirm:[];refresh:[]}>()
const errorElement=ref<HTMLElement|null>(null)
watch(()=>props.error,async error=>{if(error){await nextTick();errorElement.value?.focus()}})
</script>
<template>
  <Dialog :visible="visible" @update:visible="value=>{if(!value&&!pending&&!checking)emit('close')}" :header="title" class="employee-action-dialog" modal :draggable="false" :closable="!pending&&!checking" :close-on-escape="!pending&&!checking" :close-button-props="{severity:'secondary',text:true,'aria-label':'Tutup konfirmasi'}"><template #closeicon><Icon name="x" /></template>
    <div class="employee-action-context"><strong>{{ label }}</strong><span>{{ amount }}</span></div>
    <p class="employee-intro">{{ description }}</p>
    <p v-if="checking" role="status" class="employee-small-note">Memeriksa data terbaru…</p>
    <div v-if="error" ref="errorElement" tabindex="-1"><Message severity="error" :closable="false">{{ error }}</Message></div>
    <Message v-if="uncertain" severity="warn" :closable="false">Respons belum memastikan hasil tindakan. Periksa status terbaru sebelum mencoba kembali.</Message>
    <template #footer><Button label="Kembali" severity="secondary" :disabled="pending||checking" @click="emit('close')" /><Button v-if="error||uncertain||!ready" label="Periksa status terbaru" severity="secondary" :disabled="pending" :loading="checking" @click="emit('refresh')" ><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button><Button :label="confirmLabel" :severity="danger?'danger':undefined" :disabled="pending||checking||uncertain||!ready" :loading="pending" @click="emit('confirm')" ><template #loadingicon><Icon name="arrows-clockwise" class="bee-spin" /></template></Button></template>
  </Dialog>
</template>
