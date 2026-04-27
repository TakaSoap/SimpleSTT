/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_DEFAULT_LOCALE?: string
  readonly VITE_DEFAULT_THEME?: string
  readonly VITE_DEFAULT_APP_MODE?: 'advanced' | 'basic'
  readonly VITE_BASE_PATH?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

type BluetoothServiceUUID = number | string

interface BluetoothLEScanFilter {
  name?: string
  namePrefix?: string
  services?: BluetoothServiceUUID[]
}

interface BluetoothDevice {
  readonly id: string
  readonly name?: string
}

interface BluetoothRemoteGATTServer {
  readonly connected: boolean
}
