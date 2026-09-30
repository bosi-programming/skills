import { dirname, join } from 'node:path'

export const JAR_RELEASE_URL = 'https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar'

const CACHE_PARTS = ['bosi-skills', 'uml', 'plantuml.jar']
const SET_JAR = 'set uml.plantumlJar to its path'

export const expandHome = (path, homedir) => (path === '~' || path.startsWith('~/') ? join(homedir, path.slice(1)) : path)

export const cachedJarPath = ({ env, homedir }) =>
  join(env.XDG_CACHE_HOME || join(homedir, '.cache'), ...CACHE_PARTS)

export const locateJar = ({ configured, env, homedir, exists }) => {
  const candidate = configured ? expandHome(configured, homedir) : cachedJarPath({ env, homedir })
  return exists(candidate) ? candidate : null
}

export const hasJava = ({ spawnSync }) => {
  const result = spawnSync('java', ['-version'], { stdio: 'ignore' })
  return !result.error && result.status === 0
}

export const downloadJar = async ({ url = JAR_RELEASE_URL, dest, fetch, mkdir, writeFile }) => {
  let response
  try {
    response = await fetch(url, { redirect: 'follow' })
  } catch (error) {
    return { error: `Could not reach ${url} (${error.message}). Check the network, or download the jar by hand and ${SET_JAR}.` }
  }
  if (!response.ok) {
    return { error: `Could not download the PlantUML jar from ${url} (HTTP ${response.status}). Download it by hand and ${SET_JAR}.` }
  }
  const bytes = new Uint8Array(await response.arrayBuffer())
  await mkdir(dirname(dest), { recursive: true })
  await writeFile(dest, bytes)
  return { path: dest }
}
