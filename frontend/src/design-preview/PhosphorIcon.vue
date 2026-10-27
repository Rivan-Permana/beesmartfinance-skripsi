<script setup lang="ts">
import Icon from "@/shared/components/PhosphorIcon.vue"
defineProps<{ name: string }>()
</script>
<template><Icon :name="name" /></template>
