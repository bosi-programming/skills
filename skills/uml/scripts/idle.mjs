const MINUTE_MS = 60_000

export const createIdleTimer = ({ minutes, onIdle }) => {
  let handle = null
  const stop = () => clearTimeout(handle)
  const touch = () => {
    stop()
    handle = setTimeout(onIdle, minutes * MINUTE_MS)
    handle.unref?.()
  }
  touch()
  return { touch, stop }
}
