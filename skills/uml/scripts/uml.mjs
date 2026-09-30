import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { resolve } from 'node:path'
import { createInterface } from 'node:readline'
import { fileURLToPath } from 'node:url'

import { parseInvocation } from './args.mjs'
import { createIdleTimer } from './idle.mjs'
import { cachedJarPath, downloadJar, expandHome, hasJava, locateJar } from './jar.mjs'
import { LOCAL_SERVER, chooseLayout, findOnPath } from './layout.mjs'
import { readManifest } from './manifest.mjs'
import { planSources } from './plan.mjs'
import { MISSING_JAR, NO_JAVA, createRenderer } from './render.mjs'
import { createUmlServer, listen } from './server.mjs'

const DEFAULTS = Object.freeze({ 'output-dir': 'docs/uml', jar: '', server: LOCAL_SERVER, 'idle-minutes': '30' })
const HOST = '127.0.0.1'
const USAGE_EXIT = 2
const WORDS_START = '--'

const USAGE = `Usage: uml.mjs <command>
  check [--output-dir D] -- [--diagrams=a,b] [--regenerate] [path or description]
  status [--output-dir D] [--jar J] [--server S]
  download-jar [--jar J]
  serve [--output-dir D] [--jar J] [--server S] [--idle-minutes N]
`

const OPENERS = Object.freeze({
  darwin: (url) => ({ command: 'open', args: [url] }),
  win32: (url) => ({ command: 'cmd', args: ['/c', 'start', '', url] }),
})

export const openerFor = (platform, url) => (OPENERS[platform] ?? ((target) => ({ command: 'xdg-open', args: [target] })))(url)

const parseOptions = (argv) => {
  const options = { ...DEFAULTS }
  for (let index = 0; index < argv.length; index += 1) {
    const [flag, inline] = argv[index].split(/=(.*)/s)
    const name = flag.replace(/^--/, '')
    if (inline !== undefined) {
      options[name] = inline
    } else {
      options[name] = argv[index + 1] ?? ''
      index += 1
    }
  }
  return options
}

const printJson = (deps, value) => deps.stdout(`${JSON.stringify(value, null, 2)}\n`)

const fail = (deps, message, code = 1) => {
  deps.stderr(`${message}\n`)
  return code
}

const probe = (deps, options) => {
  const dot = findOnPath('dot', { pathEnv: deps.env.PATH, exists: deps.exists, platform: deps.platform })
  const jar = locateJar({ configured: options.jar, env: deps.env, homedir: deps.homedir, exists: deps.exists })
  return { dot, jar, java: hasJava({ spawnSync: deps.spawnSync }) }
}

const outputDirOf = (deps, options) => resolve(deps.cwd, expandHome(options['output-dir'], deps.homedir))

const splitAtDashes = (argv) => {
  const at = argv.indexOf(WORDS_START)
  return at === -1 ? { own: [], words: argv } : { own: argv.slice(0, at), words: argv.slice(at + 1) }
}

const check = async (argv, deps) => {
  const { own, words } = splitAtDashes(argv)
  const resolvePath = (path) => resolve(deps.cwd, expandHome(path, deps.homedir))
  const result = parseInvocation(words, { exists: (path) => deps.exists(resolvePath(path)) })
  if (result.error) return fail(deps, result.error)
  const manifest = await readManifest(outputDirOf(deps, parseOptions(own)), { readFile: deps.readFile })
  printJson(deps, { ...result, ...planSources({ invocation: result, manifest, resolvePath }) })
  return 0
}

const status = async (argv, deps) => {
  const options = parseOptions(argv)
  const manifest = await readManifest(outputDirOf(deps, options), { readFile: deps.readFile })
  const { dot, jar, java } = probe(deps, options)
  printJson(deps, {
    manifest: manifest.state,
    manifestError: manifest.error ?? null,
    server: options.server,
    java,
    dot,
    layout: chooseLayout({ dotPath: dot, server: options.server }),
    jar,
    jarCachePath: cachedJarPath({ env: deps.env, homedir: deps.homedir }),
  })
  return 0
}

const downloadJarCommand = async (argv, deps) => {
  const options = parseOptions(argv)
  const dest = options.jar ? expandHome(options.jar, deps.homedir) : cachedJarPath({ env: deps.env, homedir: deps.homedir })
  const result = await downloadJar({ dest, fetch: deps.fetch, mkdir: deps.mkdir, writeFile: deps.writeFile })
  if (result.error) return fail(deps, result.error)
  printJson(deps, result)
  return 0
}

