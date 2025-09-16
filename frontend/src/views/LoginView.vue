<template>
  <div class="login-wrapper">
    <n-card :title="t('login.title')" class="login-card" size="huge">
      <n-form :model="form" :rules="rules" ref="formRef">
        <n-form-item :label="t('login.username')" path="username">
          <n-input v-model:value="form.username" :placeholder="t('login.placeholders.username')" />
        </n-form-item>
        <n-form-item :label="t('login.password')" path="password">
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="mousedown"
            :placeholder="t('login.placeholders.password')"
          />
        </n-form-item>
        <div class="actions">
          <n-space>
            <n-button type="primary" size="large" :loading="loading" @click="handleSubmit">
              {{ t('login.login') }}
            </n-button>
            <n-button size="large" tertiary @click="auth.clearCredentials">
              {{ t('logout.clear') }}
            </n-button>
          </n-space>
        </div>
      </n-form>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { FormInst, FormRules } from 'naive-ui'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { login } from '../api/endpoints'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const message = useMessage()
const auth = useAuth()
const { t } = useI18n()

const loading = ref(false)
const formRef = ref<FormInst | null>(null)

const form = reactive({
  username: auth.username.value || '',
  password: ''
})

const rules: FormRules = {
  username: [{ required: true, message: () => t('validation.required'), trigger: 'blur' }],
  password: [{ required: true, message: () => t('validation.required'), trigger: 'blur' }]
}

function handleSubmit() {
  formRef.value?.validate(async (errors) => {
    if (errors) return
    loading.value = true
    try {
      auth.setCredentials(form.username, form.password)
      await login()
      message.success(t('login.success'))
      router.push({ name: 'transcribe' })
    } catch (error: unknown) {
      const text = error instanceof Error ? error.message : t('login.failure')
      auth.clearCredentials()
      message.error(text)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-wrapper {
  display: grid;
  place-items: center;
  height: 100vh;
  padding: 24px;
  background: radial-gradient(circle at 20% 20%, #f0f5ff, transparent 60%),
    radial-gradient(circle at 80% 0%, #f9f5ff, transparent 55%),
    linear-gradient(135deg, #f7f9fc 0%, #eef3fb 100%);
}

.login-card {
  width: min(420px, 100%);
  box-shadow: 0 20px 40px -24px rgba(15, 23, 42, 0.25);
  border-radius: 16px;
}

.actions {
  margin-top: 16px;
}
</style>
