<script setup>
defineProps({
  trek: { type: Object, required: true },
})

defineEmits(['book'])
</script>

<template>
  <div class="card trek-card h-100 shadow-sm">
    <div class="card-body">
      <h5 class="card-title">{{ trek.name }}</h5>
      <p class="mb-1"><i class="bi bi-geo-alt"></i> {{ trek.location }}</p>
      <p class="mb-1">
        <span class="badge" :class="'badge-difficulty-' + trek.difficulty">{{ trek.difficulty }}</span>
        &middot; {{ trek.duration_days }} day(s)
      </p>
      <p class="mb-1 text-muted small">{{ trek.available_slots }} / {{ trek.total_slots }} slots left</p>
      <button
        class="btn btn-sm btn-success mt-2"
        :disabled="trek.available_slots <= 0"
        @click="$emit('book', trek.id)"
      >
        {{ trek.available_slots <= 0 ? 'Full' : 'Book Trek' }}
      </button>
    </div>
  </div>
</template>