const firstLine = (child) =>
  new Promise((resolveLine) => {
    const lines = createInterface({ input: child.stdout })
    lines.once('line', (line) => resolveLine(line))
    child.once('exit', () => resolveLine(null))
  })

const parseReady = (line) => {
  try {
    return JSON.parse(line)?.url ?? null
  } catch {
    return null
  }
}

const readyToServe = async (deps, options) => {
  const outputDir = outputDirOf(deps, options)
  const manifest = await readManifest(outputDir, { readFile: deps.readFile })
  if (manifest.state !== 'ok') return { error: `uml.json in ${outputDir} is ${manifest.state}${manifest.error ? `: ${manifest.error}` : ''}. Write the sources first.` }
  const { dot, jar, java } = probe(deps, options)
  if (options.server !== LOCAL_SERVER) return { outputDir, manifest: manifest.manifest, dot, jar }
  if (!java) return { error: NO_JAVA }
  if (!jar) return { error: MISSING_JAR }
  return { outputDir, manifest: manifest.manifest, dot, jar }
}

const serve = async (argv, deps) => {
  const options = parseOptions(argv)
  const ready = await readyToServe(deps, options)
  if (ready.error) return fail(deps, ready.error)
  const childArgs = [
    deps.scriptPath,
    'serve-foreground',
    '--output-dir',
    ready.outputDir,
    '--jar',
    ready.jar ?? '',
    '--server',
    options.server,
    '--idle-minutes',
    options['idle-minutes'],
  ]
  const child = deps.spawn(deps.execPath, childArgs, { detached: true, stdio: ['ignore', 'pipe', 'ignore'] })
  const url = parseReady(await firstLine(child))
  child.stdout.destroy()
  child.unref()
  if (!url) return fail(deps, 'The page server stopped before it started. Run serve-foreground with the same flags to see why.')
  const opener = openerFor(deps.platform, url)
  const browser = deps.spawn(opener.command, opener.args, { detached: true, stdio: 'ignore' })
  browser.on('error', () => deps.stdout(`Could not open a browser; open ${url} by hand.\n`))
  browser.unref()
  deps.stdout(`UML page: ${url}\nServer PID: ${child.pid}\nStop it with: kill ${child.pid}\nIt stops by itself after ${options['idle-minutes']} minutes with no request.\n`)
  return 0
}

const serveForeground = async (argv, deps) => {
  const options = parseOptions(argv)
  const ready = await readyToServe(deps, options)
  if (ready.error) return fail(deps, ready.error)
  const render = createRenderer({ server: options.server, jar: ready.jar, dotPath: ready.dot, spawn: deps.spawn, fetch: deps.fetch })
  const smetana = chooseLayout({ dotPath: ready.dot, server: options.server }) === 'smetana'
  let idle = null
  const server = createUmlServer({
    outputDir: ready.outputDir,
    manifest: ready.manifest,
    render,
    readFile: deps.readFile,
    writeFile: deps.writeFile,
    smetana,
    onRequest: () => idle?.touch(),
  })
  const { url } = await listen(server, { host: HOST })
  idle = createIdleTimer({
    minutes: Number(options['idle-minutes']),
    onIdle: () => {
      server.close()
      server.closeAllConnections()
    },
  })
  deps.stdout(`${JSON.stringify({ url })}\n`)
  return 0
}

const COMMANDS = Object.freeze({
  check,
  status,
  'download-jar': downloadJarCommand,
  serve,
  'serve-foreground': serveForeground,
})

export const run = async ([command, ...argv], deps) => {
  const handler = COMMANDS[command]
  if (!handler) return fail(deps, USAGE, USAGE_EXIT)
  return handler(argv, deps)
}

const processDeps = () => ({
  stdout: (text) => process.stdout.write(text),
  stderr: (text) => process.stderr.write(text),
  cwd: process.cwd(),
  env: process.env,
  homedir: homedir(),
  platform: process.platform,
  scriptPath: fileURLToPath(import.meta.url),
  execPath: process.execPath,
  exists: existsSync,
  readFile,
  writeFile,
  mkdir,
  spawn,
  spawnSync,
  fetch: globalThis.fetch,
})

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  run(process.argv.slice(2), processDeps()).then((code) => {
    process.exitCode = code
  })
}
