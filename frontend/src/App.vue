<template>
  <n-config-provider :theme="naiveTheme" :locale="naiveLocale" :date-locale="naiveDateLocale">
    <n-loading-bar-provider>
      <n-message-provider>
        <n-layout class="app-layout" :style="layoutStyle">
          <n-layout-header bordered :style="headerStyle">
            <n-space justify="space-between" align="center" wrap class="header-bar">
              <div class="header-meta">
                <n-gradient-text size="26" class="brand">{{ t('common.appName') }}</n-gradient-text>
                <span class="tagline">{{ t('common.tagline') }}</span>
              </div>
              <n-space align="center" size="large" wrap class="header-controls">
                <n-space align="center" size="small" class="mode-switch">
                  <n-switch v-model:value="modeSelection" :checked-value="'advanced'"
                    :unchecked-value="'basic'">
                    <template #checked>
                      {{ t('common.mode.advanced') }}
                    </template>
                    <template #unchecked>
                      {{ t('common.mode.basic') }}
                    </template>
                  </n-switch>
                </n-space>
                <n-space align="center" size="small">
                  <n-select class="control" size="small" :value="locale" :options="languageOptions"
                    :placeholder="t('common.language')" @update:value="handleLocaleChange" />
                </n-space>
                <n-button-group size="small" class="theme-toggle">
                  <n-button quaternary :type="themeMode === 'system' ? 'primary' : 'default'"
                    @click="() => setMode('system')">
                    <template #icon>
                      <n-icon size="16" :component="ContrastOutline" />
                    </template>
                    <span>{{ t('common.theme.system') }}</span>
                  </n-button>
                  <n-button quaternary :type="themeMode === 'light' ? 'primary' : 'default'"
                    @click="() => setMode('light')">
                    <template #icon>
                      <n-icon size="16" :component="SunnyOutline" />
                    </template>
                    <span>{{ t('common.theme.light') }}</span>
                  </n-button>
                  <n-button quaternary :type="themeMode === 'dark' ? 'primary' : 'default'"
                    @click="() => setMode('dark')">
                    <template #icon>
                      <n-icon size="16" :component="MoonOutline" />
                    </template>
                    <span>{{ t('common.theme.dark') }}</span>
                  </n-button>
                </n-button-group>
              </n-space>
            </n-space>
          </n-layout-header>
          <n-layout-content class="app-content">
            <RouterView />
          </n-layout-content>
        </n-layout>
      </n-message-provider>
    </n-loading-bar-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { darkTheme, dateEnUS, dateZhCN, dateZhTW, enUS, zhCN, zhTW } from 'naive-ui'
import { ContrastOutline, SunnyOutline, MoonOutline } from '@vicons/ionicons5'
import { SUPPORTED_LOCALES, i18n, persistLocale } from './i18n'
import { useTheme } from './composables/useTheme'
import { provideAppMode, AppMode } from './composables/useAppMode'

const { locale, t } = useI18n()
const { mode: themeMode, isDark, setMode } = useTheme()
const appModeContext = provideAppMode('advanced')
const modeSelection = computed<AppMode>({
  get: () => appModeContext.mode.value,
  set: (value) => appModeContext.setMode(value)
})

const naiveTheme = computed(() => (isDark.value ? darkTheme : undefined))

const naiveLocale = computed(() => {
  switch (locale.value) {
    case 'zh-CN':
      return zhCN
    case 'zh-HK':
      return zhTW
    default:
      return enUS
  }
})

const naiveDateLocale = computed(() => {
  switch (locale.value) {
    case 'zh-CN':
      return dateZhCN
    case 'zh-HK':
      return dateZhTW
    default:
      return dateEnUS
  }
})

const languageOptions = SUPPORTED_LOCALES.map((item) => ({
  label: item.label,
  value: item.value
}))

const layoutStyle = computed(() => ({
  minHeight: '100vh',
  backgroundColor: isDark.value ? '#0b1220' : '#f5f7fb',
  color: isDark.value ? '#e2e8f0' : '#1f2937',
  transition: 'background-color 0.3s ease, color 0.3s ease'
}))

const headerStyle = computed(() => ({
  padding: '20px 32px',
  borderBottom: 'none',
  backgroundColor: isDark.value ? '#050505' : '#ffffff',
  boxShadow: isDark.value
    ? '0 14px 24px -20px rgba(15, 23, 42, 0.75)'
    : '0 12px 24px -18px rgba(100, 116, 139, 0.25)'
}))

type AppLocale = typeof SUPPORTED_LOCALES[number]['value']

function handleLocaleChange(value: AppLocale) {
  locale.value = value
  i18n.global.locale.value = value
  persistLocale(value)
}

</script>

<style scoped>
.header-bar {
  width: 100%;
}

.header-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.brand {
  font-weight: 700;
}

.tagline {
  margin: 0;
  font-size: 13px;
  color: rgba(71, 85, 105, 0.85);
}

.app-content {
  padding: 28px 32px 48px;
}

.control {
  width: 150px;
}

.theme-toggle {
  background-color: transparent;
}

.mode-switch {
  font-size: 12px;
  color: rgba(71, 85, 105, 0.85);
}

:global(body.theme-dark) .mode-switch {
  color: rgba(203, 213, 225, 0.85);
}

:global(body.theme-dark) .theme-toggle .n-button--quaternary {
  color: rgba(226, 232, 240, 0.85);
}

.header-controls .n-icon {
  color: rgba(148, 163, 184, 0.9);
}

:global(body.theme-dark) .header-controls .n-icon {
  color: rgba(203, 213, 225, 0.85);
}

:global(.theme-toggle .n-button--primary) {
  font-weight: 600;
}

:global(.theme-toggle .n-button) {
  min-width: 72px;
}

:global(body.theme-dark) .tagline {
  color: rgba(203, 213, 225, 0.8);
}

:global(body.theme-dark) .theme-toggle {
  background-color: rgba(15, 23, 42, 0.35);
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.2);
}

@media (max-width: 640px) {
  .control {
    width: 100%;
  }
}
</style>
