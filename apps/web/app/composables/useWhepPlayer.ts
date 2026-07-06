// Playback WHEP desde Cloudflare Stream. whep_url "mock://" => placeholder (dev sin CF).

export function useWhepPlayer() {
  const playing = ref(false)
  const isMock = ref(false)
  const error = ref('')

  let pc: RTCPeerConnection | null = null

  async function play(whepUrl: string, videoEl: HTMLVideoElement) {
    if (whepUrl.startsWith('mock://')) {
      isMock.value = true
      return
    }
    error.value = ''
    try {
      pc = new RTCPeerConnection({ bundlePolicy: 'max-bundle' })
      pc.addTransceiver('video', { direction: 'recvonly' })
      pc.addTransceiver('audio', { direction: 'recvonly' })
      pc.ontrack = (ev) => {
        if (videoEl.srcObject !== ev.streams[0]) {
          videoEl.srcObject = ev.streams[0] ?? null
        }
      }
      const offer = await pc.createOffer()
      await pc.setLocalDescription(offer)
      await waitIce(pc)

      const resp = await fetch(whepUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/sdp' },
        body: pc.localDescription!.sdp,
      })
      if (!resp.ok) throw new Error(`WHEP ${resp.status}`)
      const answer = await resp.text()
      await pc.setRemoteDescription({ type: 'answer', sdp: answer })
      playing.value = true
    } catch (e: any) {
      error.value = `No se pudo reproducir: ${e.message ?? e}`
      pc?.close()
      pc = null
    }
  }

  function stop() {
    pc?.close()
    pc = null
    playing.value = false
  }

  onBeforeUnmount(stop)

  return { playing, isMock, error, play, stop }
}

function waitIce(pc: RTCPeerConnection): Promise<void> {
  if (pc.iceGatheringState === 'complete') return Promise.resolve()
  return new Promise((resolve) => {
    const check = () => {
      if (pc.iceGatheringState === 'complete') {
        pc.removeEventListener('icegatheringstatechange', check)
        resolve()
      }
    }
    pc.addEventListener('icegatheringstatechange', check)
    setTimeout(() => { pc.removeEventListener('icegatheringstatechange', check); resolve() }, 1000)
  })
}
