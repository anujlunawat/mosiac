import { useAuthStore } from './store/authStore'
import { AuthModal } from './components/AuthModal'
import { Editor } from './components/Editor'
// import type {User} from './types'

/**
 * App — root component.
 *
 * Simple gate: if no JWT token, show the auth modal.
 * Once authenticated, show the collaborative editor.
 *
 * Auth state is persisted in localStorage via Zustand's persist middleware,
 * so users stay logged in across page refreshes.
 */
export default function App() {
  const { token, user } = useAuthStore()

  if (!token || !user) {
    return <AuthModal />
  }
  // const token = "123";
  // const user: User = {
  //   id:"123",
  //   name:"abc",
  //   email:"abc@xyz.com"
  // }
  return <Editor token={token} user={user} />
}
