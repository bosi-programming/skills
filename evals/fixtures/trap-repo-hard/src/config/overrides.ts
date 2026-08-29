import { defaults } from './defaults';

const envOverrides: Partial<typeof defaults> = {
  retryLimit: 3,
};

const runtimePatch: Partial<typeof defaults> = {
  retryLimit: 0,
};

export function resolveConfig() {
  return { ...defaults, ...envOverrides, ...runtimePatch };
}
