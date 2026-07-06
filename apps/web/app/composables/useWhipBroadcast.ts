// Broadcast WHIP hacia Cloudflare Stream (basado en el WHIPClient oficial de CF).
// whip_url "mock://" => solo preview local, sin WebRTC (dev sin cuenta CF).

export function useWhipBroadcast() {
  const previewing = ref(false)
  const broadcasting = ref(false)
  const isMock = ref(false)
  const error = ref('')

  let mediaStream: MediaStream | null = null
  let pc: RTCPeerConnection | null = null
  let resourceUrl: string | null = null

  async function startPreview(videoEl: HTMLVideoElement) {
    error.value = ''
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, frameRate: { ideal: 30 } },
        audio: true,
      })
      videoEl.srcObject = mediaStream
      videoEl.muted = true
      await videoEl.play()
      previewing.value = true
    } catch (e: any) {
      error.value = `No se pudo acceder a la cámara: ${e.message ?? e}`
    }
  }

  async function startBroadcast(whipUrl: string) {
    if (!mediaStream) {
      error.value = 'Inicia la cámara primero'
      return
    }
    if (whipUrl.startsWith('mock://')) {
      isMock.value = true
      broadcasting.value = true
      return
    }
    error.value = ''
    try {
      // Sin iceServers propios: Cloudflare maneja ICE (plan, sección 7)
      pc = new RTCPeerConnection({ bundlePolicy: 'max-bundle' })
      for (const track of mediaStream.getTracks()) {
        pc.addTransceiver(track, { direction: 'sendonly' })
      }
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      await waitIceComplete(pc)

      const resp = await fetch(whipUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: pc.localDescription!.sdp,
      })
      if (!resp.ok) throw new Error(`WHIP ${resp.status}`)
      const location = resp.headers.get('Location')
      resourceUrl = location ? new URL(location, whipUrl).toString() : null
      const answer = await resp.text()
      await pc.setRemoteDescription({ type: 'answer', sdp: answer })
      broadcasting.value = true
    } catch (e: any) {
      error.value = `Error al transmitir: ${e.message ?? e}`
      pc?.close()
      pc = null
    }
  }

  async function stopBroadcast() {
    if (resourceUrl) {
      try { await fetch(resourceUrl, { method: 'DELETE' }) } catch {}
      resourceUrl = null
    }
    pc?.close()
    pc = null
    broadcasting.value = false
    isMock.value = false
  }

  function stopPreview() {
    mediaStream?.getTracks().forEach((t) => t.stop())
    mediaStream = null
    previewing.value = false
  }

  onBeforeUnmount(() => {
    stopBroadcast()
    stopPreview()
  })

  return { previewing, broadcasting, isMock, error, startPreview, startBroadcast, stopBroadcast, stopPreview }
}

function waitIceComplete(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === 'complete') return Promise.resolve()
  return new Promise((resolve) => {
    const check = () => {
      if (pc.iceGatheringState === 'complete') {
        pc.removeEventListener('icegatheringstatechange', check)
        resolve()
      }
    }
    pc.addEventListener('icegatheringstatechange', check)
    // WHIP acepta trickle; no bloquear más de 1s juntando candidatos
    setTimeout(() => { pc.removeEventListener('icegatheringstatechange', check); resolve() }, 1000)
  })
}
