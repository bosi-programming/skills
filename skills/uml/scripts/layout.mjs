import { posix, win32 } from 'node:path'

export const LOCAL_SERVER = 'local'

const WINDOWS = 'win32'
const WINDOWS_SUFFIXES = ['.exe', '.cmd', '']

export const findOnPath = (command, { pathEnv, exists, platform }) => {
  const paths = platform === WINDOWS ? win32 : posix
  const suffixes = platform === WINDOWS ? WINDOWS_SUFFIXES : ['']
  const folders = (pathEnv ?? '').split(paths.delimiter).filter(Boolean)
  const candidates = folders.flatMap((folder) => suffixes.map((suffix) => paths.join(folder, command + suffix)))
  return candidates.find((candidate) => exists(candidate)) ?? null
}

export const chooseLayout = ({ dotPath, server }) =>
  server !== LOCAL_SERVER || dotPath ? 'graphviz' : 'smetana'
