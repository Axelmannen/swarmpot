import { mount } from 'svelte'
import './app.css'
import Payments from './Payments.svelte'

const app = mount(Payments, {
  target: document.getElementById('app')!,
})

export default app
