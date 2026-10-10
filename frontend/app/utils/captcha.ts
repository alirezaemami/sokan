/**
 * Solver for Sokan's proof-of-work captcha (sokan/captcha.py, ALTCHA scheme):
 * find the number n for which sha256(salt + n) equals the challenge.
 *
 * SHA-256 is implemented inline rather than with crypto.subtle: awaiting one
 * digest per guess is several times slower, and subtle crypto is missing on
 * plain-http origins. The work runs in a Web Worker so the form stays responsive.
 */

export interface CaptchaChallenge {
  algorithm: string
  challenge: string
  maxnumber: number
  salt: string
  signature: string
}

/** Self-contained (it is stringified into the worker): no outside references. */
export function findNumber(salt: string, challenge: string, max: number): number | null {
  const K = new Uint32Array(64)
  const H0 = new Uint32Array(8)
  // First 32 bits of the fractional parts of the square/cube roots of the first primes.
  for (let c = 2, i = 0; i < 64; c++) {
    let prime = true
    for (let d = 2; d * d <= c; d++) if (c % d === 0) prime = false
    if (!prime) continue
    if (i < 8) H0[i] = (Math.pow(c, 1 / 2) % 1) * 4294967296
    K[i++] = (Math.pow(c, 1 / 3) % 1) * 4294967296
  }
  const target = new Uint32Array(8)
  for (let i = 0; i < 8; i++) target[i] = parseInt(challenge.slice(i * 8, i * 8 + 8), 16)

  const prefix = new TextEncoder().encode(salt)
  const W = new Uint32Array(64)
  const H = new Uint32Array(8)
  const ror = (x: number, n: number) => (x >>> n) | (x << (32 - n))

  for (let n = 0; n <= max; n++) {
    const digits = String(n)
    const len = prefix.length + digits.length
    const msg = new Uint8Array(((len + 8) >> 6) * 64 + 64)
    msg.set(prefix)
    for (let i = 0; i < digits.length; i++) msg[prefix.length + i] = digits.charCodeAt(i)
    msg[len] = 0x80
    const bits = len * 8
    msg[msg.length - 4] = bits >>> 24
    msg[msg.length - 3] = bits >>> 16
    msg[msg.length - 2] = bits >>> 8
    msg[msg.length - 1] = bits

    H.set(H0)
    for (let off = 0; off < msg.length; off += 64) {
      for (let t = 0; t < 16; t++) {
        const j = off + t * 4
        W[t] = (msg[j]! << 24) | (msg[j + 1]! << 16) | (msg[j + 2]! << 8) | msg[j + 3]!
      }
      for (let t = 16; t < 64; t++) {
        const a = W[t - 15]!
        const b = W[t - 2]!
        const s0 = ror(a, 7) ^ ror(a, 18) ^ (a >>> 3)
        const s1 = ror(b, 17) ^ ror(b, 19) ^ (b >>> 10)
        W[t] = (W[t - 16]! + s0 + W[t - 7]! + s1) | 0
      }
      let a = H[0]!, b = H[1]!, c = H[2]!, d = H[3]!, e = H[4]!, f = H[5]!, g = H[6]!, h = H[7]!
      for (let t = 0; t < 64; t++) {
        const t1 = (h + (ror(e, 6) ^ ror(e, 11) ^ ror(e, 25)) + ((e & f) ^ (~e & g)) + K[t]! + W[t]!) | 0
        const t2 = ((ror(a, 2) ^ ror(a, 13) ^ ror(a, 22)) + ((a & b) ^ (a & c) ^ (b & c))) | 0
        h = g
        g = f
        f = e
        e = (d + t1) | 0
        d = c
        c = b
        b = a
        a = (t1 + t2) | 0
      }
      H[0] = H[0]! + a
      H[1] = H[1]! + b
      H[2] = H[2]! + c
      H[3] = H[3]! + d
      H[4] = H[4]! + e
      H[5] = H[5]! + f
      H[6] = H[6]! + g
      H[7] = H[7]! + h
    }
    let hit = true
    for (let i = 0; i < 8; i++) {
      if (H[i] !== target[i]) {
        hit = false
        break
      }
    }
    if (hit) return n
  }
  return null
}

function runInWorker(ch: CaptchaChallenge, signal?: AbortSignal): Promise<number | null> {
  const src = `const findNumber = ${findNumber.toString()};
self.onmessage = (e) => self.postMessage(findNumber(e.data.salt, e.data.challenge, e.data.max));`
  const url = URL.createObjectURL(new Blob([src], { type: 'text/javascript' }))
  const worker = new Worker(url)
  return new Promise((resolve, reject) => {
    const done = () => {
      worker.terminate()
      URL.revokeObjectURL(url)
    }
    signal?.addEventListener('abort', () => {
      done()
      reject(new DOMException('Aborted', 'AbortError'))
    })
    worker.onmessage = (e) => {
      done()
      resolve(e.data as number | null)
    }
    worker.onerror = (e) => {
      done()
      reject(e)
    }
    worker.postMessage({ salt: ch.salt, challenge: ch.challenge, max: ch.maxnumber })
  })
}

/** Solve a challenge and return the payload the server's `verify()` expects. */
export async function solveCaptcha(ch: CaptchaChallenge, signal?: AbortSignal): Promise<string> {
  let number: number | null
  try {
    number = await runInWorker(ch, signal)
  } catch (e) {
    if ((e as DOMException)?.name === 'AbortError') throw e
    // Workers blocked (strict CSP, old browser): solve on the main thread instead.
    number = findNumber(ch.salt, ch.challenge, ch.maxnumber)
  }
  if (number === null) throw new Error('captcha: no solution')
  const { algorithm, challenge, salt, signature } = ch
  return btoa(JSON.stringify({ algorithm, challenge, number, salt, signature }))
}

