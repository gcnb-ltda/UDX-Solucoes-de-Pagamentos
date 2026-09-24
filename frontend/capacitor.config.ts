import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'br.com.udxbanco.payments',
  appName: 'UDX Pay Test',
  webDir: 'out',
  server: {
    androidScheme: 'https',
  },
};

export default config;
