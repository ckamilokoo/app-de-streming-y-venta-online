// Modal de inicio de sesión global: cualquier vista puede abrirlo,
// opcionalmente preseleccionando un rol (CTA "Quiero vender" => streamer).

export function useAuthModal() {
  const open = useState('authModal.open', () => false)
  const preferredRole = useState<'buyer' | 'streamer'>('authModal.role', () => 'buyer')

  function show(role?: 'buyer' | 'streamer') {
    if (role) preferredRole.value = role
    open.value = true
  }

  function hide() {
    open.value = false
  }

  return { open, preferredRole, show, hide }
}
